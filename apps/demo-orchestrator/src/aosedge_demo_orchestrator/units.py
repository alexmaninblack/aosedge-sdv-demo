# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit current-run Unit lifecycle, shared by CLI and local API."""

import json
import os
import subprocess
import time
from uuid import uuid4
from pathlib import Path

from .environment import EnvironmentError, JOURNAL, OVERLAYS, digest
from .guest_access import read_guest, ssh_command
from .status import load_configuration, read_json, now
from .vm import access_path, qmp
from .probes import provisioning_forward_states


class UnitService:
    def __init__(self, vm):
        self.vm = vm
        self.environment = vm.environment
        self.root = vm.root
        self.progress = vm.progress
        from .cloud_observation import SharedCloudObserver
        self.cloud_observer = SharedCloudObserver()

    def observe(self, action, target):
        """Journal selects identity only; every displayed fact comes from Cloud."""
        from .cloud_observation import unavailable
        from .status import object_id, safe_word
        if target != "test" or action not in ("cloud-status", "monitoring"):
            raise EnvironmentError("UNIT_OBSERVATION_REQUIRES_TEST")
        state = read_json(self.root / JOURNAL)
        item = state.get("vehicles", {}).get("test", {})
        if not item.get("unitId") or not item.get("systemUid"):
            raise EnvironmentError("TEST_CLOUD_BINDING_REQUIRED")
        identity = dict(unitId=object_id(item["unitId"]), systemUid=safe_word(item["systemUid"], 256))
        owner = state.get("cloudBinding", {}).get("ownerId")
        if not owner:
            raise EnvironmentError("CLOUD_OBSERVATION_OWNER_REQUIRED")
        owner = object_id(owner)
        def fetch():
            try:
                return self._cloud("observe", observation=action, ownerId=owner, **identity)
            except EnvironmentError as error:
                return unavailable(identity, action, str(error))
        return self.cloud_observer.read((owner, identity["unitId"], identity["systemUid"], action), fetch)

    def _cloud(self, action, **values):
        config = load_configuration(self.root)
        profile = config["cloudProfiles"].get("oem-delivery")
        if not profile or profile["expectedRole"] != "oem":
            raise EnvironmentError("OEM_DELIVERY_PROFILE_REQUIRED")
        path = profile["credential"]
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
            raise EnvironmentError("OEM_CREDENTIAL_MISSING_OR_UNSAFE")
        request = dict(values, action=action, credential=str(path))
        if getattr(self, "owner_id", None):
            request.setdefault("ownerId", self.owner_id)
        if profile.get("expectedOwnerId"):
            request.setdefault("ownerId", profile["expectedOwnerId"])
        if action in ("provision", "assign", "remove", "deprovision", "delete"):
            # Submission/attempt, not a claim that Cloud applied the operation.
            self.mutations_started = True
        try:
            result = subprocess.run([str(config["cloudPython"]), "-I", "-B",
                str(Path(__file__).with_name("unit_cloud.py"))], input=json.dumps(request),
                capture_output=True, text=True, timeout=195 if action == "provision" else 120 if action == "wait" else 60 if action == "observe" else 45,
                env={"PATH": os.defpath})
            if result.returncode or len(result.stdout) > 262144:
                raise EnvironmentError("UNIT_WORKER_UNAVAILABLE")
            payload = json.loads(result.stdout)
        except EnvironmentError:
            raise
        except (subprocess.TimeoutExpired, OSError, ValueError):
            raise EnvironmentError("UNIT_WORKER_RESPONSE_UNAVAILABLE") from None
        if not payload.get("ok"):
            raise EnvironmentError(payload.get("reason", "UNIT_CLOUD_FAILED"))
        return payload["data"]

    def _bindings(self, state, inventory):
        bindings = state.get("cloudBinding")
        if bindings and bindings["ownerId"] != inventory["ownerId"]:
            raise EnvironmentError("OEM_OWNER_CHANGED")
        selected = {}
        for role, title in (("test", "Test Vehicles"), ("production", "Production Vehicles")):
            candidates = [item for item in inventory["sets"] if
                          (item["id"] == bindings["sets"][role] if bindings else
                           item["title"] == title or item["title"].endswith(" / " + title))]
            if len(candidates) != 1:
                raise EnvironmentError("ROLE_UNIT_SET_MISSING_OR_AMBIGUOUS:" + role)
            item = candidates[0]
            if item["is_validation_set"] is not (role == "test"):
                raise EnvironmentError("ROLE_UNIT_SET_TYPE_MISMATCH:" + role)
            selected[role] = item
        if selected["test"]["id"] == selected["production"]["id"] or selected["test"]["fleet"] != selected["production"]["fleet"]:
            raise EnvironmentError("ROLE_UNIT_SET_FLEET_OR_ID_CONFLICT")
        return selected

    def confirm_test_retired(self, state):
        """Fresh Test-only absence proof, preserving the full peer journal."""
        return self.confirm_retired(state, roles=("test",))

    def confirm_retired(self, state, roles=None):
        """Read-only cleanup gate; caller already owns the current-run writer."""
        binding = state.get("cloudBinding")
        if not binding or not binding.get("ownerId"):
            raise EnvironmentError("CLOUD_RETIREMENT_OWNER_REQUIRED")
        self.owner_id = binding["ownerId"]
        scoped = roles is not None
        roles = tuple(state["vehicles"]) if roles is None else tuple(roles)
        if (scoped and not roles) or any(role not in state["vehicles"] for role in roles):
            raise EnvironmentError("CLOUD_RETIREMENT_TARGET_INVALID")
        for role in roles:
            item = state["vehicles"][role]
            if not item.get("cloud"):
                continue
            if item["cloud"].get("lifecycle") != "DELETED":
                raise EnvironmentError("CLOUD_RETIREMENT_PROOF_REQUIRED")
            self.progress(role + ": confirming retired Unit/Node absence before local cleanup")
            result = self._cloud("absence", unitId=item["unitId"], nodeId=item["nodeId"])
            sets = self._bindings(state, result["inventory"])
            if (not result["absent"] or any(sets[target]["members"] for target in (roles if scoped else sets))
                    or any(unit["system_uid"] == item["systemUid"] for unit in result["inventory"]["units"])):
                raise EnvironmentError("FRESH_CLOUD_RETIREMENT_CHECK_FAILED")
        uploads = []
        for version, record in state.get("componentOperations", {}).items():
            attempt = record.get("upload", {})
            if not attempt.get("attemptStarted") or attempt.get("state") == "CONFIRMED":
                continue
            response = attempt.get("response") or {}
            approval = record.get("approve") or {}
            if (attempt.get("state") != "RESPONDED" or response.get("httpStatus") != 201
                    or not record.get("deploymentId") or record["deploymentId"] != response.get("deploymentId")):
                raise EnvironmentError("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
            if record.get("publicationPath") == "VERIFICATION_TEST":
                if record.get("ownerId") != self.owner_id:
                    raise EnvironmentError("COMPONENT_PUBLICATION_OWNER_CHANGED")
                uploads.append(dict(version=version, deploymentId=record["deploymentId"], verificationTest=True))
            else:
                if (approval.get("state") != "CONFIRMED" or not record.get("batchId")
                        or record["batchId"] != (approval.get("response") or {}).get("batchId")):
                    raise EnvironmentError("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
                uploads.append(dict(version=version, deploymentId=record["deploymentId"], batchId=record["batchId"]))
        if uploads:
            self.progress("Confirming recorded component uploads in Cloud; no upload or approval")
            result = self._cloud("reconcile-uploads", uploads=uploads)
            if result.get("confirmedUploads") != uploads:
                raise EnvironmentError("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
            for entry in uploads:
                state["componentOperations"][entry["version"]]["upload"].update(
                    state="CONFIRMED", confirmedAt=now(), reconciliationScope="PUBLICATION_ONLY")
            # This proves the publication outcome, not the old Production
            # snapshot (those Units have legitimately been deleted already).
            self.vm._save(state)
        return True

    def execute(self, action, target):
        if action not in ("provision", "deprovision", "delete", "unassign") or target not in ("test", "production", "all"):
            raise EnvironmentError("UNIT_ACTION_INVALID")
        if action == "unassign" and target != "test":
            raise EnvironmentError("UNIT_UNASSIGN_TEST_ONLY")
        with self.environment._writer():
            self.mutations_started = False
            state = read_json(self.root / JOURNAL)
            roles = [role for role in OVERLAYS if role in state["vehicles"]] if target == "all" else [target]
            # Provision preserves the running guest and its initial source.
            # Stop validation intentionally rejects attached sources for
            # deprovision/delete and must not run before this narrow exception.
            self.vm._validate(state, "start" if action == "provision" else "stop", roles)
            selected_role = state.get("currentVehicle")
            initial_connection = (state.get("source", {}).get("lastConnectionConfirmation") or {})
            connected_initial_test = (action == "provision" and selected_role == "test" and "test" in roles
                and initial_connection.get("role") == "test" and initial_connection.get("serverTls") is True
                and initial_connection.get("initialManual") is True
                and not state.get("source", {}).get("operation") and not state.get("source", {}).get("stopOperation"))
            if selected_role is not None and not connected_initial_test:
                raise EnvironmentError("UNIT_LIFECYCLE_REQUIRES_DETACHED_SOURCE")
            self.progress("Reading OEM authority and the two role Unit Sets")
            inventory = self._cloud("inventory", setIds=state.get("cloudBinding", {}).get("sets"), includeUnits=False)
            self.owner_id = inventory["ownerId"]
            selected = self._bindings(state, inventory)
            state["cloudBinding"] = {"ownerId": inventory["ownerId"], "fleetId": selected["test"]["fleet"],
                                      "sets": {role: value["id"] for role, value in selected.items()}}
            # A lost mutation response may be reconciled by an explicit command,
            # but may never trigger another SDK attempt or destructive request.
            if len(state["operations"]) != 1:
                self._reconcile(state)
            self.vm._save(state)
            results = {}
            for role in roles:
                started = time.monotonic()
                item = state["vehicles"][role]
                expected = {item["unitId"]} if item.get("unitId") else set()
                foreign = [member for member in selected[role]["members"] if member["id"] not in expected]
                result = {"state": "BLOCKED", "unitSetId": selected[role]["id"],
                          "unitSetTitle": selected[role]["title"]}
                if foreign:
                    result.update(reason="ROLE_UNIT_SET_HAS_OTHER_UNITS", conflictingUnits=foreign)
                else:
                    try:
                        detail = getattr(self, "_" + action)(state, role, selected)
                        if action == "provision" and state.get("backends"):
                            from .backend_context import sync_context
                            sync_context(self.environment, state)
                        result.update(detail, state="COMPLETED")
                    except (EnvironmentError, OSError, subprocess.SubprocessError) as error:
                        result["reason"] = str(error) if isinstance(error, EnvironmentError) else "UNIT_OPERATION_UNAVAILABLE"
                        self.progress(role + ": blocked at " + result["reason"])
                        if len(state["operations"]) > 1:
                            state["operations"][-1]["state"] = "UNCERTAIN"
                        self.vm._save(state)
                result["durationSeconds"] = round(time.monotonic() - started, 2)
                results[role] = result
                if len(state["operations"]) > 1:
                    for other in roles:
                        if other not in results:
                            results[other] = {"state": "BLOCKED", "reason": "PEER_OPERATION_RECONCILIATION_REQUIRED"}
                    break
            return {"vehicles": results, "cloudMutationsStarted": self.mutations_started}

    def _intent(self, state, role, step):
        if len(state["operations"]) != 1:
            raise EnvironmentError("PRIOR_OPERATION_REQUIRES_RECONCILIATION")
        item = state["vehicles"][role]
        item.setdefault("cloud", {})["step"] = step
        state["operations"].append({"id": str(uuid4()), "class": "UNIT_LIFECYCLE", "step": step,
            "team": "DEMO_SOLUTION", "authority": "OEM_DELIVERY", "target": [role],
            "knownExternalIds": {k: item.get(k) for k in ("unitId", "nodeId", "systemUid", "unitSetId")},
            "requestFingerprint": step + ":" + item["localVmId"], "resourceKeys": ["CURRENT_RUN"],
            "state": "SUBMITTING", "reconciliation": "UNOBSERVABLE", "lastRead": None})
        self.vm._save(state)

    def _done(self, state, role):
        state["vehicles"][role]["cloud"]["lastConfirmedAt"] = now()
        state["operations"] = state["operations"][:1]
        self.vm._save(state)

    def _reconcile(self, state):
        if len(state["operations"]) != 2 or state["operations"][-1].get("class") != "UNIT_LIFECYCLE":
            raise EnvironmentError("PRIOR_OPERATION_REQUIRES_RECONCILIATION")
        op = state["operations"][-1]
        role = op["target"][0]
        item = state["vehicles"][role]
        value = self._cloud("find", systemUid=item["systemUid"])["unit"] if item.get("systemUid") else None
        step = op["step"]
        applied = (step == "SDK_PROVISION" and value and value["status"] == "provisioned" and self._guest_provisioned(state, role))
        applied = applied or (step == "ASSIGN_SET" and value and item["unitSetId"] in value["unit_sets"])
        applied = applied or (step == "REMOVE_SET" and value and item["unitSetId"] not in value["unit_sets"])
        applied = applied or (step == "DEPROVISION" and value and value["status"] == "new" and value["online_status"] == "Offline")
        if step == "DELETE_UNIT" and item.get("unitId"):
            applied = self._cloud("absence", unitId=item["unitId"], nodeId=item["nodeId"])["absent"]
        if not applied:
            raise EnvironmentError("UNIT_PREVIOUS_ATTEMPT_UNPROVEN_NO_RETRY:" + step)
        if value:
            self._bind_unit(state, role, value)
        if step == "DELETE_UNIT":
            item["cloud"].update(lifecycle="DELETED", absenceConfirmed=True)
        self._done(state, role)

    def _live(self, state, role):
        item = state["vehicles"][role]
        if self.vm._owned_pid(self.vm._command(state, role), str(self.root / item["overlay"])) is None:
            raise EnvironmentError("VM_START_REQUIRED")

    def _forward(self, state, role, enable):
        self._live(state, role)
        port = 18089 if role == "test" else 18090
        command = ("hostfwd_add aosnet tcp:127.0.0.1:" + str(port) + "-10.0.0.100:8089" if enable else
                   "hostfwd_remove aosnet tcp:127.0.0.1:" + str(port))
        if enable:
            self.vm._free_port(port)
        output = qmp(self.vm._paths(role)[0], "human-monitor-command", arguments={"command-line": command})
        if enable and output:
            raise EnvironmentError("PROVISIONING_FORWARD_CHANGE_FAILED")
        forwards = qmp(self.vm._paths(role)[0], "human-monitor-command", arguments={"command-line": "info usernet"})
        states = provisioning_forward_states(forwards, port)
        # libslirp lists accepted/draining connections using the same endpoint.
        # Only HOST_FORWARD denotes the listening forwarding rule.
        present = "HOST_FORWARD" in states
        if "UNCLASSIFIED" in states:
            raise EnvironmentError("PROVISIONING_FORWARD_STATE_UNRECOGNIZED")
        if present != enable:
            raise EnvironmentError("PROVISIONING_FORWARD_POSTCONDITION_FAILED")
        if not enable:
            self.progress(role + ": provisioning listener removed; remaining TCP states=" + ",".join(states))
        return "127.0.0.1:" + str(port)

    def _guest_script(self, state, role, script, timeout=8):
        item = state["vehicles"][role]
        result = subprocess.run(ssh_command(access_path(self.root, role), item["sshPort"], timeout),
            input=script, capture_output=True, text=True, timeout=timeout)
        if result.returncode or len(result.stdout) > 65536:
            raise EnvironmentError("UNIT_GUEST_OBSERVATION_FAILED")
        return result.stdout

    def _guest_provisioned(self, state, role):
        return self._guest_script(state, role,
            "test -f /var/aos/.provisionstate || exit 1\n"
            "for s in aos-iam.service aos-cm.service aos-sm.service; do systemctl is-active --quiet \"$s\" || exit 1; done\n"
            "if test -f /usr/share/aos-vehicle-platform/demo-runtime-inputs-v1; then\n"
            "test \"$(cat /var/aos/workdirs/sm/runtimes/systemd-slot-component/demo-inputs/role)\" = " + role + " || exit 1\nfi\n"
            "printf 'PROVISIONED\\n'\n") == "PROVISIONED\n"

    def _bind_unit(self, state, role, unit):
        item = state["vehicles"][role]
        if unit["system_uid"] != item["systemUid"] or (unit["status"] == "provisioned"
                and "nodes" in unit and len(unit["nodes"]) != 1):
            raise EnvironmentError("UNIT_NODE_IDENTITY_MISMATCH")
        if item.get("unitId") not in (None, unit["id"]):
            raise EnvironmentError("UNIT_UUID_CHANGED")
        if unit["fleet"] != state["cloudBinding"]["fleetId"]:
            raise EnvironmentError("UNIT_FLEET_MISMATCH")
        item["unitId"] = unit["id"]
        if unit.get("nodes"):
            if item.get("nodeId") not in (None, unit["nodes"][0]["id"]):
                raise EnvironmentError("UNIT_NODE_UUID_CHANGED")
            item["nodeId"] = unit["nodes"][0]["id"]
        self.vm._save(state)

    def _wait(self, state, role, predicate, label, timeout=90):
        item = state["vehicles"][role]
        self.progress(role + ": waiting for " + label)
        value = self._cloud("wait", unitId=item.get("unitId"), systemUid=item["systemUid"],
            unitSetId=item.get("unitSetId"), needNodes=not bool(item.get("nodeId")),
            label=label, timeout=timeout)["unit"]
        self._bind_unit(state, role, value)
        if not predicate(value):
            raise EnvironmentError("UNIT_WAIT_POSTCONDITION_FAILED:" + label)
        return value

    def _provision(self, state, role, selected):
        item = state["vehicles"][role]
        if item.get("cloud", {}).get("lifecycle") in ("DEPROVISIONED", "DELETED"):
            raise EnvironmentError("RETIRED_VM_REQUIRES_FRESH_FACTORY_OVERLAY")
        self._live(state, role)
        if not item.get("systemUid"):
            guest = read_guest(access_path(self.root, role), item["sshPort"], 8)
            if not guest["unprovisioned"] or not guest["guestDnsReady"]:
                raise EnvironmentError("UNPROVISIONED_GUEST_AND_DNS_REQUIRED")
            address = self._forward(state, role, True)
            try:
                identity = self._cloud("identity", address=address)
                if any(other.get("systemUid") == identity["systemUid"] for name, other in state["vehicles"].items() if name != role):
                    raise EnvironmentError("DUPLICATE_GUEST_IDENTITY")
                # The SDK adapter performs the exact duplicate-identity query
                # immediately before registration; do not do the same read twice.
                item.update(systemUid=identity["systemUid"], unitSetId=selected[role]["id"],
                            cloud={"lifecycle": "PROVISIONING", "identity": identity})
                self._intent(state, role, "SDK_PROVISION")
                self.progress(role + ": official SDK provisioning, one Main Node, one attempt")
                self._cloud("provision", address=address, identity=identity, ownerId=state["cloudBinding"]["ownerId"])
                self._done(state, role)
            finally:
                self._forward(state, role, False)
        unit = self._wait(state, role, lambda value: value and value["status"] == "provisioned" and value["online_status"] == "Online", "CLOUD_ONLINE")
        if not self._guest_provisioned(state, role):
            raise EnvironmentError("PROVISIONED_GUEST_CORE_NOT_READY")
        if item["unitSetId"] not in unit["unit_sets"]:
            self._intent(state, role, "ASSIGN_SET")
            self._cloud("assign", unitId=item["unitId"], systemUid=item["systemUid"], unitSetId=item["unitSetId"])
            unit = self._wait(state, role, lambda value: value and item["unitSetId"] in value["unit_sets"], "ROLE_UNIT_SET")
            self._done(state, role)
        if selected["production" if role == "test" else "test"]["id"] in unit["unit_sets"]:
            raise EnvironmentError("CROSSED_ROLE_MEMBERSHIP")
        item["cloud"]["lifecycle"] = "ONLINE"
        self.vm._save(state)
        self.progress(role + ": Cloud Online; role Unit Set confirmed")
        return {"unitId": item["unitId"], "nodeId": item["nodeId"], "systemUid": item["systemUid"],
                "onlineStatus": "Online", "lifecycle": "PROVISIONED"}

    def _deprovision(self, state, role, selected):
        item = state["vehicles"][role]
        if not item.get("unitId") and item.get("systemUid"):
            value = self._cloud("find", systemUid=item["systemUid"])["unit"]
            if value:
                self._bind_unit(state, role, value)
            else:
                raise EnvironmentError("PARTIAL_PROVISIONING_REQUIRES_RECONCILIATION")
        if not item.get("unitId"):
            return {"lifecycle": "NEVER_PROVISIONED", "alreadyAbsent": True}
        if item["cloud"]["lifecycle"] in ("DEPROVISIONED", "DELETED"):
            value = self._cloud("find", systemUid=item["systemUid"])["unit"]
            if value and (value["status"] != "new" or value["online_status"] != "Offline"):
                raise EnvironmentError("RETIRED_UNIT_STATE_CONTRADICTORY")
            return {"lifecycle": item["cloud"]["lifecycle"], "alreadyDeprovisioned": True}
        self._live(state, role)
        # Keep SSH/DNS and the peer VM available. CM is the Unit's sole
        # Cloud communication owner; stopping it closes the external session.
        item["cloud"].update(lifecycle="DEPROVISIONING", cmDisconnectIntent=True)
        self.vm._save(state)
        self.progress(role + ": disconnecting CM; waiting for Cloud Offline")
        self._stop_cm(state, role)
        value = self._wait(state, role, lambda unit: unit and unit["online_status"] == "Offline", "CLOUD_OFFLINE")
        if value["status"] == "provisioned":
            self._intent(state, role, "DEPROVISION")
            self._cloud("deprovision", unitId=item["unitId"], systemUid=item["systemUid"])
            self._wait(state, role, lambda unit: unit and unit["status"] == "new" and unit["online_status"] == "Offline", "CLOUD_DEPROVISIONED")
            self._done(state, role)
        elif value["status"] != "new":
            raise EnvironmentError("UNEXPECTED_CLOUD_DEPROVISION_STATE")
        self.progress(role + ": Cloud new/Offline confirmed; stopping VM")
        # Cloud owns identity revocation. Do not restart CM with retired
        # credentials; stop this exact VM after authoritative deprovisioning.
        result = self.vm._stop(state, role, 90)
        if result["state"] != "COMPLETED":
            raise EnvironmentError("RETIRED_VM_STOP_NOT_CONFIRMED")
        self.vm._stop_dns(state)
        item["cloud"].update(lifecycle="DEPROVISIONED", cloudStatus="new", onlineStatus="Offline")
        state["stage"] = "LOCAL_ACTIVE" if any(v["runtime"]["state"] == "RUNNING" for v in state["vehicles"].values()) else "LOCAL_STOPPED"
        self.vm._save(state)
        return {"unitId": item["unitId"], "lifecycle": "DEPROVISIONED", "cloudStatus": "new",
                "onlineStatus": "Offline", "vmState": "STOPPED"}

    def _stop_cm(self, state, role):
        self._guest_script(state, role, "systemctl stop --no-block aos-cm.service\n")
        deadline = time.monotonic() + 100
        report = 0
        while time.monotonic() < deadline:
            value = self._guest_script(state, role, "systemctl show aos-cm.service -p ActiveState --value\n").strip()
            if value == "inactive":
                return
            if time.monotonic() - report >= 10:
                self.progress(role + ": CM shutdown in progress (stock systemd stop limit: 90 s)")
                report = time.monotonic()
            time.sleep(2)
        raise EnvironmentError("CM_STOP_TIMEOUT_NO_FORCE_USED")

    def _unassign(self, state, role, selected):
        item = state["vehicles"][role]
        if role != "test" or item.get("runtime", {}).get("state") != "STOPPED":
            raise EnvironmentError("UNIT_UNASSIGN_REQUIRES_STOPPED_TEST")
        if not item.get("unitId") or item.get("unitSetId") != selected[role]["id"]:
            raise EnvironmentError("UNIT_UNASSIGN_BINDING_REQUIRED")
        value = self._cloud("read", unitId=item["unitId"])["unit"]
        if (not value or value["system_uid"] != item["systemUid"] or value["status"] != "provisioned"
                or selected["production"]["id"] in value["unit_sets"]):
            raise EnvironmentError("UNIT_UNASSIGN_IDENTITY_OR_STATE_CHANGED")
        expected_sets = set(value["unit_sets"]) - {item["unitSetId"]}
        no_op = item["unitSetId"] not in value["unit_sets"]
        if not no_op:
            self._intent(state, role, "REMOVE_SET")
            self._cloud("remove", unitId=item["unitId"], systemUid=item["systemUid"], unitSetId=item["unitSetId"])
            value = self._wait(state, role, lambda unit: unit and item["unitSetId"] not in unit["unit_sets"], "MEMBERSHIP_REMOVED")
        if value["status"] != "provisioned" or set(value["unit_sets"]) != expected_sets:
            raise EnvironmentError("UNIT_UNASSIGN_POSTCONDITION_FAILED")
        item["cloud"]["roleAssignment"] = "UNASSIGNED"
        self._done(state, role)
        return dict(unitId=item["unitId"], lifecycle="PROVISIONED", roleAssignment="UNASSIGNED",
                    localDiskRetained=True, otherMembershipsUnchanged=True, noOp=no_op)

    def _delete(self, state, role, selected):
        item = state["vehicles"][role]
        if not item.get("unitId") and item.get("cloud"):
            raise EnvironmentError("PARTIAL_PROVISIONING_REQUIRES_RECONCILIATION")
        if not item.get("unitId"):
            return {"lifecycle": "NEVER_PROVISIONED", "alreadyAbsent": True}
        if item["cloud"]["lifecycle"] not in ("DEPROVISIONED", "DELETED"):
            raise EnvironmentError("UNIT_DEPROVISION_REQUIRED")
        if item["runtime"]["state"] != "STOPPED":
            raise EnvironmentError("UNIT_RETIREMENT_PROOF_REQUIRED")
        self.environment._assert_unheld(self.root / item["overlay"])
        if item["cloud"]["lifecycle"] != "DELETED":
            value = self._cloud("read", unitId=item["unitId"])["unit"]
            if value is None or value["status"] != "new" or value["online_status"] != "Offline":
                raise EnvironmentError("UNIT_DELETE_PRECONDITION_FAILED")
            opposite = state["cloudBinding"]["sets"]["production" if role == "test" else "test"]
            if opposite in value["unit_sets"]:
                raise EnvironmentError("UNIT_HAS_CROSSED_ROLE_MEMBERSHIP")
            if item["unitSetId"] in value["unit_sets"]:
                self._intent(state, role, "REMOVE_SET")
                self._cloud("remove", unitId=item["unitId"], systemUid=item["systemUid"], unitSetId=item["unitSetId"])
                self._wait(state, role, lambda unit: unit and item["unitSetId"] not in unit["unit_sets"], "MEMBERSHIP_REMOVED")
                self._done(state, role)
            self._intent(state, role, "DELETE_UNIT")
            self._cloud("delete", unitId=item["unitId"], systemUid=item["systemUid"])
        result = self._cloud("absence", unitId=item["unitId"], nodeId=item["nodeId"])
        sets = self._bindings(state, result["inventory"])
        if not result["absent"] or sets[role]["members"]:
            raise EnvironmentError("UNIT_DELETE_ABSENCE_NOT_PROVEN")
        item["cloud"].update(lifecycle="DELETED", absenceConfirmed=True)
        self._done(state, role)
        self.progress(role + ": Unit deleted; Unit and Node absence confirmed; disk retained")
        return {"unitId": item["unitId"], "lifecycle": "DELETED", "unitAbsent": True,
                "nodeAbsent": True, "roleSetEmpty": True, "localDiskRetained": True}

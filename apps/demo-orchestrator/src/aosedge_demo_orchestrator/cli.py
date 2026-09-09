# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Command-line adapter for the native Demo Orchestrator."""

import argparse
import json
import math
import getpass
import sys
from typing import List, Optional

from . import __version__
from .application import DemoOrchestrator
from .models import OperationRequest, OperationResult, OperationState, VehicleTarget
from .status import StatusService
from .environment import EnvironmentError


TARGETS = tuple(target.value for target in VehicleTarget)

def read_timeout(value):
    number = float(value)
    if not math.isfinite(number) or not 0.2 <= number <= 30:
        raise argparse.ArgumentTypeError("timeout must be between 0.2 and 30 seconds")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="democtl", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--output",
        choices=("human", "json"),
        default="human",
        help="result format (default: human)",
    )
    commands = parser.add_subparsers(dest="domain", required=True)
    backend = commands.add_parser("backend", help="owned functional backend containers, separate from Cloud and vehicle functions")
    backend_commands = backend.add_subparsers(dest="action", required=True)
    for action in ("build", "start", "stop", "status"):
        command = backend_commands.add_parser(action, help="explicit development build" if action == "build" else "owned backend " + action)
        command.add_argument("team", choices=("brake", "tire"))

    workspace = commands.add_parser("workspace", help="built-in-display window composition only")
    workspace_commands = workspace.add_subparsers(dest="action", required=True)
    workspace_commands.add_parser("status", help="read demo window geometry; no lifecycle actions")
    workspace_commands.add_parser("restore", help="place owned demo windows; no VM, Cloud or driving action")
    workspace_commands.add_parser("close", help="close owned Presenter windows and background; preserve simulation, VMs and Cloud")

    ui = commands.add_parser("ui", help="local Presenter UI")
    ui.add_subparsers(dest="action", required=True).add_parser("serve", help="serve the built UI and protected Test-first operations on loopback")
    demo = commands.add_parser("demo", help="operator's complete Test-first demo workflow")
    demo_commands = demo.add_subparsers(dest="action", required=True)
    for action in ("plan", "prepare"):
        command = demo_commands.add_parser(action, help="read the plan" if action == "plan" else "prepare the Test demo through shared Demo Control operations")
        command.add_argument("--image", required=True, help="factory version/architecture from image list")
        command.add_argument("--target", choices=("test", "all"), default="test", help="owned roles; Studio defaults to Test only")
    access = commands.add_parser("access", help="native VM enrollment input")
    access.add_subparsers(dest="action", required=True).add_parser("setup", help="native password dialog; optional Keychain save")

    status = commands.add_parser("status", help="read local VM, guest and Cloud observations")
    status.add_argument("target", nargs="?", choices=TARGETS, default="all")
    status.add_argument("--guest", action="store_true", help="read guest services and DNS using existing SSH access")
    status.add_argument("--cloud", action="store_true", help="read authenticated OEM/SP access and configured Unit state")
    status.add_argument("--timeout", type=read_timeout, default=8.0, help="read budget per probe in seconds (default: 8)")
    status.add_argument("--profile", help="read only this configured Cloud profile (requires --cloud)")
    status.add_argument("--config", help="local operator observation configuration; never a lifecycle journal")
    status.add_argument("--details", action="store_true", help="include service properties and effective permission names")

    image = commands.add_parser("image", help="discover published immutable factory images")
    image_commands = image.add_subparsers(dest="action", required=True)
    image_commands.add_parser("list", help="list readable version/architecture selectors without hashing images")
    factory_build = image_commands.add_parser("build", help="build the authorized Factory .31 from committed sources using the warm offline Builder")
    factory_build.add_argument("image", choices=("6.1.1-maninblack.31",))

    component = commands.add_parser("component", help="operate on VDP bundles in the artifact catalog")
    component_commands = component.add_subparsers(dest="action", required=True)
    component_commands.add_parser("list", help="list retained VDP artifact versions")
    for action in ("sm-builder-start", "sm-builder-stop", "sm-build", "sm-test", "sm-apply"):
        command = component_commands.add_parser(action, help="bounded Test SM qualification: dedicated existing Builder, port 10024")
        command.add_argument("target", choices=("test",))
    component_status = component_commands.add_parser("status", help="read active slot and provider-reported telemetry readiness")
    component_status.add_argument("target", choices=("test", "production"))
    sm_status = component_commands.add_parser("sm-status", help="read effective SM binary and Safe Stop freshness profile")
    sm_status.add_argument("target", choices=("test",))
    component_logs = component_commands.add_parser("logs", help="read bounded, redacted SM/CM/provider events")
    component_logs.add_argument("target", choices=("test", "production"))
    component_diagnose = component_commands.add_parser("diagnose", help="compare installed KUKSA schema against the fixed 23-path contract; read-only")
    component_diagnose.add_argument("target", choices=("test", "production"))
    for action in ("schema-apply", "schema-remove"):
        schema = component_commands.add_parser(action, help="temporary Test-only eight-leaf KUKSA schema; one service restart, no image or permission change")
        schema.add_argument("target", choices=("test",))
    for action in ("inspect", "unpack", "prepare", "verify", "sign", "cloud-status", "upload", "approve", "unapprove", "send"):
        command = component_commands.add_parser(action)
        if action == "prepare":
            command.add_argument("component_version", nargs="?", help="engineering override; omit to allocate a fresh release")
        elif action == "cloud-status":
            command.add_argument("component_version", nargs="?", help="exact release; omit for a focused Cloud-only Test overview")
        else:
            command.add_argument("component_version", help="exact version from component list")
        if action == "prepare":
            command.add_argument("--profile", dest="content_profile", choices=("v1", "v2", "v3"),
                                 help="reuse this functional profile in a new release >=4.0.0")

    environment = commands.add_parser("environment", help="manage the current demo environment")
    environment_commands = environment.add_subparsers(dest="action", required=True)
    create = environment_commands.add_parser("create", help="copy a factory image and create fresh local overlays; no boot")
    selection = create.add_mutually_exclusive_group(required=True)
    selection.add_argument("--image", help="exact version/architecture selector from image list")
    selection.add_argument("--image-path", help="exact published image path in the artifact catalog")
    create.add_argument("--target", choices=TARGETS, required=True)
    prepare = environment_commands.add_parser("prepare", help="start/provision target VMs and connect only the explicit current role")
    prepare.add_argument("--target", choices=TARGETS, required=True, help="VMs to prepare, not VMs to connect simultaneously")
    prepare.add_argument("--current", choices=("test", "production"), required=True, help="the one VM to connect to CARLA/Gateway")
    for action in ("park", "resume"):
        environment_commands.add_parser(action, help="agreed interface; not implemented yet")
    environment_commands.add_parser("retire", help="remove unused local overlays and factory copy; keep original artifact")
    vehicle = commands.add_parser("vehicle", help="select the single live vehicle")
    vehicle_commands = vehicle.add_subparsers(dest="action", required=True)
    initialize = vehicle_commands.add_parser("initialize", help="first Test connection in stationary Manual, before or after provisioning")
    initialize.add_argument("target", choices=("test",))
    select = vehicle_commands.add_parser("select", help="Safe Stop, detach, scene reset and connect one role")
    select.add_argument("target", choices=("test", "production"))
    connectivity = vehicle_commands.add_parser("connectivity", help="selected vehicle external world; preserve CARLA, VISS and control")
    connectivity.add_argument("link_action", choices=("status", "off", "on"))
    connectivity.add_argument("--target", choices=("test", "production"), help="defaults to Current Vehicle; off requires that same Current Vehicle")

    simulation = commands.add_parser("simulation", help="manage owned CARLA, Controller and Gateway; no VM/Cloud changes")
    simulation_commands = simulation.add_subparsers(dest="action", required=True)
    simulation_commands.add_parser("start", help="start simulation without selecting a VM; ready repeat is a no-op")
    simulation_commands.add_parser("stop", help="Safe Stop, detach and gracefully stop simulation; preserve VMs")

    vm = commands.add_parser("vm", help="manage local VM processes")
    vm_commands = vm.add_subparsers(dest="action", required=True)
    for action in ("start", "stop"):
        command = vm_commands.add_parser(action)
        command.add_argument("target", choices=TARGETS)
        command.add_argument("--timeout", type=vm_timeout, default=90.0, help="guest wait budget per VM, 1–300 seconds (default 90)")

    unit = commands.add_parser("unit", help="manage AosCloud Unit lifecycle")
    unit_commands = unit.add_subparsers(dest="action", required=True)
    for action in ("provision", "deprovision", "delete"):
        command = unit_commands.add_parser(action)
        command.add_argument("target", choices=TARGETS)
    unassign = unit_commands.add_parser("unassign", help="remove stopped Test from its role set; preserve provisioned Unit and disk")
    unassign.add_argument("target", choices=("test",))

    return parser


def request_from_arguments(arguments: argparse.Namespace) -> OperationRequest:
    if arguments.domain == "status":
        return OperationRequest("orchestrator", "status", VehicleTarget(arguments.target),
                                guest=arguments.guest, cloud=arguments.cloud,
                                timeout=arguments.timeout, profile=arguments.profile)
    return OperationRequest(
        domain=arguments.domain,
        action=("connectivity-" + arguments.link_action if getattr(arguments, "link_action", None) else arguments.action),
        target=VehicleTarget(arguments.target) if getattr(arguments, "target", None) else None,
        image=getattr(arguments, "image", None), image_path=getattr(arguments, "image_path", None),
        current=getattr(arguments, "current", None),
        component_version=getattr(arguments, "component_version", None),
        content_profile=getattr(arguments, "content_profile", None),
        team=getattr(arguments, "team", None),
        timeout=getattr(arguments, "timeout", 8.0),
    )


def render_human(result: OperationResult, details: bool = False) -> str:
    document = result.to_dict()
    summary = f"{document['state']} {document['operation']}"
    if "target" in document:
        summary += f" target={document['target']}"
    if "technical_role" in document:
        summary += f" role={document['technical_role']}"
    lines = [summary, document["message"]]
    data = document.get("data")
    if data and document["operation"].startswith("vehicle.connectivity-"):
        lines.append("Vehicle: " + data["target"] + "; external connectivity: " + data["state"])
        lines.append("Filter evidence only; AosCloud Online/Offline is observed separately.")
    if data and document["operation"].startswith("workspace."):
        lines.append(json.dumps(data, indent=2, sort_keys=True))
    if data and document["operation"].startswith("component."):
        lines.append(json.dumps(data, indent=2, sort_keys=True))
    if data and document["operation"].startswith("backend."):
        lines.append(json.dumps(data, indent=2, sort_keys=True))
    if data and document["operation"].startswith("demo."):
        lines.append("VDP: " + str(data.get("contentProfile", "v1")) + " / " + str(data.get("version", "not selected")))
        lines.append("Phase: " + data.get("phase", "not observed"))
    if data and document["operation"].startswith("simulation."):
        lines.append("Simulation: " + data["state"] + (" (unchanged)" if data["noOp"] else ""))
        lines.append("Current Vehicle: " + str(data.get("currentVehicle") or "none"))
        if data.get("physicalStop"):
            lines.append("Physical stop: " + data["physicalStop"])
        if data.get("workspace"):
            lines.append("Workspace: " + data["workspace"]["state"])
            lines.extend(data["workspace"].get("problems", []))
    if data and document["operation"] in ("environment.prepare", "vehicle.select"):
        lines.append("Current Vehicle: " + data["currentVehicle"] + (" (unchanged)" if data["noOp"] else ""))
        lines.append("Profile: " + data["trustProfile"] + "; per-Unit mTLS: " + data["perUnitMtls"])
        for role, value in data["vehicles"].items():
            lines.append(role + ": source=" + value["gate"] + "; VDP=" + value["vdpProcess"]
                         + "; VDP data=" + value["vdpData"])
    if data and document["operation"].startswith("unit."):
        for role, item in data["vehicles"].items():
            lines.append(role + ": " + item["state"] + " " + item.get("reason", ""))
            lines.append("  " + json.dumps({k: v for k, v in item.items() if k not in ("state", "reason")}, sort_keys=True))
    if data and document["operation"] == "image.list":
        for item in data["images"]:
            lines.append(item["selector"] + "  " + str(item["sizeBytes"]) + " bytes  " + item["state"])
            if item["problems"]:
                lines.append("  " + ", ".join(item["problems"]))
        if not data["images"]:
            lines.append("No published images found.")
        for issue in data["issues"]:
            lines.append("  " + issue["reason"])
    if data and document["operation"] == "environment.create":
        lines.append("Factory copy: " + data["factory"]["path"])
        for role, vehicle in data["vehicles"].items():
            lines.append(role + ": " + vehicle["overlay"] + "  " + vehicle["state"])
        lines.append("Current Vehicle: none")
    if data and document["operation"] == "environment.retire":
        for path in data["removed"]:
            lines.append("Removed: " + path)
        for path in data.get("preserved", []):
            lines.append("Preserved: " + path)
    if data and document["operation"].startswith("vm."):
        if data.get("infrastructure", {}).get("reason"):
            lines.append("Infrastructure: " + data["infrastructure"]["reason"])
        for role, item in data["vehicles"].items():
            lines.append(role + ": " + item["state"] + " " + str(item.get("processState", "UNKNOWN")))
            if "durationSeconds" in item:
                lines.append("  Duration: " + str(item["durationSeconds"]) + " s")
            if item.get("reason"):
                lines.append("  " + item["reason"])
            if "guestReady" in item:
                lines.append("  SSH=" + str(item["guestReady"]) + " DNS=" + str(item.get("guestDnsReady")))
            if item.get("factoryRole"):
                value = item["factoryRole"]
                lines.append("  Factory role: " + str(value.get("role", role)) + "; " + value["state"])
            if item.get("access"):
                from .guest_access import ssh_command
                from .status import project_root
                import shlex
                args = ssh_command(project_root() / item["access"], item["sshPort"], 5)
                lines.append("  SSH: " + shlex.join([arg for arg in args[:-2] if arg != "-T"]))
    snapshot = document.get("status")
    if not snapshot:
        return "\n".join(lines)
    lines.append("Observed: " + snapshot["readCompletedAt"])
    journal = snapshot.get("journal", {})
    if journal.get("value"):
        lines.append("Current run: " + journal["value"]["stage"])
    source = snapshot.get("source", {})
    if source:
        if source.get("connectionObservation") == "NOT_REQUESTED":
            selected = source.get("selectedVehicle")
            lines.append("CARLA selected VM: " + (selected or "none") + " (connection not probed)")
            confirmation = source.get("lastConnectionConfirmation") or {}
            lines.append("Last connection confirmation: " + str(confirmation.get("confirmedAt") or "not recorded"))
        else:
            connected = source.get("currentVehicle", "unknown")
            lines.append("CARLA connected VM: " + ("none" if connected is None else connected))
        lines.append("Source: " + source.get("state", "UNKNOWN"))
        if source.get("reason"):
            lines.append("  " + source["reason"])
        if source.get("trustProfile"):
            lines.append("  " + source["trustProfile"] + "; mTLS=" + source["perUnitMtls"])
        for role, value in source.get("vehicles", {}).items():
            lines.append("  " + role + ": gate=" + value["gate"] + "; VDP=" + value["vdpProcess"] + "; data=" + value["vdpData"])
    config = snapshot["configuration"]
    if config.get("reason"):
        lines.append("Configuration: " + config["reason"] + " (check the local status configuration)")
    for role, vehicle in snapshot["vehicles"].items():
        lines.append("\n" + role + " [" + vehicle["technicalRole"] + "]")
        local = vehicle["local"]
        facts = local.get("value") or {}
        lines.append("  VM: " + str(facts.get("processState") or local.get("reason") or "UNKNOWN"))
        if facts:
            lines.append("  Overlay: " + facts["overlay"])
        if facts.get("configuredImageVersion"):
            lines.append("  Image: " + facts["configuredImageVersion"] + " (configured reference; not rehashed)")
        if local.get("reason") and facts:
            lines.append("  Local: " + local["reason"])
        if "qmp" in facts:
            qmp = facts["qmp"]
            lines.append("  QMP: " + str((qmp.get("value") or {}).get("status") or qmp.get("reason")))
        guest = vehicle["guest"]
        if details and "provisioningForward" in facts:
            lines.append("  Provisioning port states: " + json.dumps(facts["provisioningForward"], sort_keys=True))
        dns = vehicle["hostDns"]
        lines.append("  Host DNS: " + str(dns.get("reason") or "RESPONDING"))
        data = guest.get("value")
        lines.append("  Guest: " + (guest.get("reason") or (data or {}).get("ssh", guest["state"])))
        if data:
            lines.append("  Aos: release=" + str(data["release"]) + " mode=" + data["mode"] + " connection=NOT_OBSERVED")
            lines.append("  Guest DNS: " + ("RESOLVED" if data["dns"]["resolved"] else "UNRESOLVED") +
                         " bridge-port-match=" + str(data["dns"]["portMatches"]))
            if details:
                lines.append("    Boot timing: " + json.dumps(data.get("bootSeconds", {}), sort_keys=True))
                lines.append("    DNS details: " + json.dumps(data["dns"], sort_keys=True))
                lines.append("    Recent CM log categories: " + json.dumps(data.get("cloudLogObservations", {}), sort_keys=True))
                lines.append("    CM process log categories: " + json.dumps(data.get("cloudProcessLogObservations", {}), sort_keys=True))
                lines.append("    CM logging/stop: " + json.dumps(data.get("cloudServiceDetails", {}), sort_keys=True))
                lines.append("    CM boot failures: " + json.dumps(data.get("cloudBootFailures", {}), sort_keys=True))
                lines.append("    CM core metadata: " + json.dumps(data.get("cloudCoreMetadata", {}), sort_keys=True))
                lines.append("    CM start context: " + json.dumps(data.get("cloudStartContext", {}), sort_keys=True))
                lines.append("    CM binary version: " + json.dumps(data.get("cloudBinaryVersion", [])))
            for name, service in data["services"].items():
                lines.append("    " + name + ": " + str(service.get("ActiveState")) + "/" +
                             str(service.get("SubState")) + " restarts=" + str(service.get("NRestarts")))
                if details:
                    lines.append("      load=" + str(service.get("LoadState")) + " result=" + str(service.get("Result")))
    lines.append("\nCloud")
    for name, profile in snapshot["cloud"].items():
        if "access" not in profile:
            lines.append("  " + name + ": " + str(profile.get("reason")))
            continue
        local = profile["credential"].get("value") or {}
        access = profile["access"]
        data = access.get("value") or {}
        lines.append("  " + name + ": credential=" + ("PRESENT" if local.get("present") else "MISSING") +
                     " access=" + str(access.get("reason") or access["state"]))
        certificate = (profile.get("certificate") or {}).get("value") or {}
        if certificate:
            lines.append("    Certificate expires=" + certificate["validUntil"] + " time-valid=" + str(certificate["timeValid"]))
        if data:
            permissions = data["effectivePermissions"]
            lines.append("    Role=" + data["role"] + " owner=" + str(data["ownerId"]) +
                         " effective-permissions=" + ("UNKNOWN" if permissions is None else str(len(permissions))))
            if details and permissions is not None:
                lines.append("    " + ", ".join(permissions))
        for role, unit in profile["units"].items():
            value = unit.get("value")
            if not value:
                lines.append("    Unit " + role + ": " + str(unit.get("reason")))
            else:
                lines.append("    Unit " + role + ": " + value["onlineStatus"] + " / " + value["status"] +
                             " id=" + value["id"])
                lines.append("      Unit Sets=" + str(len(value["unitSets"])) if value["unitSets"] is not None
                             else "      Unit Sets=UNKNOWN")
                if unit.get("reason"):
                    lines.append("      " + unit["reason"])
                if details:
                    lines.append("      " + json.dumps(value, sort_keys=True))
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.domain == "ui":
        from .presenter import serve
        return serve()
    if arguments.domain == "access":
        from .native_access import NativeVMAccess
        access = NativeVMAccess(progress=lambda message: print(message, file=sys.stderr, flush=True))
        try:
            access("test")
            print("COMPLETED access.setup — native VM access available; no VM or Cloud action")
            return 0
        except EnvironmentError as error:
            print("BLOCKED access.setup " + str(error), file=sys.stderr)
            return 1
        finally:
            access.clear()
    service = StatusService(config_path=getattr(arguments, "config", None))
    from .vm import VMService
    def password_provider(role):
        if not sys.stdin.isatty():
            return None
        return getpass.getpass("Guest root password for first SSH setup (" + role + "): ")
    vm_service = VMService(password_provider=password_provider,
                          progress=lambda message: print(message, file=sys.stderr, flush=True))
    native_access = None
    if arguments.domain == "demo" and arguments.action == "prepare":
        from .native_access import NativeVMAccess
        native_access = NativeVMAccess(progress=vm_service.progress)
        vm_service.password_provider = native_access
    try:
        result = DemoOrchestrator(service, vm_service=vm_service).execute(request_from_arguments(arguments))
    except ValueError:
        parser.error("invalid status options; --profile requires --cloud")
    except KeyboardInterrupt:
        print("INTERRUPTED: current VM/Cloud state retained; reconcile before continuing.", file=sys.stderr)
        return 130
    finally:
        if native_access:
            native_access.clear()
    if arguments.output == "json":
        print(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))
    else:
        print(render_human(result, getattr(arguments, "details", False)))
    if result.state in (OperationState.READY, OperationState.OBSERVED, OperationState.COMPLETED):
        return 0
    return 1 if result.state in (OperationState.PARTIAL, OperationState.BLOCKED) else 2


def vm_timeout(value):
    number = float(value)
    if not math.isfinite(number) or not 1 <= number <= 300:
        raise argparse.ArgumentTypeError("VM timeout must be between 1 and 300 seconds")
    return number

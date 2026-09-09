# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Transport-neutral adapter for the future loopback-only local API."""

from typing import Any, Dict, Mapping, Optional

from .application import DemoOrchestrator
from .models import OperationRequest, VehicleTarget


def execute_operation(
    payload: Mapping[str, Any],
    orchestrator: Optional[DemoOrchestrator] = None,
) -> Dict[str, Any]:
    """Execute the same application request used by democtl."""

    domain = payload.get("domain", "")
    action = payload.get("action", "")
    target_value = payload.get("target")
    target = VehicleTarget(target_value) if target_value else None
    application = orchestrator or DemoOrchestrator()
    if domain == "backend" and action in ("start", "stop", "status"):
        if set(payload) != {"domain", "action", "team"} or payload["team"] not in ("brake", "tire"):
            raise ValueError("Backend accepts a fixed team only, never paths, images or commands")
        return application.execute(OperationRequest(domain, action, team=payload["team"])).to_dict()
    if domain == "backend":
        raise ValueError("Backend development builds are CLI-only, never a presentation action")
    if domain == "demo" and action in ("plan", "prepare"):
        if (set(payload) - {"domain", "action", "image", "target"} or not isinstance(payload.get("image"), str)
                or target not in (None, VehicleTarget.TEST, VehicleTarget.ALL)):
            raise ValueError("Demo preparation accepts a catalog image and Test or all target only")
        return application.execute(OperationRequest(domain, action, target or VehicleTarget.TEST, image=payload["image"])).to_dict()
    if domain == "component" and action in ("sm-builder-start", "sm-builder-stop", "sm-build", "sm-test", "sm-apply", "sm-status"):
        if set(payload) != {"domain", "action", "target"} or target != VehicleTarget.TEST:
            raise ValueError("SM qualification accepts Test only, no caller-selected paths or commands")
        return application.execute(OperationRequest(domain, action, target)).to_dict()
    if domain == "component" and action in ("status", "logs", "diagnose", "schema-apply", "schema-remove"):
        if set(payload) != {"domain", "action", "target"} or target not in (VehicleTarget.TEST, VehicleTarget.PRODUCTION):
            raise ValueError("Component status requires one role")
        if action in ("schema-apply", "schema-remove") and target != VehicleTarget.TEST:
            raise ValueError("Temporary schema operations require Test")
        return application.execute(OperationRequest(domain, action, target)).to_dict()
    if domain == "component" and action in ("list", "inspect", "unpack", "prepare", "verify", "sign", "cloud-status", "upload", "approve", "unapprove", "send"):
        expected = {"domain", "action"} if action == "list" else {"domain", "action", "component_version"}
        if action == "cloud-status" and "component_version" not in payload:
            expected.remove("component_version")
        if action == "prepare" and "content_profile" in payload:
            expected.add("content_profile")
            if "component_version" not in payload:
                expected.remove("component_version")
        if set(payload) != expected:
            raise ValueError("Component operations accept only a catalog version, never paths or credentials")
        return application.execute(OperationRequest(domain, action,
            component_version=payload.get("component_version"), content_profile=payload.get("content_profile"))).to_dict()
    if domain == "workspace" and action in ("status", "restore", "close"):
        if set(payload) != {"domain", "action"}:
            raise ValueError("Workspace accepts no paths, targets or caller-selected windows")
        return application.execute(OperationRequest(domain, action)).to_dict()
    if domain == "simulation" and action in ("start", "stop"):
        if set(payload) != {"domain", "action"}:
            raise ValueError("Simulation uses only the owned current environment")
        return application.execute(OperationRequest(domain, action)).to_dict()
    if domain == "environment" and action == "prepare":
        if set(payload) != {"domain", "action", "target", "current"}:
            raise ValueError("Prepare requires only an explicit target and current vehicle")
        request = OperationRequest(domain, action, target, current=payload["current"])
        if request.selection_error():
            raise ValueError(request.selection_error())
        return application.execute(request).to_dict()
    if domain == "vehicle" and action in ("select", "initialize"):
        if set(payload) != {"domain", "action", "target"}:
            raise ValueError("Vehicle select accepts only one target")
        request = OperationRequest(domain, action, target)
        if action == "initialize" and target != VehicleTarget.TEST:
            raise ValueError("Initial Manual connection requires Test")
        if request.selection_error():
            raise ValueError(request.selection_error())
        return application.execute(request).to_dict()
    if domain == "unit" and action in ("provision", "deprovision", "delete", "unassign"):
        if set(payload) != {"domain", "action", "target"} or target is None:
            raise ValueError("Unit requests accept only action and target")
        if action == "unassign" and target != VehicleTarget.TEST:
            raise ValueError("Unit unassign is Test-only")
        return application.execute(OperationRequest(domain, action, target)).to_dict()
    if domain == "vm" and action in ("start", "stop"):
        if set(payload) != {"domain", "action", "target"} or target is None:
            raise ValueError("VM requests accept only action and target")
        return application.execute(OperationRequest(domain, action, target, timeout=90)).to_dict()
    if domain == "environment" and action == "retire":
        if set(payload) != {"domain", "action"}:
            raise ValueError("Retire accepts no caller-selected targets, paths or force flag")
        return application.execute(OperationRequest(domain, action)).to_dict()
    if domain == "image" and action == "list":
        if set(payload) - {"domain", "action"}:
            raise ValueError("Unsupported image list field")
        return application.execute(OperationRequest(domain, action)).to_dict()
    if domain == "image" and action == "build":
        if set(payload) != {"domain", "action", "image"} or payload["image"] != "6.1.1-maninblack.31":
            raise ValueError("Only the authorized Factory .31 build is available")
        return application.execute(OperationRequest(domain, action, image=payload["image"])).to_dict()
    if domain == "environment" and action == "create":
        # CLI paths do not become a browser-controlled filesystem capability.
        if set(payload) - {"domain", "action", "target", "image"}:
            raise ValueError("Unsupported create field; API accepts a catalog selector only")
        if not isinstance(payload.get("image"), str) or not payload["image"] or target is None:
            raise ValueError("Explicit image selector and target required")
        return application.execute(OperationRequest(domain, action, target, image=payload["image"])).to_dict()
    if domain == "orchestrator" and action == "status":
        # The future server binds configuration and credentials; callers cannot
        # select local paths, profiles, Cloud endpoints or executables.
        if set(payload) - {"domain", "action", "target", "guest", "cloud"}:
            raise ValueError("Unsupported status request field")
        if type(payload.get("guest", False)) is not bool or type(payload.get("cloud", False)) is not bool:
            raise ValueError("Status read modes must be booleans")
        return application.execute(OperationRequest(domain, action, target,
            guest=payload.get("guest", False), cloud=payload.get("cloud", False))).to_dict()
    return application.execute(OperationRequest(domain, action, target)).to_dict()

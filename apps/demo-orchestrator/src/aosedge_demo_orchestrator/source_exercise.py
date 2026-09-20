# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded qualification motion through the existing single CARLA tick owner."""
import time
from uuid import uuid4

from .environment import EnvironmentError
from .status import now


def execute(service, state, kind):
    source = state.get("source") or {}
    recovery = kind == "return_to_road"
    if kind not in ("brake", "tire", "return_to_road") or state.get("currentVehicle") != "test" or "test" not in state.get("vehicles", {}):
        raise EnvironmentError("SIMULATION_EXERCISE_REQUIRES_SELECTED_TEST")
    if source.get("operation") or source.get("stopOperation"):
        raise EnvironmentError("SIMULATION_EXERCISE_SOURCE_OPERATION_PENDING")
    driver = service.driver
    observed = driver.ready(state)
    if observed.get("exerciseSupported") is not True:
        raise EnvironmentError("SIMULATION_EXERCISE_REQUIRES_UPDATED_CONTROLLER")
    if recovery and observed.get("roadRecoverySupported") is not True:
        raise EnvironmentError("ROAD_RECOVERY_REQUIRES_UPDATED_CONTROLLER")
    record = source.get("exercise")
    resume = bool(record and record.get("phase") != "RELEASED")
    if resume:
        if record.get("kind") != kind or record.get("runId") != source["runId"]:
            raise EnvironmentError("SIMULATION_EXERCISE_RECONCILIATION_REQUIRED")
    else:
        if observed.get("held"):
            raise EnvironmentError("SIMULATION_EXERCISE_CONTROLLER_BUSY")
        record = dict(id=str(uuid4()), kind=kind, runId=source["runId"], phase="INTENT", startedAt=now())
        source["exercise"] = record
        service.vm._save(state)
    identity = record["id"]
    observed = driver.rpc(source, "status", identity)
    if observed.get("held") and observed.get("operationId") != identity:
        raise EnvironmentError("SIMULATION_EXERCISE_CONTROLLER_BUSY")

    def intent(action):
        record["phase"] = action.upper() + "_ATTEMPTED"
        service.vm._save(state)
        return driver.rpc(source, action, identity)

    # Reconcile an uncertain command by its existing operation identity. Never
    # restart an exercise or reset its scene after it has begun.
    if observed.get("operationId") != identity:
        if record["phase"] not in ("INTENT", "SAFE_STOP_ATTEMPTED"):
            raise EnvironmentError("SIMULATION_EXERCISE_OPERATION_LOST")
        driver.progress("Test maneuver: confirming physical Safe Stop")
        observed = intent("safe_stop")
    if observed["phase"] == "STOPPING":
        observed = driver.wait(source, identity, "SAFE_STOP")
    if observed["phase"] == "SAFE_STOP" and not (observed.get("exercise") or {}).get("id") == identity:
        observed = intent("reset")
    if observed["phase"] == "RESETTING":
        observed = driver.wait(source, identity, "RESET")
    if observed["phase"] == "RESET_FAILED" or record.get("resetError"):
        reason=record.get("resetError") or observed.get("resetError")
        if reason not in ("ROAD_POSITION_INVALID","ROAD_POSITION_OCCUPIED","ROAD_POSITION_UNCONFIRMED"):
            raise EnvironmentError("ROAD_RECOVERY_REJECTION_UNCONFIRMED")
        record["resetError"]=reason
        service.vm._save(state)
        released=observed if observed.get("phase")=="RELEASED" else intent("release")
        if released.get("held") or released.get("phase")!="RELEASED":
            raise EnvironmentError("ROAD_RECOVERY_RELEASE_UNCONFIRMED")
        result=dict(state="FAILED",kind=kind,reason=reason,noOp=resume,currentVehicle="test",operationId=identity,
                    physicalStop="CONFIRMED",modelQualification="NOT_EVALUATED")
        record.update(phase="RELEASED",finishedAt=now(),result=result)
        service.vm._save(state)
        return result
    if observed["phase"] == "RESET":
        # Reset can report one stationary frame before the respawned car
        # settles onto the road. Confirm an advancing, stable stopped interval
        # before asking the existing controller to start motion. Never retry a
        # rejected start blindly or relax the controller's physical-stop gate.
        settle_deadline = time.monotonic() + 5
        stable_since, last_frame = None, None
        while True:
            frame = observed.get("frame") or {}
            checked_at = time.monotonic()
            if observed.get("operationId") != identity or observed.get("phase") != "RESET":
                raise EnvironmentError("SIMULATION_EXERCISE_RESET_IDENTITY_MISMATCH")
            stopped = (observed.get("fresh") is True and frame.get("activeMode") == "SAFE_STOP"
                and isinstance(frame.get("frameId"), int) and frame.get("speedKmh", 1) <= .5
                and frame.get("brake", 0) >= .99 and (not recovery or frame.get("roadReady") is True))
            if not stopped:
                stable_since = None
            elif frame["frameId"] != last_frame:
                if stable_since is None:
                    stable_since = checked_at
                elif checked_at - stable_since >= .5:
                    break
            last_frame = frame.get("frameId")
            if checked_at >= settle_deadline:
                raise EnvironmentError("SIMULATION_EXERCISE_RESET_NOT_SETTLED")
            time.sleep(.05)
            observed = driver.rpc(source, "status", identity)
        if recovery:
            driver.progress("Return to road: confirming stationary Manual; Autopilot stays off")
            observed=intent("manual_ready")
        else:
            driver.progress("Test maneuver: " + kind + " real CARLA motion; maximum 60 seconds")
            observed = intent("exercise_" + kind)
    if recovery:
        if observed.get("phase")=="MANUAL_PREPARING":
            observed=driver.wait(source,identity,"MANUAL_READY")
        if observed.get("phase")=="MANUAL_READY":
            observed=intent("release_manual")
        if observed.get("operationId")!=identity or observed.get("held") or observed.get("phase")!="RELEASED":
            raise EnvironmentError("ROAD_RECOVERY_UNCONFIRMED")
        frame=observed.get("frame") or {}
        if (record.get("phase")!="RELEASE_MANUAL_ATTEMPTED" or observed.get("fresh") is not True or
                frame.get("activeMode")!="MANUAL" or frame.get("speedKmh",1)>.5 or frame.get("brake",0)<.99):
            raise EnvironmentError("ROAD_RECOVERY_MANUAL_UNCONFIRMED")
        result=dict(state="COMPLETED",kind=kind,reason="NONE",noOp=resume,currentVehicle="test",operationId=identity,
                    physicalStop="CONFIRMED",driveMode="MANUAL",autopilotStarted=False,modelQualification="NOT_EVALUATED")
        record.update(phase="RELEASED",finishedAt=now(),result=result)
        service.vm._save(state)
        return result
    deadline, heartbeat = time.monotonic() + 65, time.monotonic() + 10
    while True:
        motion = observed.get("exercise") or {}
        if observed.get("operationId") != identity or motion.get("id") != identity or motion.get("kind") != kind:
            raise EnvironmentError("SIMULATION_EXERCISE_IDENTITY_MISMATCH")
        if motion.get("state") in ("COMPLETED", "ABORTED"):
            break
        if motion.get("state") != "RUNNING" or time.monotonic() >= deadline:
            raise EnvironmentError("SIMULATION_EXERCISE_UNCONFIRMED; control lease expires to Safe Stop")
        if time.monotonic() >= heartbeat:
            driver.progress("Test maneuver: " + kind + " in progress; same operation, no restart")
            heartbeat = time.monotonic() + 10
        time.sleep(.25)
        observed = driver.rpc(source, "status", identity)
    if observed.get("phase") != "RELEASED":
        driver.wait(source, identity, "SAFE_STOP")
        observed = intent("release")
        if observed.get("held") or observed.get("phase") != "RELEASED":
            raise EnvironmentError("SIMULATION_EXERCISE_RELEASE_UNCONFIRMED")
    result = dict(state=motion["state"], kind=kind, reason=motion["reason"],
        operationId=identity, metrics=motion.get("metrics", {}), noOp=resume,
        currentVehicle="test", physicalStop="CONFIRMED", modelQualification="NOT_EVALUATED")
    record.update(phase="RELEASED", finishedAt=now(), result=result)
    service.vm._save(state)
    return result

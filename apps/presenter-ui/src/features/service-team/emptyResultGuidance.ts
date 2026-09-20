// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import type { selectFunction } from "./functionObservation";

/** Shared card/dialog guidance, only from current source observations. */
export function emptyResultGuidance(fn: ReturnType<typeof selectFunction>, team: "brake" | "tire") {
  if (fn.state !== "CURRENT" || !fn.item) return {
    status: "Input not confirmed",
    text: fn.state === "LAST_KNOWN" ? "Only last-known input is available. Current telemetry readiness is not confirmed."
      : "Waiting for a current service input report. Backend contact alone does not confirm telemetry readiness.",
  };
  const c = fn.item.message.content;
  if (c.input.state === "ACCESS_DENIED" || c.connection === "ACCESS_DENIED")
    return { status: "Input access denied", text: "The service reports denied input access. Driving cannot resolve this access failure." };
  if (c.connection === "REAUTHENTICATING" || c.input.reason === "REAUTHENTICATING")
    return { status: "Renewing input access", text: "Renewing local input access. Waiting for authenticated telemetry to resume." };
  if (c.input.state === "STALE")
    return { status: "Waiting for fresh input", text: `Source data is stale. Waiting for fresh input before the next ${team === "brake" ? "recording" : "driving exercise"}.` };
  if (c.input.state === "INVALID")
    return { status: "Input rejected", text: "Source input failed validation. A new result requires valid input; driving alone may not resolve this." };
  if (c.input.state === "DISCONNECTED" || c.connection === "DISCONNECTED")
    return { status: "Input disconnected", text: "Local telemetry is disconnected. Waiting for the input connection to recover." };
  if (c.input.state !== "RECEIVING")
    return { status: "Waiting for input", text: "The service is waiting for usable local input. No denied access or telemetry readiness is confirmed." };
  if (c.delivery.state === "BLOCKED")
    return { status: "Delivery blocked", text: "Input is arriving, but the service reports blocked delivery. No new backend result is confirmed." };
  if (c.delivery.queuedMessages > 0 || ["PENDING", "RETRYING"].includes(c.delivery.state))
    return { status: "Delivery pending", text: "Input is arriving; retained messages are awaiting backend delivery. A new result is not confirmed yet." };
  if (["PRE", "ACTIVE", "POST"].includes(c.activity.state))
    return { status: team === "brake" ? "Recording in progress" : "Driving exercise in progress", text: `Input is arriving and a ${team === "brake" ? "recording" : "driving exercise"} is in progress. Waiting for its outcome.` };
  if (c.activity.state === "SKIPPED")
    return { status: team === "brake" ? "Recording did not qualify" : "Driving exercise did not qualify", text: `Input is arriving, but the last ${team === "brake" ? "recording" : "driving exercise"} did not qualify. Inspect the activity reason before the next attempt.` };
  if (c.activity.state === "COMPLETED")
    return { status: "Waiting for result receipt", text: `The service reports a completed ${team === "brake" ? "recording" : "driving exercise"}. No matching backend result is confirmed yet.` };
  return { status: team === "brake" ? "Waiting for braking result" : "Waiting for drive result",
    text: team === "brake" ? "Input is arriving. Waiting for a qualifying braking episode."
      : "Input is arriving. Waiting for a completed driving exercise." };
}

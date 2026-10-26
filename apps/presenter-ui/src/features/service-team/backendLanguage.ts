// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { readable } from "./useBackendObservation";

/** Display vocabulary only. Never changes evidence selection or readiness. */
export function backendLabel(value: unknown, axis?: "input" | "activity" | "delivery") {
  if (value === "WAITING") return axis === "input" ? "Waiting for vehicle data" : axis === "activity" ? "Waiting for a suitable event" : "Waiting";
  const labels: Record<string, string> = {
    RECEIVING: "Receiving", STALE: "Stale", DISCONNECTED: "Disconnected", INVALID: "Invalid input", PRE: "Preparing event", ACTIVE: "Event in progress", POST: "Finishing event",
    COMPLETED: "Completed", SKIPPED: "Event skipped", IDLE: "No queued delivery", PENDING: "Delivery pending",
    RETRYING: "Retrying delivery", BLOCKED: "Delivery blocked", NOT_QUALIFIED: "Waiting for a suitable maneuver",
    INSUFFICIENT_SAMPLES: "More samples needed", SOURCE_DISCONTINUITY: "Vehicle scene changed",
    REAUTHENTICATING: "Renewing access", NONE: "", AWAITING_INPUT: "Waiting for vehicle data",
    SOURCE_GAP: "Vehicle data gap", INVALID_SAMPLE: "Invalid sample", INVALID_INPUT: "Invalid input",
    TRANSPORT_LOST: "Connection lost", ACCESS_DENIED: "Access denied", STORAGE_UNAVAILABLE: "Storage unavailable",
    BRAKE_HEALTH_ASSESSMENT: "Brake condition assessment", TIRE_HEALTH_ASSESSMENT: "Tire condition assessment",
    WINDOW_COMPLETION: "Braking recording", BRAKE_EVENT: "Brake event", TIRE_EVENT: "Tire event",
    DURABLY_RECEIVED: "Received", CONFLICT: "Integrity conflict",
  };
  return typeof value === "string" && value in labels ? labels[value] : readable(value);
}

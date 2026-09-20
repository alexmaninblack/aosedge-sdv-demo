// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
export function recordingLabel(state: unknown): string {
  const labels: Record<string, string> = {
    COMPLETE: "Recording complete",
    INCOMPLETE_SOURCE_GAP: "Recording interrupted: source data gap",
    TRUNCATED_MAX_DURATION: "Recording stopped at the duration limit",
    ABORTED_SERVICE_STOP: "Recording interrupted: service stopped",
    ABORTED_RESTART: "Recording interrupted: service restarted",
  };
  return typeof state === "string" && labels[state] ? labels[state] : "Recording outcome not confirmed";
}

/** Chunk delivery does not repair an incomplete source recording. */
export function windowDeliveryLabel(window: Record<string, unknown>): string {
  const received = window.receivedChunkCount, expected = window.expectedChunkCount;
  if (!Number.isSafeInteger(received) || Number(received) < 0 || Number(received) > 15)
    return "Chunk delivery not confirmed";
  if (!Number.isSafeInteger(expected) || Number(expected) < 1 || Number(expected) > 15)
    return `${received} chunks received · total not yet reported`;
  if (Number(received) > Number(expected)) return "Chunk delivery inconsistent";
  const counts = `(${received}/${expected})`;
  return received === expected && window.deliveryState === "DURABLY_RECEIVED"
    ? `All retained chunks received ${counts}`
    : `Chunk delivery pending or unconfirmed ${counts}`;
}

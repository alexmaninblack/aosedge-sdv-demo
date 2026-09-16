// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
export type ProductRow = { backendReceivedAt: string; deliveryState?: string; stale?: boolean; message: {
  messageType?: string; serviceVersion?: string; unitSystemUid?: string;
  content?: unknown; [key: string]: unknown;
} };
export type Resource = { state: string; data?: Record<string, unknown> };
export const object = (value: unknown): Record<string, unknown> => value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};

/** Backend projections only: no guest reads, mock fallback or advisory claim. */
export function productRows(resources: Record<string, Resource | undefined>, uid: string): ProductRow[] {
  const rows: ProductRow[] = [];
  for (const name of ["productData", "assessments", "events", "advisories", "functionStatus"]) {
    const data = resources[name]?.data;
    if (!data) continue;
    if (data.unitSystemUid !== uid || !Array.isArray(data.items) || data.items.length > 10) throw new Error("BACKEND_SCOPE_MISMATCH");
    for (const raw of data.items) {
      const row = object(raw), message = name === "productData" ? row : object(row.message);
      if (message.unitSystemUid !== uid || typeof row.backendReceivedAt !== "string") throw new Error("BACKEND_RECORD_SCOPE_MISMATCH");
      if (name === "productData") rows.push({ backendReceivedAt: row.backendReceivedAt,
        deliveryState: String(row.deliveryState ?? ""), message: { ...message, messageType: "WINDOW_COMPLETION",
          content: { status: row.terminalState, quality: row.terminalState, receivedSampleCount: row.receivedSampleCount,
            receivedChunkCount: row.receivedChunkCount, expectedChunkCount: row.expectedChunkCount } } });
      else rows.push({ backendReceivedAt: row.backendReceivedAt, deliveryState: String(row.deliveryState ?? ""),
        ...(typeof row.stale === "boolean" ? { stale: row.stale } : {}), message });
    }
  }
  return rows.sort((a, b) => b.backendReceivedAt.localeCompare(a.backendReceivedAt));
}

export function completedProduct(row: ProductRow, version: string): boolean {
  if (row.message.serviceVersion !== version || !["DURABLY_RECEIVED", "DURABLE_ACCEPTED"].includes(row.deliveryState ?? "")) return false;
  if (row.message.messageType === "WINDOW_COMPLETION") return object(row.message.content).status === "COMPLETE";
  return ["BRAKE_HEALTH_ASSESSMENT", "TIRE_HEALTH_ASSESSMENT"].includes(row.message.messageType ?? "");
}

// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT

/** Convert only verified bytes, never unitless values or DMIPS to percentages. */
export function formatResource(value: unknown, unit?: string | null, key?: string) {
  if (value === null || value === undefined) return "Not reported";
  if (key === "ram" && typeof value === "number" && Number.isFinite(value) && value >= 0 && /^(bytes|byte|b)$/i.test(unit ?? "")) {
    const gib = value >= 1024 ** 3;
    const scaled = value / 1024 ** (gib ? 3 : 2);
    // Keep small nonzero observations distinguishable from zero.
    return `${scaled > 0 && scaled < .01 ? "<0.01" : new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(scaled)} ${gib ? "GiB" : "MiB"}`;
  }
  return `${String(value)} ${unit ?? "· unit not specified"}`;
}

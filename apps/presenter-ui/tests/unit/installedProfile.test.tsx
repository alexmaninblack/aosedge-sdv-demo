// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import { ComponentDetails, ServiceCompatibility } from "../../src/app/StudioReadViews";
import { confirmedInstalledProfile, installedCompatibility } from "../../src/domain/installedCompatibility";
import type { CloudComponent } from "../../src/domain/platformObservation";

afterEach(cleanup);
const row = (): CloudComponent => ({ type: "demo-vehicle-data-provider", reported_component_id: "component",
  installed_component: { id: "installed", version: "79.0.0" }, pending_component: { version: "80.0.0" },
  pending_component_status: "pending", runtimeState: "NOT_REPORTED_BY_CLOUD",
  installedProfile: { state: "CURRENT", profile: "v3", releaseVersion: "79.0.0", cloudVersionId: "installed", source: "CLOUD_INSTALLATION_AND_PACKAGE", reason: null } });

test("component dialog uses confirmed installed profile, not pending release", () => {
  render(<ComponentDetails row={row()} current />);
  expect(screen.getByText("V3")).toBeInTheDocument();
  expect(screen.getByText("Pending 80.0.0")).toBeInTheDocument();
});

test.each(["missing", "unknown", "wrong-release", "wrong-uuid"])("profile stays unconfirmed for %s evidence", kind => {
  const value = row();
  if (kind === "missing") delete value.installedProfile;
  if (kind === "unknown") value.installedProfile!.state = "UNKNOWN";
  if (kind === "wrong-release") value.installedProfile!.releaseVersion = "80.0.0";
  if (kind === "wrong-uuid") value.installedProfile!.cloudVersionId = "different-artifact";
  render(<ComponentDetails row={value} current />);
  expect(screen.getByText("Not confirmed")).toBeInTheDocument();
  expect(screen.queryByText("V3")).not.toBeInTheDocument();
});

test.each([
  ["brake", "v1", "v1", true], ["brake", "v1", "v2", true], ["brake", "v1", "v3", true],
  ["brake", "v2", "v1", false], ["brake", "v2", "v2", true], ["brake", "v2", "v3", true],
  ["brake", "v3", "v1", false], ["brake", "v3", "v2", false], ["brake", "v3", "v3", true],
  ["tire", "v1", "v1", false], ["tire", "v1", "v2", false], ["tire", "v1", "v3", true],
] as const)("Cloud software matrix: %s %s with VDP %s", (team, serviceProfile, profile, compatible) => {
  const evidence = { ...row().installedProfile!, profile };
  expect(installedCompatibility(evidence, team, serviceProfile, true)).toMatchObject({ state: "CURRENT", compatible });
});

test("software compatibility cannot come from unknown, missing or invented service profiles", () => {
  expect(installedCompatibility({ ...row().installedProfile!, state: "UNKNOWN" }, "brake", "v3", true).state).toBe("UNKNOWN");
  expect(installedCompatibility(null, "brake", "v3", true).compatible).toBeNull();
  expect(installedCompatibility(row().installedProfile!, "tire", "v3", true).state).toBe("UNKNOWN");
  expect(installedCompatibility(row().installedProfile!, undefined, "v1", true).state).toBe("UNKNOWN");
  expect(confirmedInstalledProfile({ ...row().installedProfile!, cloudVersionId: null }, "79.0.0")).toBeNull();
});

test("stale software evidence never becomes current compatibility or input readiness", () => {
  expect(installedCompatibility(row().installedProfile!, "brake", "v3", false).state).toBe("STALE");
  render(<ServiceCompatibility evidence={{ ...row().installedProfile!, state: "STALE" }} team="tire" profile="v1" current />);
  expect(screen.getByText("Compatible · VDP V3 · last known")).toBeInTheDocument();
  expect(screen.getByText(/Input, assessments and advisory are observed separately/)).toBeInTheDocument();
  expect(screen.queryByText("Ready")).not.toBeInTheDocument();
});

test("retained profile is labelled last known", () => {
  const value = row(); value.installedProfile!.state = "STALE";
  render(<ComponentDetails row={value} current />);
  expect(screen.getByText("V3 · last known")).toBeInTheDocument();
});

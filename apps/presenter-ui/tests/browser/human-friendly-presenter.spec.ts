// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { expect, test, type Page } from "@playwright/test";

async function scenario(page: Page) {
  const state = { power: "RUNNING", source: "CONNECTED", uncertain: false, empty: false };
  const mutations: any[] = [], jobs: any[] = [];
  await page.route("**/api/**", async route => {
    const path = new URL(route.request().url()).pathname, time = new Date().toISOString();
    if (path.endsWith("/operations")) {
      if (route.request().method() === "GET") return route.fulfill({ json: { sessionId: "branch-fixture", cloudDomain: "stage.example", active: null, uncertain: state.uncertain, jobs } });
      const body = route.request().postDataJSON(); mutations.push(body);
      if (body.action === "stop-demo") { state.power = "STOPPED"; state.source = "STOPPED"; }
      if (body.action === "start-demo") state.power = "RUNNING";
      if (body.action === "start-simulation") state.source = "RUNNING_UNASSIGNED";
      if (body.action === "connect-test") state.source = "CONNECTED";
      const job = { id: body.requestId, action: body.action, runId: "same-test", state: "COMPLETED", startedAt: time, finishedAt: time,
        results: [{ operation: body.action, state: "COMPLETED", message: "Fixture owner receipt", facts: body.action === "cloud-inspect" ? { domain: "stage.example" } : {} }], progress: [] };
      jobs.push(job); return route.fulfill({ status: 202, json: job });
    }
    if (path.endsWith("/snapshot")) return route.fulfill({ json: { mode: "LOCAL_READ_ONLY", runId: state.empty ? null : "same-test", observedAt: time, registrationComplete: !state.empty,
      images: [{ selector: "41/arm64", version: "Factory .41", state: "METADATA_AVAILABLE", problems: [] }],
      access: { "oem-delivery": { present: true, state: "NOT_REQUESTED" }, "service-provider": { present: true, state: "NOT_REQUESTED" } },
      vehicles: { test: { state: state.empty ? "NOT_APPLICABLE" : "CURRENT", reason: state.empty ? "TARGET_NOT_CONFIGURED" : null,
        process: state.power, overlayExists: !state.empty, imageVersion: state.empty ? null : "Factory .41" }, production: { state: "NOT_APPLICABLE" } },
      source: { state: state.empty ? "NOT_PREPARED" : state.source, selectedVehicle: state.source === "CONNECTED" && !state.empty ? "test" : null,
        currentVehicle: state.source === "CONNECTED" && !state.empty ? "test" : null } } });
    if (path.endsWith("/platform")) return route.fulfill({ json: state.empty ? { state: "UNAVAILABLE", value: null, observedAt: time } : {
      state: "CURRENT", observedAt: time, bindingKey: "same-test:same-unit", value: { source: "Aos Cloud", target: "test", lifecycle: "provisioned", online: state.power === "RUNNING" ? "ONLINE" : "OFFLINE",
        installedVersion: "80.0.0", installedProfile: { state: "CURRENT", profile: "v3", releaseVersion: "80.0.0", cloudVersionId: "same-vdp", source: "CLOUD_INSTALLATION_AND_PACKAGE" },
        pendingVersion: null, updateStatus: "installed", latestPublishedVersion: null, runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD",
        releases: [], inventory: { unitId: "same-unit", systemUid: "same-controller", components: { state: "CURRENT", value: [{ type: "demo-vehicle-data-provider", installed_component: { version: "80.0.0", id: "same-vdp" } }] },
          services: { state: "CURRENT", value: [] } } } } });
    if (path.endsWith("/client-state")) return route.fulfill({ json: { buildId: "branch-test", canReload: true } });
    return route.abort();
  });
  return { state, mutations };
}

for (const viewport of [{ width: 1280, height: 720 }, { width: 1118, height: 1124 }]) test(`one visible controls entry and distinct Stop/Delete, ${viewport.width}x${viewport.height}`, async ({ page }) => {
  const fixture = await scenario(page); await page.setViewportSize(viewport); await page.goto("/#native-browser");
  await expect(page.getByRole("button", { name: "Demo controls", exact: true })).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Demo controls", exact: true })).toBeInViewport();
  await expect(page.getByRole("button", { name: "Session", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Demo controls", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Demo controls", exact: true });
  await expect(dialog.getByRole("button", { name: "Stop demo and keep data", exact: true })).toBeEnabled();
  await expect(dialog.getByRole("button", { name: "Delete Test & start over", exact: true })).toHaveCount(0);
  await dialog.getByText("Delete this Test", { exact: true }).click();
  await dialog.getByRole("button", { name: "Delete Test & start over", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("Permanently delete");
  await expect(page.getByRole("dialog")).toContainText("There is no undo");
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  expect(fixture.mutations).toEqual([]);
  await page.getByRole("button", { name: "Demo controls", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Demo controls", exact: true })).toBeInViewport();
  await page.screenshot({ path: `test-results/branch-controls-${viewport.width}.png` });
});

test("stop and restart keep identity/software, without Create, provisioning, publication or automatic driving", async ({ page }) => {
  const fixture = await scenario(page); await page.goto("/#native-browser");
  await page.getByRole("button", { name: "Demo controls", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Stop demo and keep data", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("Keep its Cloud identity, disk, models and history");
  await expect(page.getByRole("dialog")).toContainText("Docker Engine and Production stay unchanged");
  await page.getByRole("button", { name: "Cancel", exact: true }).click(); expect(fixture.mutations).toEqual([]);
  await page.getByRole("button", { name: "Demo controls", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Stop demo and keep data", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Stop demo and keep data", exact: true }).click();
  await expect(page.getByRole("button", { name: "Start controller", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Vehicle Data Platform installed details" })).toContainText("v3 · 80.0.0");
  await page.getByRole("button", { name: "Start controller", exact: true }).click();
  await expect(page.getByRole("button", { name: "Start simulator", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Start simulator", exact: true }).click();
  await expect(page.getByRole("button", { name: "Connect in Manual", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Connect in Manual", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Connect in Manual", exact: true }).click();
  await expect(page.locator(".studio-guide")).toContainText("Next software profile");
  expect(fixture.mutations.map(row => row.action)).toEqual(["stop-demo", "start-demo", "start-simulation", "connect-test"]);
  expect(fixture.mutations.every(row => row.sessionId === "branch-fixture" && !row.target && !row.force)).toBe(true);
  await expect(page.getByRole("button", { name: "Vehicle Data Platform installed details" })).toContainText("v3 · 80.0.0");
});

test("unknown result prevents both stop and deletion while keeping Activity available", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.uncertain = true; await page.goto("/#native-browser");
  await page.getByRole("button", { name: "Demo controls", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("button", { name: "Stop demo and keep data", exact: true })).toBeDisabled();
  await page.getByText("Delete this Test", { exact: true }).click();
  await expect(page.getByRole("button", { name: "Delete Test & start over", exact: true })).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: /Activity/ })).toBeEnabled(); expect(fixture.mutations).toEqual([]);
});

test("quick preparation is an explicit pre-Create choice, with a publication confirmation", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.empty = true; await page.goto("/#native-browser");
  await expect(page.getByRole("button", { name: "Create controller", exact: true })).toBeVisible();
  await expect(page.getByRole("combobox", { name: "Preparation", exact: true })).toHaveCount(0);
  await page.getByText("Advanced preparation", { exact: true }).click();
  await page.getByRole("combobox", { name: "Preparation", exact: true }).selectOption("quick");
  await page.getByRole("button", { name: "Prepare demo", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("publish VDP V1");
  await page.getByRole("button", { name: "Cancel", exact: true }).click(); expect(fixture.mutations).toEqual([]);
});

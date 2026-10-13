// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { expect, test } from "@playwright/test";

for (const team of ["platform", "brake"] as const) {
  test(`${team}: unavailable read cannot replace selected v2 with v1`, async ({ page }) => {
    let unavailable = false;
    const mutations: any[] = [], jobs: any[] = [];
    await page.route("**/api/**", async route => {
      const path = new URL(route.request().url()).pathname;
      if (path.endsWith("/snapshot")) {
        if (unavailable) return route.fulfill({ status: 503, json: {} });
        return route.fulfill({ json: {
          mode: "LOCAL_READ_ONLY", observedAt: new Date().toISOString(), runId: "current-test", registrationComplete: true,
          images: [], access: {}, candidates: [],
          vehicles: { test: { state: "CURRENT", process: "RUNNING", overlayExists: true }, production: { state: "NOT_APPLICABLE" } },
          source: { state: "CONNECTED", selectedVehicle: "test", currentVehicle: "test" },
        } });
      }
      if (path.endsWith("/operations")) {
        if (route.request().method() === "GET") return route.fulfill({ json: {
          sessionId: "fixture-session", uncertain: false, active: null, jobs,
        } });
        const body = route.request().postDataJSON(); mutations.push(body);
        const job = { ...body, id: body.requestId, runId: "current-test", state: "COMPLETED", progress: [], results: [], version: "151.0.0" };
        jobs.push(job); return route.fulfill({ status: 202, json: job });
      }
      if (path.endsWith("/platform")) return route.fulfill({ json: {
        state: "CURRENT", observedAt: new Date().toISOString(), bindingKey: "current-test:unit", publications: [],
        value: { target: "test", source: "Aos Cloud", online: "ONLINE", lifecycle: "provisioned", installedVersion: "150.0.0",
          releases: [], runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD",
          installedProfile: { state: "CURRENT", profile: "v1", releaseVersion: "150.0.0", cloudVersionId: "vdp-150", source: "CLOUD_INSTALLATION_AND_PACKAGE" },
          inventory: { unitId: "unit", systemUid: "system", components: { state: "CURRENT", value: [] }, services: { state: "CURRENT", value: [] } },
        },
      } });
      return route.abort();
    });
    await page.goto("/");
    await page.getByRole("button", { name: team === "platform" ? "Platform Team" : "Brake Team", exact: true }).click();
    const selected = page.getByRole("button", { name: team === "platform" ? "v2 Brake analysis" : "v2 Condition assessment", exact: true });
    await selected.click();
    unavailable = true;
    await page.getByRole("button", { name: "Refresh Cloud state", exact: true }).click();
    await expect(page.locator(".studio-guide")).toContainText("Controller state unavailable");
    await expect(selected).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByRole("button", { name: "Prepare v2", exact: true })).toBeDisabled();
    expect(mutations).toHaveLength(0);
    unavailable = false;
    await page.getByRole("button", { name: "Refresh state", exact: true }).click();
    await expect(page.getByRole("button", { name: "Prepare v2", exact: true })).toBeEnabled();
    await expect(selected).toHaveAttribute("aria-pressed", "true");
    await page.getByRole("button", { name: "Prepare v2", exact: true }).click();
    await expect.poll(() => mutations.length).toBe(1);
    expect(mutations[0]).toMatchObject(team === "platform" ? { action: "prepare", profile: "v2" }
      : { action: "service-prepare", team: "brake", profile: "v2" });
    expect(jobs).toHaveLength(1);
  });
}

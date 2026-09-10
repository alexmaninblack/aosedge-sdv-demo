import { expect, test } from "@playwright/test";

test("Cloud entry/reentry and a failed refresh retain visibly last-known inventory, with no guest request", async ({ page }) => {
  let fail = false;
  let cloudReads = 0;
  const unexpected: string[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/presenter/platform") {
      cloudReads += 1;
      return route.fulfill({ json: fail ? { state: "UNAVAILABLE", observedAt: null, reason: "AOS_CLOUD_STATE_UNAVAILABLE", value: null } : {
        state: "CURRENT", observedAt: new Date().toISOString(), reason: null, value: {
          target: "test", source: "Aos Cloud", online: "Online", lifecycle: "provisioned", installedVersion: "18.0.0",
          pendingVersion: null, updateStatus: "installed", latestPublishedVersion: "18.0.0", releases: [],
          runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD" } } });
    }
    if (path === "/api/presenter/snapshot") return route.fulfill({ json: {
      mode: "LOCAL_READ_ONLY", available: true, observedAt: new Date().toISOString(), images: [], access: {},
      vehicles: { test: { state: "CURRENT", process: "RUNNING", imageVersion: "31", overlayExists: true },
        production: { state: "CURRENT", process: "NOT_CREATED", imageVersion: null, overlayExists: false } },
      source: { state: "SELECTED_NOT_PROBED", selectedVehicle: "test", currentVehicle: null } } });
    // No native command capability is granted to this browser fixture.
    if (path === "/api/presenter/operations" && route.request().method() === "GET") return route.fulfill({ status: 401, json: {} });
    unexpected.push(path); return route.abort();
  });
  await page.goto("/");
  await page.getByRole("button", { name: /Platform Team/ }).click();
  await expect(page.getByText("VDP 18.0.0 · Cloud installed", { exact: true })).toBeVisible();
  expect(cloudReads).toBe(1);
  fail = true;
  await page.getByRole("button", { name: "Refresh Cloud state" }).click();
  await expect(page.getByText("VDP 18.0.0 · Cloud installed · last known", { exact: true })).toBeVisible();
  await expect(page.getByText("Previous observation — not current.", { exact: true })).toBeVisible();
  await expect(page.locator(".platform-cloud-facts")).toContainText("Online");
  await page.getByRole("button", { name: /Brake Team/ }).click();
  fail = false;
  await page.getByRole("button", { name: /Platform Team/ }).click();
  await expect(page.getByText("VDP 18.0.0 · Cloud installed", { exact: true })).toBeVisible();
  expect(cloudReads).toBe(3);
  expect(unexpected).toEqual([]);
});

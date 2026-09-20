import { expect, test, type Page } from "@playwright/test";

const ids = { brake: "11111111-1111-4111-8111-111111111111", tire: "22222222-2222-4222-8222-222222222222" };
async function serviceScenario(page: Page) {
  const jobs: Record<string, unknown>[] = [], releases: Record<string, any>[] = [], assignments = new Set<string>();
  const mutations: Record<string, any>[] = [];
  let counter = 11;
  const now = () => new Date().toISOString();
  await page.route("**/api/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/operations")) {
      if (route.request().method() === "GET") return route.fulfill({ json: { sessionId: "fixture-session", uncertain: false, active: null, jobs } });
      const body = route.request().postDataJSON(); mutations.push(body);
      let release = releases.find(row => row.releaseHandle === body.release);
      if (body.action === "service-prepare") {
        const version = `${++counter}.0.0`;
        release = { team: body.team, contentProfile: body.profile, version, releaseHandle: `${body.team}/${version}`, runId: "current-run", serviceId: ids[body.team as keyof typeof ids], signed: false, submitted: false, demoMockedData: true, preparedAt: now(), publication: {} };
        releases.push(release);
      }
      if (body.action === "service-publish" && release) Object.assign(release, { signed: true, submitted: true, publication: { stage: "READY", observedAt: now() } });
      if (body.action === "service-assign") assignments.add(body.serviceId);
      const job = { id: body.requestId, action: body.action, team: body.team ?? release?.team, profile: body.profile ?? release?.contentProfile,
        release: release?.releaseHandle, version: release?.version, serviceId: body.serviceId ?? release?.serviceId, runId: "current-run", state: "COMPLETED", progress: [], results: [{ state: "COMPLETED", operation: body.action, message: "Fixture receipt", facts: {} }], finishedAt: now() };
      jobs.push(job); return route.fulfill({ status: 202, json: job });
    }
    if (path.endsWith("/snapshot")) return route.fulfill({ json: {
      mode: "LOCAL_READ_ONLY", available: true, observedAt: now(), runId: "current-run", registrationComplete: true, serviceReleases: releases,
      candidates: [{ version: "23.0.0", contentProfile: "v3", submitted: true }], access: {},
      images: [{ version: "Factory .33", selector: "33/arm64", architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] }],
      vehicles: { test: { state: "CURRENT", process: "RUNNING", overlayExists: true, imageVersion: "Factory .33" }, production: { state: "CURRENT", process: "STOPPED", overlayExists: true, imageVersion: "Factory .31" } },
      source: { state: "CONNECTED", selectedVehicle: "test", currentVehicle: "test" },
    } });
    if (path.endsWith("/platform")) return route.fulfill({ json: {
      state: "CURRENT", bindingKey: "current-run:unit-id", observedAt: now(), serviceReleases: releases,
      value: { target: "test", source: "Aos Cloud", online: "ONLINE", lifecycle: "provisioned", installedVersion: "23.0.0", pendingVersion: null,
        installedProfile: { state: "CURRENT", profile: "v3", releaseVersion: "23.0.0", cloudVersionId: "vdp-23", source: "CLOUD_INSTALLATION_AND_PACKAGE", reason: null },
        updateStatus: "installed", releases: [], latestPublishedVersion: null, runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD",
        inventory: { unitId: "unit-id", systemUid: "test-system", teamServiceIds: ids, components: { state: "CURRENT", value: [] }, services: { state: "CURRENT", value: [...assignments].map(id => {
          const latest = releases.filter(row => row.serviceId === id && row.submitted).at(-1)!;
          return { service: { id, title: `${latest.team} Health` }, service_versions: { installed_service_version: { version: latest.version }, pending_service_version: null }, instances: { state: "CURRENT", value: [{ instance_id: 0, run_state: "active", version: latest.version }] } };
        }) } } },
    } });
    return route.abort();
  });
  return { mutations, assignments };
}

async function confirm(page: Page, action: string) {
  await page.getByRole("dialog").getByRole("button", { name: action, exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
}

test("service UI: prepare, cancel, publish, first Deploy, higher release without Deploy; peer preserved", async ({ page }) => {
  const state = await serviceScenario(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Brake Team", exact: true }).click();
  await page.getByRole("button", { name: "Prepare v1", exact: true }).click();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  expect(state.mutations).toEqual([]);
  await page.getByRole("button", { name: "Prepare v1", exact: true }).click();
  await confirm(page, "Prepare service");
  await expect(page.getByText("Selected candidate · v1 · 12.0.0")).toBeVisible();
  await page.getByRole("button", { name: "Sign & publish", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("configured Service Provider");
  await confirm(page, "Sign & publish service");
  await expect(page.getByRole("button", { name: "Deploy to Test" })).toBeEnabled();
  await page.getByRole("button", { name: "Deploy to Test" }).click();
  await expect(page.getByRole("dialog")).toContainText("No version or instance count is sent");
  await confirm(page, "Deploy service to Test");
  await expect(page.getByRole("button", { name: "Deploy to Test" })).toHaveCount(0);
  await expect(page.getByText("Installed 12.0.0", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Tire Team", exact: true }).click();
  await page.getByRole("button", { name: "Prepare v1", exact: true }).click();
  await confirm(page, "Prepare service");
  await expect(page.getByText("Selected candidate · v1 · 13.0.0")).toBeVisible();
  await page.getByRole("button", { name: "Sign & publish", exact: true }).click();
  await confirm(page, "Sign & publish service");
  await page.getByRole("button", { name: "Deploy to Test" }).click();
  await confirm(page, "Deploy service to Test");
  await expect(page.getByText("Installed 13.0.0", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Brake Team", exact: true }).click();
  await page.getByRole("button", { name: "v2 Condition assessment" }).click();
  await page.getByRole("button", { name: "Prepare v2", exact: true }).click();
  await confirm(page, "Prepare service");
  await expect(page.getByText("Selected candidate · v2 · 14.0.0")).toBeVisible();
  await page.getByRole("button", { name: "Sign & publish", exact: true }).click();
  await confirm(page, "Sign & publish service");
  await expect(page.getByText("Installed 14.0.0", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Deploy to Test" })).toHaveCount(0);
  expect([...state.assignments]).toEqual([ids.brake, ids.tire]);
  expect(state.mutations.filter(row => row.action === "service-assign")).toHaveLength(2);
  expect(state.mutations.every(row => !row.target && !row.numInstances && !row.serviceVersion)).toBe(true);
  await page.reload();
  await page.getByRole("button", { name: "Brake Team", exact: true }).click();
  await page.getByRole("button", { name: "v2 Condition assessment" }).click();
  await expect(page.getByText("Selected candidate · v2 · 14.0.0")).toBeVisible();
  await expect(page.locator(".studio-release-stages .complete")).toHaveCount(3);
});

for (const viewport of [{ width: 1280, height: 720 }, { width: 1512, height: 982 }, { width: 1118, height: 1124 }]) {
  test(`Studio fixed viewport ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport); await serviceScenario(page);
    await page.goto(viewport.width === 1118 ? "/#native-browser" : "/");
    await expect(page.locator(".studio-controller")).toBeVisible();
    for (const name of ["Vehicle", "Platform Team", "Brake Team", "Tire Team"]) {
      await page.getByRole("button", { name, exact: true }).click();
      const fits = await page.locator(".studio-body").evaluate(node => ({ width: node.scrollWidth <= node.clientWidth + 1, height: node.scrollHeight <= node.clientHeight + 1 }));
      if (!fits.height || !fits.width) await page.screenshot({ path: `test-results/studio-overflow-${viewport.width}.png` });
      expect(fits, name).toEqual({ width: true, height: true });
    }
    await page.screenshot({ path: `test-results/studio-${viewport.width}.png` });
  });
}

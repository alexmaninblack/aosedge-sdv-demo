import { expect, test, type Page } from "@playwright/test";

async function retainedRun(page: Page, retiring = false, online = "ONLINE",
  phase = "deprovision-test", reason = "UNIT_WAIT_TIMEOUT:CLOUD_OFFLINE", registrationStarted = false,
  options: { confirmedProfile?: boolean; registrationComplete?: boolean } = {}) {
  const { confirmedProfile = true, registrationComplete = false } = options;
  const requests: { path: string; method: string }[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    requests.push({ path, method: route.request().method() });
    if (path.endsWith("/snapshot")) return route.fulfill({ json: {
      mode: "LOCAL_READ_ONLY", runId: "current-test", available: true, observedAt: new Date().toISOString(),
      registrationComplete,
      registrationStarted,
      lifecycle: retiring ? { action: "retire", state: "PARTIAL", phase, reason } : undefined,
      preparation: { image: "32/arm64", phase: "PROVISIONING" },
      candidates: [{ version: "19.0.0", contentProfile: "v1", signed: true, submitted: true },
        { version: "20.0.0", contentProfile: "v2", signed: true, submitted: true }],
      images: [31, 32].map((n) => ({ selector: `${n}/arm64`, version: `Factory .${n}`, architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] })), access: {},
      vehicles: { test: { state: "CURRENT", process: "RUNNING", imageVersion: "Factory .32", overlayExists: true },
        production: { state: "CURRENT", process: "NOT_CREATED", overlayExists: false } },
      source: retiring ? { state: "STOPPED", currentVehicle: null } : { state: "SELECTED_NOT_PROBED", selectedVehicle: "test", currentVehicle: registrationComplete ? "test" : null },
    } });
    if (path.endsWith("/platform")) return route.fulfill({ json: {
      state: "CURRENT", observedAt: new Date().toISOString(), bindingKey: "current-test:unit-a", reason: null,
      publication: { version: "20.0.0", stage: "READY" },
      publications: [{ version: "19.0.0", stage: "READY" }, { version: "20.0.0", stage: "READY" }],
      value: { target: "test", source: "Aos Cloud", online, lifecycle: "provisioned", installedVersion: "20.0.0", pendingVersion: null,
        installedProfile: { state: confirmedProfile ? "CURRENT" : "UNKNOWN", profile: confirmedProfile ? "v2" : null, releaseVersion: "20.0.0", cloudVersionId: "vdp-20", source: "CLOUD_INSTALLATION_AND_PACKAGE", reason: confirmedProfile ? null : "INSTALLED_PROFILE_PUBLICATION_NOT_CONFIRMED" },
        updateStatus: "installed", latestPublishedVersion: null, releases: [], runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD",
        inventory: { unitId: "unit-a", systemUid: "test-system", nodes: { state: "CURRENT", value: [{ node_id: "controller" }] }, components: { state: "CURRENT", value: [] }, services: { state: "CURRENT", value: [] } } },
    } });
    if (path.endsWith("/operations")) return route.fulfill({ json: { sessionId: "native", active: null, uncertain: false,
      jobs: [{ id: "old", runId: "old-test", action: "prepare", version: "99.0.0", profile: "v1", state: "COMPLETED", progress: [], results: [] }] } });
    if (path.endsWith("/monitoring")) return route.fulfill({ json: { unitId: "unit-a", readCompletedAt: new Date().toISOString(),
      monitoring: { state: "CURRENT", value: { cpu: { state: "CURRENT", unit: "DMIPS", value: [{ nodeId: "controller", value: 0, time: new Date().toISOString() }] } } } } });
    if (path === "/api/presenter/backend/brake" || path === "/api/presenter/backend/tire") return route.fulfill({ json: {
      team:path.split("/").at(-1),state:"OBSERVED",source:"REAL_BACKEND_HTTP",observedAt:new Date().toISOString(),
      observations:{readiness:{state:"OBSERVED",data:{ready:true}},mockData:{state:"OBSERVED",data:{source:"DEMO_MOCK",vehicleTelemetry:false,
        unitSystemUid:"test-system",counts:[{kind:"assessment",count:3}],records:[{backendReceivedAt:new Date().toISOString(),message:{
          messageType:"Synthetic assessment",serviceVersion:"7.0.0",unitSystemUid:"test-system",content:{score:42}}}]}}}} });
    return route.abort();
  });
  return requests;
}

for (const online of ["ONLINE", "OFFLINE"]) test(`partial retirement ${online} never offers startup or publication`, async ({ page }) => {
  const requests = await retainedRun(page, true, online);
  await page.goto("/");
  await expect(page.getByText("Retirement paused", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start simulator", exact: true })).toHaveCount(0);
  if (online === "OFFLINE") await expect(page.getByRole("button", { name: "Continue Finish", exact: true })).toBeEnabled();
  else await expect(page.getByRole("button", { name: "Continue Finish", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: /Platform Team/ }).click();
  await expect(page.getByRole("button", { name: "Prepare v1", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: /Brake Team/ }).click();
  await expect(page.getByRole("button", { name: "Prepare v1", exact: true })).toBeDisabled();
  expect(requests.every(row => row.method === "GET")).toBe(true);
});

for (const [phase, reason, online] of [
  ["stop-simulation", "SOURCE_STOP_UNCONFIRMED", "ONLINE"],
  ["deprovision-test", "RETIRED_VM_STOP_NOT_CONFIRMED", "ONLINE"],
  ["retire-test-data-and-overlay", "BACKEND_CONTEXT_UNLINK_UNCONFIRMED", "UNKNOWN"],
]) test(`Finish can continue ${phase} without an unrelated Offline requirement`, async ({ page }) => {
  const requests = await retainedRun(page, true, online, phase, reason);
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Continue Finish", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Start simulator", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Continue Finish", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(requests.every(row => row.method === "GET")).toBe(true);
});

for (const [action, state] of [["park", "COMPLETED"], ["park", "PARTIAL"], ["resume", "PARTIAL"], ["resume", "COMPLETED"]])
test(`stopped historical ${action}/${state} offers only confirmed Finish, not restart`, async ({ page }) => {
  const requests = await retainedRun(page);
  await page.route("**/api/presenter/snapshot", route => route.fulfill({ json: {
    mode: "LOCAL_READ_ONLY", runId: "current-test", observedAt: new Date().toISOString(),
    lifecycle: { action, state }, registrationComplete: true, images: [], access: {},
    vehicles: { test: { state: "CURRENT", process: "STOPPED", overlayExists: true },
      production: { state: "CURRENT", process: "STOPPED", overlayExists: true } },
    source: { state: "STOPPED", currentVehicle: null },
  } }));
  await page.goto("/");
  await expect(page.getByText("Demo interrupted", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /^(Park|Resume|Continue Resume|Start simulator|Connect in Manual)$/ })).toHaveCount(0);
  await page.getByRole("button", { name: "Finish demo", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Brake Team", exact: true }).click();
  await expect(page.getByRole("button", { name: "Prepare v1", exact: true })).toBeDisabled();
  expect(requests.every(row => row.method === "GET")).toBe(true);
});

for (const sourceState of ["STOPPED", "NOT_PREPARED", "UNKNOWN"]) test(`new controller with ${sourceState} source does not confuse old layout evidence with current windows`, async ({ page }) => {
  const requests = await retainedRun(page);
  await page.route("**/api/presenter/operations", route => route.fulfill({ json: {
    sessionId: "native", active: null, uncertain: false, jobs: [],
    workspace: { state: "INCOMPLETE", zOrder: { state: "UNAVAILABLE" } },
  } }));
  await page.route("**/api/presenter/snapshot", route => route.fulfill({ json: {
    mode: "LOCAL_READ_ONLY", runId: "new-test", observedAt: new Date().toISOString(),
    registrationStarted: false, registrationComplete: false,
    lifecycle: { action: "create", state: "COMPLETED" }, images: [], access: {},
    vehicles: { test: { state: "CURRENT", process: "RUNNING", overlayExists: true },
      production: { state: "CURRENT", process: "STOPPED", overlayExists: true } },
    source: { state: sourceState, currentVehicle: null },
  } }));
  await page.goto("/");
  if (sourceState === "UNKNOWN") await expect(page.getByLabel("Desktop window layout")).toBeVisible();
  else {
    await expect(page.getByRole("button", { name: "Start simulator", exact: true })).toBeVisible();
    await expect(page.getByLabel("Desktop window layout")).toHaveCount(0);
  }
  expect(requests.every(row => row.method === "GET")).toBe(true);
});

test("external CLI retirement returns the open Studio to Create without reloading or submitting actions", async ({ page }) => {
  const requests = await retainedRun(page, true);
  await page.route("**/api/presenter/operations", route => route.fulfill({ json: {
    sessionId: "native", active: null, uncertain: false, jobs: [],
    workspace: { state: "INCOMPLETE", zOrder: { state: "UNAVAILABLE" } },
  } }));
  let retired = false, snapshotReads = 0;
  await page.route("**/api/presenter/snapshot", route => {
    snapshotReads++;
    requests.push({ path: "/api/presenter/snapshot", method: route.request().method() });
    return route.fulfill({ json: {
      mode: "LOCAL_READ_ONLY", runId: retired ? undefined : "current-test", observedAt: new Date().toISOString(),
      images: [{ selector: "33/arm64", version: "Factory .33", architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] }], access: {},
      lifecycle: retired ? undefined : { action: "retire", state: "PARTIAL", phase: "deprovision-test" },
      vehicles: { test: { state: "CURRENT", process: "STOPPED", overlayExists: !retired, imageVersion: "Factory .33" },
        production: { state: "CURRENT", process: "STOPPED", overlayExists: true, imageVersion: "Factory .31" } },
      source: { state: "STOPPED", currentVehicle: null },
    } });
  });
  await page.clock.install();
  await page.goto("/");
  await expect(page.getByText("Retirement paused", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Desktop window layout")).toBeVisible();
  // Cloud still returns the previous Unit. Only a fresh local receipt can
  // establish that CLI cleanup completed; no page reload or timed success.
  retired = true;
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByRole("button", { name: "Create controller", exact: true })).toBeEnabled();
  await expect(page.getByText("Retirement paused", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Factory image")).toBeEnabled();
  await expect(page.getByRole("button", { name: "Vehicle Data Platform Factory slot · no Cloud report" })).toBeVisible();
  await expect(page.getByLabel("Desktop window layout")).toHaveCount(0);
  expect(snapshotReads).toBeGreaterThan(1);
  expect(requests.every(row => row.method === "GET")).toBe(true);
  expect(requests.some(row => /guest|runtime-inspect/.test(row.path))).toBe(false);
});

test("partial SDK registration can continue without a Cloud binding or ready publication", async ({ page }) => {
  const requests = await retainedRun(page, false, "UNKNOWN", "", "", true);
  await page.route("**/api/presenter/platform", route => route.fulfill({ json: {
    state: "UNAVAILABLE", observedAt: new Date().toISOString(), value: null,
    reason: "TEST_CLOUD_BINDING_NOT_OBSERVED", publication: { version: "20.0.0", stage: "PROCESSING" },
  } }));
  await page.goto("/");
  await expect(page.getByText("Test Vehicle · Registration incomplete")).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue registration", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Continue registration", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(requests.every(row => row.method === "GET")).toBe(true);
});

test("Reload retains exact profile publication, ignores previous-run jobs and can finish registration", async ({ page }) => {
  const requests = await retainedRun(page);
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Continue registration" })).toBeEnabled();
  await expect(page.getByLabel("Factory image")).toHaveValue("32/arm64");
  await expect(page.getByLabel("Factory image")).toBeDisabled();
  await page.getByLabel("Preparation", { exact: true }).selectOption("quick");
  await expect(page.getByLabel("Factory image")).toHaveValue("32/arm64");
  await expect(page.getByRole("button", { name: "Continue preparation" })).toBeEnabled();
  await page.getByRole("button", { name: /Platform Team/ }).click();
  await expect(page.getByText("Selected candidate · v1 · 19.0.0")).toBeVisible();
  await expect(page.locator(".studio-release-stages .complete")).toHaveCount(2);
  await page.getByRole("button", { name: "v2 Brake analysis" }).click();
  await expect(page.locator(".studio-release-stages .complete")).toHaveCount(3);
  await page.getByRole("button", { name: "v1 Braking telemetry" }).click();
  await expect(page.locator(".studio-release-stages .complete")).toHaveCount(2);
  expect(requests.every((request) => request.method === "GET")).toBe(true);
});

test("installed profile never falls back to a matching local prepared candidate", async ({ page }) => {
  const requests = await retainedRun(page, false, "ONLINE", "", "", false, { confirmedProfile: false, registrationComplete: true });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Vehicle Data Platform Release · 20.0.0", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Vehicle Data Platform v2 · 20.0.0", exact: true })).toHaveCount(0);
  await expect(page.getByText("Installed profile not confirmed", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open Platform v1", exact: true })).toHaveCount(0);
  expect(requests.every(row => row.method === "GET")).toBe(true);
});

test("Team backend is visibly synthetic, drillable and separate from Cloud runtime", async ({ page }) => {
  const requests=await retainedRun(page);
  await page.goto("/");
  await page.getByRole("button", {name:/Brake backend Open dashboard/}).click();
  await expect(page.getByText("Configured data path · service → backend")).toBeVisible();
  await page.getByRole("button", { name: "Records", exact: true }).click();
  await page.getByRole("button", { name: "Show mock history" }).click();
  await expect(page.getByText("MOCK DATA · Explicit synthetic test records")).toBeVisible();
  await page.getByRole("button", {name:"Records", exact:true}).click();
  await expect(page.getByRole("button", {name:/Synthetic assessment/})).toBeVisible();
  await page.screenshot({path:"test-results/studio-brake-backend.png"});
  await page.getByRole("button", {name:/Synthetic assessment/}).click();
  await expect(page.getByRole("dialog").last()).toContainText("Mock product record");
  await page.getByText("Record content and technical identifiers").click();
  await expect(page.getByRole("dialog").last()).toContainText('"score": 42');
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await page.getByRole("button", {name:/Tire Team/}).click();
  await expect(page.getByRole("heading", {name:"Tire Health Service"})).toBeVisible();
  await page.getByRole("button", {name:/Open Tire backend/}).click();
  await expect(page.getByLabel("tire backend evidence")).toBeVisible();
  expect(requests.every(row=>row.method === "GET")).toBe(true);
  expect(requests.some(row=>/guest|runtime-inspect/.test(row.path))).toBe(false);
});

test("Cloud monitoring has a return path, preserves zero DMIPS and never requests guest data", async ({ page }) => {
  const requests = await retainedRun(page);
  await page.goto("/");
  await page.getByRole("button", { name: /Aos Cloud Unit monitoring/ }).click();
  await expect(page.getByRole("heading", { name: "Cloud monitoring", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Resources", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("figure", { name: "controller CPU · last five minutes" })).toContainText("0 DMIPS");
  await page.keyboard.press("Escape");
  await expect(page.locator(".studio-controller")).toBeVisible();
  expect(requests.every((request) => request.method === "GET" && ["/api/presenter/snapshot", "/api/presenter/platform", "/api/presenter/operations", "/api/presenter/monitoring", "/api/presenter/monitoring-history", "/api/presenter/client-state", "/api/presenter/backend/brake", "/api/presenter/backend/tire"].includes(request.path))).toBe(true);
});

test("Studio uses protected Test actions, automatic releases and actual receipts without page-open mutation", async ({ page }) => {
  const jobs: object[] = [];
  const mutations: Record<string, unknown>[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/presenter/snapshot") return route.fulfill({ json: {
      mode: "LOCAL_READ_ONLY", runId: "current-test", available: true, observedAt: new Date().toISOString(),
      images: [{ selector: "31/arm64", version: "Factory .31", architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] }], access: {},
      vehicles: { test: { state: "CURRENT", process: "RUNNING", imageVersion: "Factory .31", overlayExists: true }, production: { state: "CURRENT", process: "NOT_CREATED", overlayExists: false } },
      source: { state: "SELECTED_NOT_PROBED", selectedVehicle: "test", currentVehicle: null } } });
    if (path === "/api/presenter/platform") return route.fulfill({ json: { state: "CURRENT", observedAt: new Date().toISOString(), reason: null, value: {
      target: "test", source: "Aos Cloud", online: "ONLINE", lifecycle: "provisioned", installedVersion: "18.0.0", pendingVersion: null,
      updateStatus: "installed", latestPublishedVersion: null, releases: [], runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD" } } });
    if (path === "/api/presenter/operations") {
      if (route.request().method() === "GET") return route.fulfill({ json: { sessionId: "test-native", active: null, uncertain: false, jobs } });
      const payload = route.request().postDataJSON(); mutations.push(payload);
      const job = { id: payload.requestId, runId: "current-test", action: payload.action, version: payload.version ?? "19.0.0", profile: "v1", state: "COMPLETED",
        startedAt: new Date().toISOString(), finishedAt: new Date().toISOString(), progress: [], results: [{ operation: `component.${payload.action}`, state: "COMPLETED", message: "fixture receipt", facts: {} }] };
      jobs.push(job); return route.fulfill({ status: 202, json: job });
    }
    return route.abort();
  });
  await page.goto("/");
  await expect(page.getByTestId("studio-workspace")).toBeVisible();
  expect(mutations).toEqual([]);
  await expect(page.getByText("Production · Deferred")).toBeVisible();
  await page.getByRole("button", { name: /Platform Team/ }).click();
  await expect(page.getByRole("button", { name: "Prepare v1" })).toBeEnabled();
  await expect(page.getByRole("textbox")).toHaveCount(0);
  await page.getByRole("button", { name: "Prepare v1" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Prepare VDP", exact: true }).click();
  await expect(page.getByText("Selected candidate · v1 · 19.0.0")).toBeVisible();
  expect(mutations[0]).toMatchObject({ action: "prepare", profile: "v1", sessionId: "test-native" });
  expect(mutations[0]).not.toHaveProperty("version");
  expect(mutations[0]).not.toHaveProperty("target");
  await page.getByRole("button", { name: "Sign & publish", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("no batch-approval step is required");
  await page.getByRole("dialog").getByRole("button", { name: "Sign & publish VDP" }).click();
  await expect(page.getByRole("button", { name: "Sign & publish", exact: true })).toBeDisabled();
  expect(mutations.map((row) => row.action)).toEqual(["prepare", "publish"]);
  await expect(page.getByRole("button", { name: /Approve|Authorize/ })).toHaveCount(0);
  await page.screenshot({ path: "test-results/studio-platform.png" });
  await page.getByRole("button", { name: "AosEdge Software Evolution Demo" }).click();
  await page.screenshot({ path: "test-results/studio-vehicle.png" });
  expect(await page.locator(".studio-controller").evaluate((node) => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
});

import { expect, test, type Page } from "@playwright/test";

async function retainedRun(page: Page) {
  const requests: { path: string; method: string }[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    requests.push({ path, method: route.request().method() });
    if (path.endsWith("/snapshot")) return route.fulfill({ json: {
      mode: "LOCAL_READ_ONLY", runId: "current-test", available: true, observedAt: new Date().toISOString(),
      registrationComplete: false,
      preparation: { image: "32/arm64", phase: "PROVISIONING" },
      candidates: [{ version: "19.0.0", contentProfile: "v1", signed: true, submitted: true },
        { version: "20.0.0", contentProfile: "v2", signed: true, submitted: true }],
      images: [31, 32].map((n) => ({ selector: `${n}/arm64`, version: `Factory .${n}`, architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] })), access: {},
      vehicles: { test: { state: "CURRENT", process: "RUNNING", imageVersion: "Factory .32", overlayExists: true },
        production: { state: "CURRENT", process: "NOT_CREATED", overlayExists: false } },
      source: { state: "SELECTED_NOT_PROBED", selectedVehicle: "test", currentVehicle: null },
    } });
    if (path.endsWith("/platform")) return route.fulfill({ json: {
      state: "CURRENT", observedAt: new Date().toISOString(), bindingKey: "current-test:unit-a", reason: null,
      publication: { version: "20.0.0", stage: "READY" },
      publications: [{ version: "19.0.0", stage: "READY" }, { version: "20.0.0", stage: "READY" }],
      value: { target: "test", source: "Aos Cloud", online: "ONLINE", lifecycle: "provisioned", installedVersion: "20.0.0", pendingVersion: null,
        updateStatus: "installed", latestPublishedVersion: null, releases: [], runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD",
        inventory: { unitId: "unit-a", systemUid: "test-system", components: { state: "CURRENT", value: [] }, services: { state: "CURRENT", value: [] } } },
    } });
    if (path.endsWith("/operations")) return route.fulfill({ json: { sessionId: "native", active: null, uncertain: false,
      jobs: [{ id: "old", runId: "old-test", action: "prepare", version: "99.0.0", profile: "v1", state: "COMPLETED", progress: [], results: [] }] } });
    if (path.endsWith("/monitoring")) return route.fulfill({ json: { unitId: "unit-a", readCompletedAt: new Date().toISOString(),
      monitoring: { state: "CURRENT", value: { cpu: { state: "CURRENT", unit: "DMIPS", value: [{ value: 0, time: new Date().toISOString() }] } } } } });
    if (path === "/api/presenter/backend/brake" || path === "/api/presenter/backend/tire") return route.fulfill({ json: {
      team:path.split("/").at(-1),state:"OBSERVED",source:"REAL_BACKEND_HTTP",observedAt:new Date().toISOString(),
      observations:{readiness:{state:"OBSERVED",data:{ready:true}},mockData:{state:"OBSERVED",data:{source:"DEMO_MOCK",vehicleTelemetry:false,
        unitSystemUid:"test-system",counts:[{kind:"assessment",count:3}],records:[{backendReceivedAt:new Date().toISOString(),message:{
          messageType:"Synthetic assessment",serviceVersion:"7.0.0",unitSystemUid:"test-system",content:{score:42}}}]}}}} });
    return route.abort();
  });
  return requests;
}

test("Reload retains exact profile publication, ignores previous-run jobs and can finish registration", async ({ page }) => {
  const requests = await retainedRun(page);
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Continue registration" })).toBeEnabled();
  await page.getByLabel("Preparation", { exact: true }).selectOption("quick");
  await expect(page.getByLabel("Factory image")).toHaveValue("32/arm64");
  await expect(page.getByRole("button", { name: "Continue preparation" })).toBeEnabled();
  await page.getByRole("button", { name: /Platform Team/ }).click();
  await expect(page.getByText("Selected candidate · v1 · 19.0.0")).toBeVisible();
  await expect(page.locator(".studio-release-stages .complete")).toHaveCount(3);
  await page.getByLabel("Capability profile").selectOption("v2");
  await expect(page.locator(".studio-release-stages .complete")).toHaveCount(4);
  await page.getByLabel("Capability profile").selectOption("v1");
  await expect(page.locator(".studio-release-stages .complete")).toHaveCount(3);
  expect(requests.every((request) => request.method === "GET")).toBe(true);
});

test("Team backend is visibly synthetic, drillable and separate from Cloud runtime", async ({ page }) => {
  const requests=await retainedRun(page);
  await page.goto("/");
  await page.getByRole("button", {name:/Brake Team/}).click();
  await expect(page.getByText("MOCK DATA · Real service → real backend")).toBeVisible();
  await expect(page.getByRole("button", {name:/Synthetic assessment/})).toBeVisible();
  await page.screenshot({path:"test-results/studio-brake-backend.png"});
  await page.getByRole("button", {name:/Synthetic assessment/}).click();
  await expect(page.getByRole("dialog")).toContainText("not vehicle telemetry");
  await expect(page.getByRole("dialog")).toContainText('"score": 42');
  await page.keyboard.press("Escape");
  await page.getByRole("button", {name:/Tire Team/}).click();
  await expect(page.getByLabel("tire backend evidence")).toBeVisible();
  expect(requests.every(row=>row.method === "GET")).toBe(true);
  expect(requests.some(row=>/guest|runtime-inspect/.test(row.path))).toBe(false);
});

test("Cloud monitoring has a return path, preserves zero DMIPS and never requests guest data", async ({ page }) => {
  const requests = await retainedRun(page);
  await page.goto("/");
  await page.getByRole("button", { name: /Aos Cloud.*ONLINE/ }).click();
  await expect(page.getByRole("heading", { name: "Cloud monitoring", exact: true })).toBeVisible();
  await expect(page.locator(".studio-metrics")).toContainText("0 DMIPS");
  await page.getByRole("button", { name: "Vehicle map", exact: true }).click();
  await expect(page.locator(".studio-controller")).toBeVisible();
  expect(requests.every((request) => request.method === "GET" && ["/api/presenter/snapshot", "/api/presenter/platform", "/api/presenter/operations", "/api/presenter/monitoring"].includes(request.path))).toBe(true);
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
  await expect(page.getByRole("option", { name: "Production · Deferred" })).toBeDisabled();
  await page.getByRole("button", { name: /Platform Team/ }).click();
  await expect(page.getByRole("button", { name: "Prepare v1" })).toBeEnabled();
  await expect(page.getByRole("textbox")).toHaveCount(0);
  await page.getByRole("button", { name: "Prepare v1" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Prepare VDP", exact: true }).click();
  await expect(page.getByText("Selected candidate · v1 · 19.0.0")).toBeVisible();
  expect(mutations[0]).toMatchObject({ action: "prepare", profile: "v1", sessionId: "test-native" });
  expect(mutations[0]).not.toHaveProperty("version");
  expect(mutations[0]).not.toHaveProperty("target");
  await page.getByRole("button", { name: "Sign", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Sign VDP" }).click();
  await expect(page.getByRole("button", { name: "Publish to Cloud" })).toBeEnabled();
  await page.getByRole("button", { name: "Publish to Cloud" }).click();
  await expect(page.getByRole("dialog")).toContainText("no batch-approval step is required");
  await page.getByRole("dialog").getByRole("button", { name: "Publish VDP to Aos Cloud" }).click();
  await expect(page.getByRole("button", { name: "Publish to Cloud" })).toBeDisabled();
  expect(mutations.map((row) => row.action)).toEqual(["prepare", "sign", "upload"]);
  await expect(page.getByRole("button", { name: /Approve|Authorize/ })).toHaveCount(0);
  await page.screenshot({ path: "test-results/studio-platform.png" });
  await page.getByRole("button", { name: "AosEdge Software Evolution Demo" }).click();
  await page.screenshot({ path: "test-results/studio-vehicle.png" });
  expect(await page.locator(".studio-controller").evaluate((node) => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
});

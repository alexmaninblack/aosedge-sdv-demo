// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { test, expect, type Page } from "@playwright/test";
import { confirmedReset, binding } from "../unit/backendFixture";

for (const width of [1100, 640]) test(`UIA7 disk and traffic units, scope and compact layout (${width})`, async ({ page }) => {
  await page.setViewportSize({ width, height: 850 });
  const fixture = await scenario(page);
  const now = new Date().toISOString();
  const row = (value: number, partition?: string) => ({ nodeId: "controller", value, partition, time: now });
  const metric = (value: unknown[]) => ({ state: "CURRENT", unit: "bytes", value });
  await page.route("**/api/presenter/monitoring", route => route.fulfill({ json: { unitId: "test-a", readCompletedAt: now,
    monitoring: { state: "CURRENT", value: {
      disk: metric([row(138240, "states"), row(417792, "storages"), row(94048256, "var"), row(621244416, "workdirs"),
        ...["brake", "tire"].flatMap(team => [row(0, "states"), row(102400, "storages")].map(sample => ({ ...sample, serviceId: team + "-id", subjectId: team + "-subject", instance: 0 })))]),
      inTraffic: metric([row(22881064), { ...row(0), serviceId: "brake-id", subjectId: "brake-subject", instance: 0 }]),
      outTraffic: metric([row(1942370), { ...row(0), serviceId: "brake-id", subjectId: "brake-subject", instance: 0 }]),
    } } } }));
  await page.goto("/#native-browser");
  await page.getByRole("button", { name: "Aos Cloud Unit monitoring", exact: true }).click();
  await page.getByRole("button", { name: "Resources", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "Disk", exact: true }).click();
  await expect(dialog.getByText("135 KiB", { exact: true })).toBeVisible();
  await expect(dialog.getByText("592.46 MiB", { exact: true })).toBeVisible();
  await expect(dialog.getByRole("navigation", { name: "Resource pages" })).toHaveCount(0);
  await expect(dialog.locator(".studio-disk-readings article")).toHaveCount(4);
  await expect(dialog).not.toContainText("unit not specified");
  expect(await dialog.evaluate(node => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
  await page.screenshot({ path: `test-results/disk-units-${width}.png` });
  await dialog.getByRole("button", { name: "Service instance", exact: true }).click();
  await expect(dialog.getByText("0 B", { exact: true })).toHaveCount(2);
  await expect(dialog.getByText("100 KiB", { exact: true })).toHaveCount(2);
  await dialog.getByRole("button", { name: "Inbound", exact: true }).click();
  await expect(dialog.getByText("0 B", { exact: true })).toBeVisible();
  await expect(dialog).toContainText("Local/private network traffic is excluded");
  await expect(dialog).toContainText("Received · daily total");
  await dialog.getByRole("button", { name: "Controller", exact: true }).click();
  await expect(dialog.getByText("21.82 MiB", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Outbound", exact: true }).click();
  await expect(dialog.getByText("1.85 MiB", { exact: true })).toBeVisible();
  await expect(dialog).toContainText("Sent · daily total");
  await expect(dialog).not.toContainText("unit not specified");
  await page.screenshot({ path: `test-results/traffic-units-${width}.png` });
  await page.keyboard.press("Escape");
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

for (const attempt of [1, 2, 3]) test(`UIA Reset feedback and details stay independent of hung history (${attempt})`, async ({ page }) => {
  const fixture = await scenario(page);
  let releasePost: () => void = () => {};
  let posts = 0, job: any = null, historyReads = 0;
  await page.route("**/api/presenter/monitoring-history", async route => { historyReads++; await new Promise<void>(() => {}); });
  await page.route("**/api/presenter/operations", async route => {
    if (route.request().method() === "POST") {
      const command = route.request().postDataJSON(); posts++;
      expect(command.action).toBe("backend-reset"); expect(command.team).toBe("brake"); expect(command.sessionId).toBe("dialog");
      await new Promise<void>(resolve => { releasePost = resolve; });
      job = { ...command, id: command.requestId, runId: "dialog-run", cloudDomain: "fixture.test", state: "COMPLETED", startedAt: new Date().toISOString(), progress: [],
        results: [{ facts: { command: { commandId: confirmedReset().commandId } } }] };
      return route.fulfill({ status: 202, json: job });
    }
    return route.fulfill({ json: { sessionId: "dialog", cloudDomain: "fixture.test", active: null, uncertain: false, jobs: job ? [job] : [] } });
  });
  await page.goto("/#native-browser");
  const card = page.locator('[data-anchor="brake-backend"]');
  const reset = page.getByRole("button", { name: "Reset Brake scenario", exact: true });
  await expect(reset).toBeEnabled();
  const started = Date.now(); await reset.press("Enter");
  await expect(card).toContainText("Resetting · submitting"); const feedbackMs = Date.now() - started;
  await expect(reset).toBeDisabled(); await expect(page.getByRole("dialog")).toHaveCount(0); expect(posts).toBe(1);
  const openAt = Date.now(); await page.getByRole("button", { name: "Brake backend Open dashboard", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Brake backend", exact: true })).toBeVisible(); const popupMs = Date.now() - openAt;
  await expect(page.getByRole("dialog")).toContainText("Resetting · submitting");
  releasePost(); fixture.state.reset = true; fixture.state.resetOutcome = "PENDING";
  await page.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("waiting for Gateway CLEAR");
  fixture.state.resetOutcome = "CLEARED";
  const clearAt = Date.now(); await page.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("Gateway confirmed CLEAR"); const clearMs = Date.now() - clearAt;
  await page.keyboard.press("Escape"); await expect(reset).toBeEnabled();
  await expect(page.locator('[data-anchor="tire-backend"]')).toContainText("Inspection recommended");
  // Initial latest read plus the existing post-operation refresh. Hung history
  // stays coalesced; opening details does not create another observer.
  expect(posts).toBe(1); expect(historyReads).toBe(1); expect(fixture.reads("/monitoring")).toBe(2);
  console.log(JSON.stringify({ uiaFixtureTiming: attempt, feedbackMs, popupMs, clearReadToVisibleMs: clearMs }));
  expect(Math.max(feedbackMs, popupMs, clearMs)).toBeLessThan(2000);
});

async function scenario(page: Page) {
  const state = { uid: "test-a", failBrake: false, oldBrake: false, pending: false, reset: false, failResources: false,
    statusOnlyPending: false, cloudCurrent: true, receiptAge: 0, partialEvents: false, productConflict: false, firstServicePending: false,
    profileState: "CURRENT", vdpProfile: "v3", profileId: "vdp-78", functionAge: 0, functionInput: "RECEIVING", functionActivity: "ACTIVE", functionConflict: false, windowMode: false, windowInterrupted: false, noResult: false, resetVersion: "58.0.0", resetOutcome: "CLEARED", resetConnected: true };
  const calls: { path: string; method: string }[] = [];
  const now = new Date().toISOString();
  const windowRecord = { unitSystemUid: state.uid, serviceVersion: "56.0.0", eventId: "4cba2d80-c04a-4d24-9f03-f4a85d56da13",
    serviceInstance: { serviceId: "brake-id", subjectId: "brake-subject", instanceIndex: 0, instanceId: "native-brake-v1" },
    windowStartTimestamp: now, terminalState: "COMPLETE", receivedSampleCount: 150, receivedChunkCount: 3, expectedChunkCount: 3,
    backendReceivedAt: new Date(Date.parse(now) + 1).toISOString(), deliveryState: "DURABLY_RECEIVED" };
  const releases = ["brake", "tire"].map(team => ({ team, contentProfile: team === "brake" ? "v3" : "v1", version: team === "brake" ? "58.0.0" : "34.0.0",
    releaseHandle: `${team}/current`, runId: "dialog-run", serviceId: `${team}-id`, submitted: true, signed: true, demoMockedData: false, publication: { stage: "READY" } }));
  await page.route("**/api/**", route => {
    const path = new URL(route.request().url()).pathname;
    calls.push({ path, method: route.request().method() });
    if (path === `/api/presenter/backend/brake/windows/${windowRecord.eventId}`) return route.fulfill({ json: {
      schemaVersion: 2, contractVersion: "2.0.0", resourceType: "WINDOW_DETAIL", unitRole: "VALIDATION", unitSystemUid: state.uid,
      window: { ...windowRecord, terminalState: state.windowInterrupted ? "INCOMPLETE_SOURCE_GAP" : "COMPLETE" }, samples: Array.from({ length: state.windowInterrupted ? 30 : 150 }, (_, i) => ({ sampleIndex: i,
        sourceTimestamp: new Date(Date.parse(now) + i * 100).toISOString(), phase: i < 50 ? "PRE" : i < 100 ? "ACTIVE" : "POST",
        speedKph: Math.max(0, 50 - Math.max(0, i - 50)), brakePedalPercent: i >= 50 && i < 100 ? 70 : 0,
        longitudinalAccelerationMps2: i >= 50 && i < 100 ? -3 : 0 })) } });
    if (path.endsWith("/operations")) return route.fulfill({ json: { sessionId: "dialog", cloudDomain: "fixture.test", active: null, uncertain: false, jobs: [] } });
    if (path.endsWith("/snapshot")) return route.fulfill({ json: {
      mode: "LOCAL_READ_ONLY", runId: "dialog-run", observedAt: now, registrationComplete: true, access: {}, serviceReleases: releases,
      candidates: [{ version: "78.0.0", contentProfile: "v3", submitted: true }],
      images: [{ selector: "35/arm64", version: "Factory .35", state: "METADATA_AVAILABLE", problems: [] }],
      vehicles: { test: { state: "CURRENT", process: "RUNNING", overlayExists: true, imageVersion: "Factory .35" }, production: { state: "CURRENT", process: "NOT_CREATED", overlayExists: false } },
      source: { state: "CONNECTED", selectedVehicle: "test", currentVehicle: "test" },
    } });
    if (path.endsWith("/platform")) return route.fulfill({ json: {
      state: state.cloudCurrent ? "CURRENT" : "STALE", bindingKey: `dialog-run:${state.uid}`, observedAt: now, serviceReleases: releases,
      value: { target: "test", source: "Aos Cloud", online: "ONLINE", lifecycle: "provisioned", installedVersion: "78.0.0", pendingVersion: state.pending ? "79.0.0" : null,
        installedProfile: { state: state.profileState, profile: state.vdpProfile, releaseVersion: "78.0.0", cloudVersionId: state.profileId, source: "CLOUD_INSTALLATION_AND_PACKAGE", reason: null },
        releases: [], runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD", inventory: {
          unitId: state.uid, systemUid: state.uid, nodes: { state: "CURRENT", value: [{ node_id: "controller" }] }, teamServiceIds: { brake: "brake-id", tire: "tire-id" },
          components: { state: "CURRENT", value: [{ type: "demo-vehicle-data-provider", installed_component: { id: "vdp-78", version: "78.0.0" }, pending_component: null, pending_component_status: state.statusOnlyPending ? "downloading" : null }] },
          services: { state: "CURRENT", value: releases.map(release => ({ subject: `${release.team}-subject`, service: { id: release.serviceId, title: `${release.team === "brake" ? "Brake" : "Tire"} Health` },
            service_versions: { installed_service_version: state.firstServicePending && release.team === "brake" ? null : { version: release.version },
              pending_service_version: state.firstServicePending && release.team === "brake" ? { version: release.version } : null },
            instances: { state: "CURRENT", value: state.firstServicePending && release.team === "brake" ? [] : [{ instance_id: 0, run_state: "active", version: release.version }] } })) },
        } },
    } });
    if (path.endsWith("/monitoring-history")) return route.fulfill({ json: { unitId: state.uid, readCompletedAt: now, history: { state: "CURRENT", value: { series: [], coverage: { points: 0, retention: "SOURCE_RETURNED", conflicts: 0 } } } } });
    if (path.endsWith("/monitoring")) {
      if (state.failResources) return route.fulfill({ status: 503, json: {} });
      return route.fulfill({ json: { unitId: state.uid, readCompletedAt: now, monitoring: { state: "CURRENT", value: {
        cpu: { state: "CURRENT", unit: "DMIPS", value: [{ nodeId: "controller", value: 0, time: now }] },
        ram: { state: "CURRENT", unit: "bytes", value: [{ nodeId: "controller", value: 123456, time: now }] },
      } } } });
    }
    const team = path.endsWith("/backend/brake") ? "brake" : path.endsWith("/backend/tire") ? "tire" : null;
    if (team) {
      if (team === "brake" && state.failBrake) return route.fulfill({ status: 503, json: {} });
      const pageData = (items: unknown[] = []) => ({ state: "OBSERVED", data: { unitSystemUid: state.uid, items } });
      return route.fulfill({ json: { team, state: "OBSERVED", source: "REAL_BACKEND_HTTP", observedAt: now, observations: {
        readiness: { state: "OBSERVED", data: { ready: true } }, productData: pageData(state.windowMode && team === "brake" ? [windowRecord] : []), events: state.partialEvents ? { state: "UNAVAILABLE" } : pageData(), advisories: pageData(), functionStatus: pageData(),
        functionObservations: { state: "OBSERVED", data: { schemaVersion: 3, contractVersion: "3.0.0", resourceType: "FUNCTION_OBSERVATION", unitSystemUid: state.uid, truncated: false,
          items: [{ backendReceivedAt: now, authority: "FUNCTION_TEAM_REPORTED_OBSERVATION", stale: false, clockSkew: false, deliveryState: state.functionConflict ? "CONFLICT" : "DURABLY_RECEIVED", message: {
            schemaVersion: 3, contractVersion: "3.0.0", messageType: team.toUpperCase() + "_FUNCTION_OBSERVATION", unitSystemUid: state.uid, unitRole: "VALIDATION",
            serviceInstance: { serviceId: `${team}-id`, subjectId: `${team}-subject`, instanceIndex: 0, instanceId: `native-${team}` },
            serviceVersion: team === "brake" ? "58.0.0" : "34.0.0", serviceProfile: team === "brake" ? "v3" : "v1", generation: 1, sequence: 4,
            observedAt: new Date(Date.parse(now) - state.functionAge).toISOString(), contentSha256: "a".repeat(64), content: {
              connection: state.functionInput === "WAITING" ? "STARTING" : "CONNECTED", input: { state: state.functionInput, reason: state.functionInput === "RECEIVING" ? "NONE" : state.functionInput === "WAITING" ? "AWAITING_INPUT" : "SOURCE_GAP" },
              activity: { state: state.functionActivity, reason: state.functionActivity === "WAITING" ? "NOT_QUALIFIED" : "NONE", episodeId: "episode-a" },
              delivery: { state: "IDLE", queuedMessages: 0, lastReceiptAt: now }, advisory: { state: "WAITING", requestId: null }, lastResult: null,
            } } }] } },
        assessments: pageData(state.noResult ? [] : [{ backendReceivedAt: new Date(Date.parse(now) - state.receiptAge).toISOString(), deliveryState: state.productConflict && team === "brake" ? "CONFLICT" : "DURABLY_RECEIVED", message: {
          messageType: team === "brake" ? "BRAKE_HEALTH_ASSESSMENT" : "TIRE_HEALTH_ASSESSMENT", unitSystemUid: state.uid,
          serviceInstance: { serviceId: `${team}-id`, subjectId: `${team}-subject`, instanceIndex: 0, instanceId: `native-${team}` },
          serviceVersion: team === "brake" ? state.oldBrake ? "57.0.0" : "58.0.0" : "34.0.0", sourceEventTime: now,
          content: { currentBand: "INSPECTION_RECOMMENDED", conditionScore: 40, confidencePercent: 75, quality: "VALID", provenance: "DEMO_SYNTHETIC" },
        } }]),
        demoReset: { state: "OBSERVED", data: { schemaVersion: 1, unitSystemUid: state.uid, connected: state.resetConnected,
          command: state.reset && team === "brake" ? { ...confirmedReset({ ...binding, unitSystemUid: state.uid, serviceVersion: state.resetVersion },
            new Date(Date.parse(now) + 1).toISOString(), new Date(Date.parse(now) + 2).toISOString()),
            ...(state.resetOutcome === "CLEARED" ? {} : { state: state.resetOutcome, result: null }) } : null } },
      } } });
    }
    return route.fulfill({ status: 404, json: {} });
  });
  return { state, calls, reads: (suffix: string) => calls.filter(call => call.path.endsWith(suffix)).length };
}

for (const viewport of [{ width: 1280, height: 720 }, { width: 1280, height: 1000 }]) test(`reaudit: product conflict remains explicit and fits ${viewport.height}px`, async ({ page }) => {
  await page.setViewportSize(viewport);
  const fixture = await scenario(page); fixture.state.productConflict = true;
  await page.goto("/#native-browser");
  const card = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  await expect(card).toContainText("Result conflict");
  await expect(card).not.toContainText("Inspection recommended");
  await card.click();
  const dialog = page.getByRole("dialog", { name: "Brake backend", exact: true });
  await expect(dialog.getByRole("heading", { name: "Result not trusted" })).toBeVisible();
  await expect(dialog.getByRole("meter")).toHaveCount(0);
  await expect(dialog.getByText(/Conflicting content/)).toBeVisible();
  expect(await dialog.evaluate(el => el.scrollHeight <= el.clientHeight + 1)).toBe(true);
  await page.screenshot({ path: `test-results/reaudit-conflict-${viewport.height}.png` });
  await dialog.getByRole("button", { name: "Records", exact: true }).click();
  await expect(dialog.getByText("Current Test · CONFLICT")).toBeVisible();
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("reaudit: first service delivery has observation guidance, without republish or Safe Stop", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.firstServicePending = true;
  await page.goto("/#native-browser");
  const guide = page.locator(".studio-guide");
  await expect(guide).toContainText("Service update pending");
  await expect(guide).toContainText("Brake 58.0.0");
  await expect(guide).toContainText("Safe Stop is not required");
  await expect(guide).not.toContainText("Prepare and publish");
  await expect(guide.getByRole("button", { name: "Refresh Cloud state" })).toBeEnabled();
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("audit: status-only component pending agrees across overview, dialog and Platform guide", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.statusOnlyPending = true;
  await page.goto("/#native-browser");
  await expect(page.getByRole("button", { name: "Aos Cloud Unit monitoring" })).toContainText("1 pending / in progress");
  await page.getByRole("button", { name: "Aos Cloud Unit monitoring" }).click();
  const tile = page.getByRole("button", { name: /Vehicle Data Platform 78.0.0 Update in progress/ });
  await expect(tile).toBeVisible(); await tile.click();
  await expect(page.getByRole("dialog", { name: "Vehicle Data Platform", exact: true })).toContainText("Update in progress · version not reported");
  await page.keyboard.press("Escape"); await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Platform Team", exact: true }).click();
  await expect(page.locator(".studio-guide")).toContainText("version not reported");
  await expect(page.getByRole("button", { name: "Sign & publish", exact: true })).toBeDisabled();
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("audit: old receipt and stale binding have matching qualifiers on card and popup", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.receiptAge = 2 * 86400000;
  await page.goto("/#native-browser");
  const card = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  await expect(card).toContainText("Latest result received · 2d ago");
  await expect(card).toContainText(/Backend checked · \d+s ago/);
  fixture.state.cloudCurrent = false;
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(card).toContainText("Inspection recommended · last known");
  await card.click();
  await expect(page.getByRole("dialog", { name: "Brake backend", exact: true })).toContainText("Latest product result · last known");
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("audit: partial history preserves fresh input without claiming complete result proof", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.partialEvents = true;
  await page.setViewportSize({ width: 1280, height: 720 }); await page.goto("/");
  const card = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  await expect(card).toContainText("RECEIVING"); await expect(card).toContainText("last known");
  await card.click();
  const dialog = page.getByRole("dialog", { name: "Brake backend", exact: true });
  await expect(dialog).toContainText("Partial backend read"); await expect(dialog).toContainText("events");
  await page.screenshot({ path: "test-results/partial-backend-1280.png" });
  const size = await dialog.locator(".modal-body").evaluate(n => ({ available: n.clientHeight, content: n.scrollHeight }));
  expect(size.content, JSON.stringify(size)).toBeLessThanOrEqual(size.available + 1);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Tire Team", exact: true }).click();
  await expect(page.locator(".studio-guide")).toContainText("Next in the demo: Brake result");
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

for (const viewport of [{ width: 1280, height: 720 }, { width: 1118, height: 1124 }]) test(`stale empty input and interrupted recording fit ${viewport.width}x${viewport.height}`, async ({ page }) => {
  const fixture = await scenario(page);
  fixture.state.noResult = true; fixture.state.functionInput = "STALE";
  await page.setViewportSize(viewport); await page.goto(viewport.width === 1118 ? "/#native-browser" : "/");
  for (const team of ["Brake", "Tire"]) {
    const guidance = `Source data is stale. Waiting for fresh input before the next ${team === "Brake" ? "recording" : "driving exercise"}.`;
    const card = page.getByRole("button", { name: `${team} backend Open dashboard`, exact: true });
    await expect(card).toContainText("Waiting for fresh input");
    await card.click();
    const dialog = page.getByRole("dialog", { name: `${team} backend`, exact: true });
    await expect(dialog.getByText(guidance, { exact: true })).toBeVisible();
    const fits = await dialog.locator(".modal-body").evaluate(n => n.scrollHeight <= n.clientHeight + 1 && n.scrollWidth <= n.clientWidth + 1);
    expect(fits).toBe(true);
    await page.keyboard.press("Escape");
  }
  fixture.state.functionInput = "WAITING";
  await page.getByRole("button", { name: "Brake backend Open dashboard", exact: true }).click();
  await page.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await expect(page.getByRole("dialog").getByText("The service is waiting for usable local input. No denied access or telemetry readiness is confirmed.")).toBeVisible();
  fixture.state.windowMode = true; fixture.state.windowInterrupted = true;
  await page.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await page.getByRole("button", { name: "Records", exact: true }).click();
  await page.getByRole("button", { name: /WINDOW_COMPLETION/ }).click();
  const detail = page.getByRole("dialog", { name: "Backend product record", exact: true });
  await expect(detail.getByText("Recording interrupted: source data gap", { exact: true })).toBeVisible();
  await expect(detail.getByText("All retained chunks received (3/3)", { exact: true })).toBeVisible();
  await expect(detail.getByText("INCOMPLETE_SOURCE_GAP", { exact: true })).toBeVisible();
  const fits = await detail.locator(".modal-body").evaluate(n => n.scrollHeight <= n.clientHeight + 1 && n.scrollWidth <= n.clientWidth + 1);
  expect(fits).toBe(true);
  await page.screenshot({ path: `test-results/follow-up-window-${viewport.width}.png` });
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("SOTA retains a confirmed earlier Reset as history without hiding the current result", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.reset = true; fixture.state.resetVersion = "57.0.0";
  await page.goto("/#native-browser");
  const brake = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  await expect(brake).toContainText("Inspection recommended");
  await brake.click();
  await expect(page.getByRole("dialog").getByText("Reset for release 57.0.0 confirmed · historical, not a reset of the current release.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "INSPECTION RECOMMENDED", exact: true })).toBeVisible();
  await expect(page.getByText("Reset outcome unconfirmed", { exact: true })).toHaveCount(0);
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("Vehicle summaries and dialogs share reads; closing restores Vehicle and focus", async ({ page }) => {
  const fixture = await scenario(page);
  await page.goto("/#native-browser");
  const brake = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  await expect(brake).toContainText("Inspection recommended");
  await expect(page.getByRole("button", { name: "Aos Cloud Unit monitoring" })).toContainText("1 component · 2 services");
  expect(fixture.reads("/monitoring")).toBe(1);
  const reads = fixture.reads("/backend/brake");
  await brake.click();
  await expect(page.getByRole("dialog", { name: "Brake backend", exact: true })).toBeVisible();
  await expect(page.getByRole("dialog").getByRole("button", { name: /Reset.*scenario/ })).toHaveCount(0);
  expect(fixture.reads("/backend/brake")).toBe(reads);
  await page.getByRole("button", { name: "Records", exact: true }).click();
  await page.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await expect(page.getByRole("button", { name: "Refresh backend", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Records", exact: true }).focus();
  await expect(page.getByRole("button", { name: "Records", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Records", exact: true })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(brake).toBeFocused();
  await expect(page.getByRole("button", { name: "Vehicle", exact: true })).toHaveAttribute("aria-pressed", "true");
  expect(fixture.calls.every(call => call.method === "GET" && !/guest|runtime-inspect/.test(call.path))).toBe(true);
});

test("moving input and qualifying activity are independent; late receipts never refresh source facts", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.functionActivity = "WAITING";
  await page.goto("/#native-browser");
  const brake = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  await expect(brake).toContainText("RECEIVING"); await expect(brake).toContainText("WAITING");
  await brake.click();
  await expect(page.getByText("NOT QUALIFIED", { exact: true })).toBeVisible();
  fixture.state.functionAge = 120000;
  await page.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await expect(page.getByText(/Function report · LAST KNOWN/)).toBeVisible();
  await page.keyboard.press("Escape"); await expect(brake).toContainText("Last known");
  await expect(brake).not.toContainText("RECEIVING");
  fixture.state.functionConflict = true; fixture.state.functionAge = 0;
  await brake.click(); await page.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await expect(page.getByText(/Function report · CONFLICT/)).toBeVisible();
  await expect(page.locator('[aria-label="Service function observation"]')).not.toContainText("RECEIVING");
});

test("service dialog separates installed compatibility from input and refreshes in place", async ({ page }) => {
  const fixture = await scenario(page);
  fixture.state.vdpProfile = "v2";
  fixture.state.pending = true;
  await page.goto("/#native-browser");
  await page.locator('[data-anchor="brake-service"]').click();
  const compatibility = page.getByRole("region", { name: "Installed software compatibility" });
  await expect(compatibility).toContainText("VDP V3 or later");
  await expect(compatibility).toContainText("Required VDP profile not installed · VDP V2");
  await expect(compatibility).toContainText("Input, assessments and advisory are observed separately");
  fixture.state.vdpProfile = "v3";
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(compatibility).toContainText("Compatible · VDP V3");
  await page.keyboard.press("Escape");
  await page.locator('[data-anchor="tire-service"]').click();
  await expect(compatibility).toContainText("VDP V3 or later");
  await expect(compatibility).toContainText("Compatible · VDP V3");
  expect(fixture.calls.every(call => call.method === "GET" && !/guest|runtime-inspect/.test(call.path))).toBe(true);
});

for (const condition of ["STALE", "UNKNOWN", "wrong-artifact"]) test(`profile ${condition} cannot establish current software progress`, async ({ page }) => {
  const fixture = await scenario(page);
  if (condition === "wrong-artifact") fixture.state.profileId = "vdp-pending";
  else fixture.state.profileState = condition;
  await page.goto("/#native-browser");
  await expect(page.locator(".studio-guide")).not.toContainText("Software story complete");
  await expect(page.locator(".studio-guide")).toContainText(condition === "STALE" ? "Refresh installed profile" : "Installed profile not confirmed");
  if (condition === "STALE") await expect(page.locator(".studio-vdp")).toContainText("last known");
  await page.locator('[data-anchor="brake-service"]').click();
  const compatibility = page.getByRole("region", { name: "Installed software compatibility" });
  await expect(compatibility).toContainText(condition === "STALE" ? "Compatible · VDP V3 · last known" : "Not confirmed");
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("team dialog retains its authoring profile; details have no reset action and write nothing", async ({ page }) => {
  const fixture = await scenario(page);
  await page.goto("/#native-browser");
  await page.getByRole("button", { name: "Brake Team", exact: true }).click();
  await page.getByRole("button", { name: "v3 Driver advisory", exact: true }).click();
  await page.getByRole("button", { name: /Open Brake backend/ }).click();
  await expect(page.getByRole("dialog").getByRole("button", { name: /Reset.*scenario/ })).toHaveCount(0);
  await expect(page.getByRole("dialog", { name: "Brake backend", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "v3 Driver advisory", exact: true })).toHaveAttribute("aria-pressed", "true");
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("completed story offers confirmed Finish; old-release evidence never completes it", async ({ page }) => {
  const fixture = await scenario(page);
  fixture.state.oldBrake = true;
  await page.goto("/#native-browser");
  await expect(page.getByRole("button", { name: "Brake backend Open dashboard" })).toContainText("No current-release result");
  await expect(page.locator(".studio-guide")).not.toContainText("Software story complete");
  fixture.state.oldBrake = false;
  await page.getByRole("button", { name: "Brake backend Open dashboard" }).click();
  await page.getByRole("button", { name: "Refresh backend" }).click();
  await expect(page.getByText("INSPECTION RECOMMENDED", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(".studio-guide")).toContainText("Software story complete");
  await page.locator(".studio-guide").getByRole("button", { name: "Finish demo", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("Permanent, no backup");
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("backend failure retains labelled history without affecting peer or Cloud; reset excludes old drive", async ({ page }) => {
  const fixture = await scenario(page);
  await page.goto("/#native-browser");
  const brake = page.getByRole("button", { name: "Brake backend Open dashboard" });
  await expect(brake).toContainText("Inspection recommended");
  fixture.state.failBrake = true;
  await brake.click();
  await page.getByRole("button", { name: "Refresh backend" }).click();
  await expect(page.getByText(/Backend unavailable or incomplete/)).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(brake).toContainText("Last known / incomplete");
  await expect(page.getByRole("button", { name: "Tire backend Open dashboard" })).toContainText("Result received");
  fixture.state.failBrake = false; fixture.state.reset = true;
  await brake.click(); await page.getByRole("button", { name: "Refresh backend" }).click();
  await expect(page.getByRole("dialog").getByText("Input is arriving and a recording is in progress. Waiting for its outcome.")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(brake).toContainText("No new result after reset");
  await expect(brake).not.toContainText("Inspection recommended");
});

for (const outcome of ["PENDING", "EXPIRED", "FAILED", "REJECTED"]) test(`reset ${outcome} retains honest card/dialog copy across contact recovery`, async ({ page }) => {
  const fixture = await scenario(page); fixture.state.reset = true;
  fixture.state.resetOutcome = outcome; fixture.state.resetConnected = false;
  await page.setViewportSize({ width: 1280, height: 720 }); await page.goto("/#native-browser");
  const card = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  const title = outcome === "PENDING" ? "Reset pending" : "Reset outcome unconfirmed";
  await expect(card).toContainText(title); await expect(card).not.toContainText("No current-release result");
  await card.click();
  const dialog = page.getByRole("dialog", { name: "Brake backend", exact: true });
  await expect(dialog.getByRole("heading", { name: title, exact: true })).toBeVisible();
  await expect(dialog).not.toContainText("No result for release 58.0.0 yet.");
  if (outcome !== "PENDING") {
    await expect(dialog).toContainText(`Reset ${outcome.toLowerCase()} · outcome unconfirmed`);
    await expect(dialog).toContainText("Reset requires Brake V3 and a connected reset channel.");
  }
  await expect(dialog.getByRole("button", { name: /Reset.*scenario/ })).toHaveCount(0);
  const size = await dialog.locator(".modal-body").evaluate(n => ({ available: n.clientHeight, content: n.scrollHeight }));
  expect(size.content, JSON.stringify(size)).toBeLessThanOrEqual(size.available + 1);
  fixture.state.resetConnected = true;
  await dialog.getByRole("button", { name: "Refresh backend", exact: true }).click();
  await expect(dialog).toContainText("Reset channel contact: recent");
  await expect(dialog.getByRole("heading", { name: title, exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Records", exact: true }).click();
  await expect(dialog).toContainText("BRAKE_HEALTH_ASSESSMENT");
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("Session defaults to lifecycle without credential inspection; setup is an explicit section", async ({ page }) => {
  const fixture = await scenario(page);
  await page.goto("/#native-browser");
  await expect(page.getByRole("heading", { name: "Your vehicle" })).toBeVisible();
  await page.evaluate(() => window.dispatchEvent(new Event("presenter-session")));
  await expect(page.getByRole("dialog", { name: "Demo session" })).toBeVisible();
  await expect(page.getByRole("button", { name: /^(Park|Resume|Continue Resume)$/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Finish demo", exact: true })).toBeEnabled();
  await expect(page.getByRole("dialog")).toContainText("Use Safe Stop in Driving Control for a pause");
  await expect(page.getByRole("button", { name: "Finish demo", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Test setup", exact: true }).click();
  await expect(page.getByRole("button", { name: "Check Cloud setup", exact: true })).toBeEnabled();
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

test("switching the observed Test drops prior summaries and a resource failure stays labelled", async ({ page }) => {
  const fixture = await scenario(page);
  await page.goto("/#native-browser");
  const cloud = page.getByRole("button", { name: "Aos Cloud Unit monitoring", exact: true });
  await expect(cloud).toContainText("No pending updates");
  expect(fixture.reads("/monitoring")).toBe(1);
  await cloud.click();
  await page.getByRole("button", { name: "Resources", exact: true }).click();
  await expect(page.getByRole("dialog").getByText("0 DMIPS", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog").getByText("0.12 MiB", { exact: true })).toBeVisible();
  fixture.state.failResources = true;
  await page.getByRole("button", { name: "Refresh Cloud state", exact: true }).click();
  await expect(page.getByText(/Cloud resource read failed/)).toBeVisible();
  await expect(page.getByRole("dialog").getByText("0.12 MiB", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog").getByRole("figure", { name: "controller Memory · last five minutes" })).toContainText("Last known");
  await page.keyboard.press("Escape");
  await expect(cloud).toContainText("No pending updates");
  await expect(cloud).toContainText("DMIPS");
  await expect(cloud).toContainText("Memory");
  fixture.state.uid = "test-b"; fixture.state.failBrake = true;
  await page.locator(".studio-footer").getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(cloud).not.toContainText("0 DMIPS");
  const brake = page.getByRole("button", { name: "Brake backend Open dashboard", exact: true });
  await expect(brake).not.toContainText("Inspection recommended");
  await expect(page.locator(".studio-guide")).not.toContainText("Software story complete");
});

test("service colors link matching backends while AosCore and Cloud share platform identity", async ({ page }) => {
  await scenario(page); await page.goto("/#native-browser");
  const core = page.locator(".studio-factory");
  await expect(core).toContainText("AosCore");
  await expect(core).toContainText("In-vehicle runtime");
  await expect(core.locator(".b2-service")).toBeVisible();
  await expect(core.getByRole("combobox", { name: "Factory image" })).toBeDisabled();
  await expect(page.getByText("AosEdge platform", { exact: true })).toHaveCount(2);
  for (const team of ["brake", "tire"]) {
    const card = page.locator(`[data-anchor='${team}-backend']`);
    const service = page.locator(`[data-anchor='${team}-service']`);
    await expect(card).toHaveAttribute("data-team", team);
    await expect(service).toHaveAttribute("data-team", team);
    const color = await card.evaluate(node => getComputedStyle(node).borderTopColor);
    await expect(service).toHaveCSS("border-left-color", color);
    await expect(page.locator(`.studio-wires path[data-team='${team}']`)).toHaveCSS("stroke", color);
    await card.click();
    await expect(page.locator(`.studio-modal-layer[data-team='${team}'] .modal-head`)).toHaveCSS("border-top-color", color);
    await page.keyboard.press("Escape");
  }
  await expect(page.locator(".studio-wires path.online")).toHaveCSS("stroke", "rgb(56, 140, 114)");
});

test("upgraded Brake exposes retained V1 charts without relabelling the V3 result", async ({ page }) => {
  const fixture = await scenario(page); fixture.state.windowMode = true;
  await page.goto("/");
  await page.getByRole("button", { name: "Brake backend Open dashboard", exact: true }).click();
  await expect(page.getByRole("heading", { name: "INSPECTION RECOMMENDED", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View braking recordings & charts ↗", exact: true }).click();
  await expect(page.getByLabel("Record type", { exact: true })).toHaveValue("windows");
  await expect(page.getByRole("button", { name: /WINDOW_COMPLETION/ })).toContainText("56.0.0");
  await expect(page.getByRole("button", { name: /BRAKE_HEALTH_ASSESSMENT/ })).toHaveCount(0);
  await page.getByRole("button", { name: /WINDOW_COMPLETION/ }).click();
  await expect(page.getByRole("img", { name: "Speed: actual retained samples" })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByLabel("Record type", { exact: true }).selectOption("all");
  await expect(page.getByRole("button", { name: /BRAKE_HEALTH_ASSESSMENT/ })).toBeVisible();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await expect(page.getByRole("heading", { name: "INSPECTION RECOMMENDED", exact: true })).toBeVisible();
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

for (const viewport of [{ width: 1280, height: 720 }, { width: 1728, height: 1117 }, { width: 1118, height: 1124 }]) test(`retained V1 window detail fits ${viewport.width}x${viewport.height}`, async ({ page }) => {
  const fixture = await scenario(page); fixture.state.windowMode = true;
  await page.setViewportSize(viewport); await page.goto(viewport.width === 1118 ? "/#native-browser" : "/");
  await page.getByRole("button", { name: "Brake backend Open dashboard", exact: true }).click();
  await page.getByRole("button", { name: "Records", exact: true }).click();
  await page.getByRole("button", { name: /WINDOW_COMPLETION/ }).click();
  const dialog = page.getByRole("dialog", { name: "Backend product record", exact: true });
  await expect(dialog.getByRole("region", { name: "Retained braking window" })).toContainText("150 retained samples");
  await expect(dialog.getByRole("img", { name: "Speed: actual retained samples" })).toBeVisible();
  await expect(dialog.getByRole("img", { name: "Brake pedal: actual retained samples" })).toBeVisible();
  await expect(dialog.getByRole("row")).toHaveCount(viewport.height <= 800 ? 4 : 6);
  const cellPositions = await dialog.locator("thead th").evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().x));
  expect(cellPositions.every((x, i) => !i || x > cellPositions[i - 1])).toBe(true);
  const valuePositions = await dialog.locator("tbody tr:first-child td").evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().x));
  expect(valuePositions.every((x, i) => Math.abs(x - cellPositions[i]) < 1)).toBe(true);
  const dimensions = await dialog.locator(".modal-body").evaluate(node => ({ available: [node.clientWidth, node.clientHeight], content: [node.scrollWidth, node.scrollHeight] }));
  await page.screenshot({ path: `test-results/window-detail-${viewport.width}.png` });
  expect(dimensions.content[0], JSON.stringify(dimensions)).toBeLessThanOrEqual(dimensions.available[0] + 1);
  expect(dimensions.content[1], JSON.stringify(dimensions)).toBeLessThanOrEqual(dimensions.available[1] + 1);
  await dialog.getByRole("button", { name: "Next samples" }).click();
  await expect(dialog.getByLabel("Window sample pages")).toContainText(viewport.height <= 800 ? "2 / 50" : "2 / 30");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Brake backend", exact: true })).toBeVisible();
  expect(fixture.calls.every(call => call.method === "GET")).toBe(true);
});

for (const viewport of [{ width: 1280, height: 720 }, { width: 1327, height: 851 }, { width: 1327, height: 900 }, { width: 1327, height: 923 }, { width: 1440, height: 900 }, { width: 1728, height: 1117 }, { width: 1118, height: 1124 }]) test(`2.10 populated summaries and dialogs fit ${viewport.width}x${viewport.height}`, async ({ page }) => {
  await scenario(page); await page.setViewportSize(viewport);
  await page.goto(viewport.width === 1118 ? "/#native-browser" : "/");
  await expect(page.getByRole("button", { name: "Brake backend Open dashboard" })).toContainText("Inspection recommended");
  const fit = async (selector: string) => {
    const box = await page.locator(selector).evaluate(node => ({ width: node.scrollWidth <= node.clientWidth + 1, height: node.scrollHeight <= node.clientHeight + 1 }));
    if (!box.height || !box.width) await page.screenshot({ path: `test-results/dialog-overflow-${viewport.width}.png` });
    const dimensions = await page.locator(selector).evaluate(node => ({
      available: [node.clientWidth, node.clientHeight], content: [node.scrollWidth, node.scrollHeight],
      children: [...node.children].map(child => ({ class: child.className, height: child.getBoundingClientRect().height })),
      sections: [...node.querySelectorAll('.studio-backends,.studio-architecture,.studio-controller,.studio-controller h2,.studio-service-slots,.studio-vdp,.studio-factory,.studio-core')].map(child => ({ class: child.className, height: child.getBoundingClientRect().height })),
    }));
    expect(box.width, JSON.stringify(dimensions)).toBe(true);
    if (selector === ".studio-body" && !box.height) {
      expect(await page.locator(selector).evaluate(node => getComputedStyle(node).overflowY)).toBe("auto");
      await page.locator(".studio-controller").scrollIntoViewIfNeeded();
      await expect(page.getByLabel("Factory image")).toBeInViewport();
      await page.locator('[data-anchor="cloud-backend"]').scrollIntoViewIfNeeded();
    } else if (!box.height && await page.getByRole("region", { name: "CPU and memory history" }).count()) {
      expect(await page.locator(selector).evaluate(node => getComputedStyle(node).overflowY)).toBe("auto");
      await page.getByRole("figure", { name: "tire Memory · last five minutes" }).scrollIntoViewIfNeeded();
      await expect(page.getByRole("figure", { name: "tire Memory · last five minutes" })).toBeInViewport();
    } else expect(box.height, JSON.stringify(dimensions)).toBe(true);
  };
  await fit(".studio-body");
  await expect(page.locator('[data-anchor="cloud-backend"] .studio-summary-time')).toBeVisible();
  await expect.poll(() => page.locator(".studio-architecture-stage").evaluate(root => {
    const bounds = root.getBoundingClientRect();
    return ["brake", "tire"].flatMap((name, index) => {
      const path = root.querySelectorAll<SVGPathElement>(".studio-wires path.service")[index];
      const target = root.querySelector(`[data-anchor='${name}-service']`)?.getBoundingClientRect();
      const backend = root.querySelector(`[data-anchor='${name}-backend']`)?.getBoundingClientRect();
      const controller = root.querySelector('[data-anchor="controller"]')?.getBoundingClientRect();
      if (!path || !target || !backend || !controller) return [{ name, missing: true }];
      const end = path.getPointAtLength(path.getTotalLength());
      const elbow = Number(path.getAttribute('d')?.match(/ V ([\d.]+)/)?.[1]);
      const aligned = Math.abs(end.x - (target.x + target.width / 2 - bounds.x)) < 2 && Math.abs(end.y - (target.top - bounds.top)) < 2
        && elbow > backend.bottom - bounds.top && elbow < controller.top - bounds.top;
      return aligned ? [] : [{ name, missing: false, path: path.getAttribute('d'), elbow, backend: backend.bottom - bounds.top, controller: controller.top - bounds.top, end: [end.x, end.y], target: [target.x + target.width / 2 - bounds.x, target.top - bounds.top] }];
    });
  })).toEqual([]);
  await page.screenshot({ path: `test-results/vehicle-210-${viewport.width}.png` });
  for (const name of ["Brake backend Open dashboard", "Tire backend Open dashboard", "Aos Cloud Unit monitoring"]) {
    await page.getByRole("button", { name, exact: true }).click();
    await fit(".studio-modal-layer > .modal > .modal-body");
    if (name.startsWith("Aos")) { await page.getByRole("button", { name: "Resources", exact: true }).click(); await fit(".studio-modal-layer > .modal > .modal-body"); }
    await page.screenshot({ path: `test-results/dialog-210-${name.split(" ")[0]}-${viewport.width}.png` });
    await page.keyboard.press("Escape");
  }
  for (const team of ["brake", "tire"]) {
    await page.locator(`[data-anchor='${team}-service']`).click();
    await expect(page.getByRole("region", { name: "Installed software compatibility" })).toContainText("Compatible · VDP V3");
    await fit(".studio-modal-layer > .modal > .modal-body");
    await page.screenshot({ path: `test-results/compatibility-${team}-${viewport.width}.png` });
    await page.keyboard.press("Escape");
  }
});

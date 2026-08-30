import { expect, test } from "@playwright/test";

async function openGlobal(page: import("@playwright/test").Page, fixture: string) {
  await page.goto(`/?fixture=${fixture}`);
  await page.getByRole("button", { name: /AosEdge Software Evolution Demo/ }).click();
}

test("UI-AT-004/005 — exact Test and Production read projection", async ({ page }) => {
  await openGlobal(page, "ready");
  const state = page.getByTestId("read-only-cloud-state");
  await expect(state).toContainText("Test Vehicle");
  await expect(state).toContainText("VALIDATION");
  await expect(state).toContainText("Production Vehicle");
  await expect(state).toContainText("Persistent role Unit Sets");
  await expect(state).toContainText("Distinct release objects");
});

test("UI-AT-022/032 — stale source remains visibly stale", async ({ page }) => {
  await openGlobal(page, "read-only-stale");
  await expect(page.getByText("STALE · AVAILABLE", { exact: false }).first()).toBeVisible();
  await expect(page.getByText("Current state cannot be confirmed", { exact: false }).first()).toBeVisible();
});

test("UI-AT-020/029 — unauthenticated Cloud session does not retain current Unit state", async ({ page }) => {
  await openGlobal(page, "read-only-unauthenticated");
  await expect(page.getByText("UNKNOWN · UNAUTHENTICATED", { exact: false }).first()).toBeVisible();
  await expect(page.getByText("Current membership cannot be confirmed")).toBeVisible();
});

test("UI-AT-006/043 — incomplete membership never renders current", async ({ page }) => {
  await openGlobal(page, "read-only-truncated-membership");
  await expect(page.getByText("INCOMPLETE", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Current membership cannot be confirmed")).toBeVisible();
});

test("UI-AT-021/024 — Details shows only sanitized fixture provenance", async ({ page }) => {
  await page.goto("/?fixture=ready");
  await page.getByRole("button", { name: "Details" }).first().click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("CONTRACT_SYNTHETIC · fixture — not live");
  await expect(dialog).toContainText("Effective read permissions");
  await expect(dialog).not.toContainText(/BEGIN PRIVATE KEY|Bearer\s|https?:\/\//i);
});

test("UI-AT-027 — native log view is metadata-only and owner-scoped", async ({ page }) => {
  await page.goto("/?fixture=ready");
  await page.getByRole("button", { name: /Platform Logs/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("waiting unit");
  await expect(dialog).toContainText("empty log has been provided");
  await expect(dialog).toContainText("Raw content");
  await expect(dialog).toContainText("Not exposed by this fixture-first read projection");
});

test("UI-AT-040/041 — Brake current-Unit projection preserves pending provenance", async ({ page }) => {
  await page.goto("/?fixture=ready");
  await page.locator("[data-team='brake']").click();
  const projection = page.getByTestId("brake-read-projection");
  await expect(projection).toContainText("PENDING_ASSESSMENT_CORRELATION");
  await expect(projection).not.toContainText(/Unit ready|Cloud lifecycle/i);
});

test("UI-AT-048 — current Unit with no Brake data is a factual empty result", async ({ page }) => {
  await page.goto("/?fixture=read-only-brake-empty");
  await page.locator("[data-team='brake']").click();
  await expect(page.getByText("Current Unit · no Brake data")).toBeVisible();
  await expect(page.getByText(/Empty is factual and does not imply Unit failure/)).toBeVisible();
});

test("UI-AT-050 — Brake schema failure remains source-local", async ({ page }) => {
  await page.goto("/?fixture=read-only-schema-invalid");
  await page.locator("[data-team='brake']").click();
  await expect(page.getByText("UNKNOWN · SCHEMA_INVALID", { exact: false }).first()).toBeVisible();
});

test("UI-AT-019/020 — fixture confirmation emits no off-origin request", async ({ page }) => {
  await page.goto("/?fixture=ready");
  const origin = new URL(page.url()).origin;
  const offOrigin: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).origin !== origin) offOrigin.push(request.url());
  });
  await page.getByRole("button", { name: "Sign and submit prepared candidate" }).first().click();
  await page.getByRole("button", { name: "Confirm fixture presentation" }).click();
  await expect(page.getByRole("status")).toContainText("no external operation submitted");
  expect(offOrigin).toEqual([]);
});

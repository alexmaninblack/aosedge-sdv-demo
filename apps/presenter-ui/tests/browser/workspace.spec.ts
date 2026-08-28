import { expect, test } from "@playwright/test";

test("fixed context and independent version scroll are restored per team", async ({ page }) => {
  await page.goto("/?fixture=ready");
  const context = page.getByTestId("fixed-team-context");
  const scroll = page.getByTestId("release-scroll");
  const contextTop = await context.evaluate((element) => element.getBoundingClientRect().top);
  await scroll.evaluate((element) => { element.scrollTop = 620; element.dispatchEvent(new Event("scroll")); });
  await expect.poll(() => scroll.evaluate((element) => element.scrollTop)).toBeGreaterThan(300);
  expect(await context.evaluate((element) => element.getBoundingClientRect().top)).toBe(contextTop);
  await page.locator('[data-team="brake"]').click();
  await scroll.evaluate((element) => { element.scrollTop = 180; element.dispatchEvent(new Event("scroll")); });
  await page.locator('[data-team="platform"]').click();
  await expect.poll(() => scroll.evaluate((element) => element.scrollTop)).toBeGreaterThan(300);
  await page.locator('[data-team="brake"]').click();
  await expect.poll(() => scroll.evaluate((element) => element.scrollTop)).toBeGreaterThan(100);
});

test("Details traps focus, closes with Escape and returns focus without moving native reservations", async ({ page }) => {
  await page.goto("/?fixture=ready");
  const leftBounds = await page.locator(".native-reservations").boundingBox();
  const details = page.getByRole("button", { name: "Details" }).first();
  await details.focus();
  await details.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("button", { name: "Close dialog" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(details).toBeFocused();
  expect(await page.locator(".native-reservations").boundingBox()).toEqual(leftBounds);
});

test("desktop composition has no horizontal page scroll and reserves approximate halves", async ({ page }) => {
  await page.goto("/?fixture=ready");
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  expect(dimensions.width).toBe(dimensions.viewport);
  const left = await page.locator(".native-reservations").boundingBox();
  const right = await page.locator(".browser-workspace").boundingBox();
  expect(left).not.toBeNull();
  expect(right).not.toBeNull();
  expect(Math.abs(left!.width - right!.width)).toBeLessThan(130);
});

test("broken project icons fall back to labelled text without hiding state", async ({ page }) => {
  await page.goto("/?fixture=asset-failure");
  await expect(page.getByRole("img", { name: /icon unavailable/ }).first()).toBeVisible();
  await expect(page.getByText("Current vehicle · Test Vehicle")).toBeVisible();
  await expect(page.getByText("Platform Team", { exact: true }).first()).toBeVisible();
});

test("Platform details omit Service quota and VDP store while Brake details include Service quota", async ({ page }) => {
  await page.goto("/?fixture=ready");
  await expect(page.getByText("Service quota fields and VDP-owned application/log stores are intentionally absent.")).toBeVisible();
  await page.getByRole("button", { name: "Details" }).first().click();
  await expect(page.getByRole("dialog")).not.toContainText("Approved Service quota");
  await expect(page.getByRole("dialog")).toContainText("no Service quota or VDP-owned application/log store");
  await page.keyboard.press("Escape");
  await page.locator('[data-team="brake"]').click();
  await page.getByRole("button", { name: "Details" }).first().click();
  await expect(page.getByRole("dialog")).toContainText("Approved Service quota");
  await expect(page.getByRole("dialog")).toContainText("private identities are excluded");
});

test("Platform Logs and Service Operational Logs retain distinct scopes", async ({ page }) => {
  await page.goto("/?fixture=ready");
  await page.getByRole("button", { name: "Platform Logs" }).click();
  await expect(page.getByRole("dialog")).toContainText("Platform Team · Platform Logs");
  await expect(page.getByRole("dialog")).toContainText("Current Unit/system/VDP");
  await expect(page.getByRole("dialog")).toContainText("Native systemd journal via AosEdge/AosCloud log delivery");
  await expect(page.getByRole("dialog")).toContainText("No VDP or Demo UI log store");
  await page.keyboard.press("Escape");

  await page.locator('[data-team="brake"]').click();
  await page.getByRole("button", { name: "Operational Logs" }).click();
  await expect(page.getByRole("dialog")).toContainText("Brake Team · Operational Logs");
  await expect(page.getByRole("dialog")).toContainText("Current Service instance and owning provider");
  await expect(page.getByRole("dialog")).toContainText("AosCloud native Service-log delivery representation");
});

test("fixture action confirms locally and makes no external request", async ({ page }) => {
  const offOriginRequests: string[] = [];
  page.on("request", (request) => { if (!request.url().startsWith("http://127.0.0.1:18070")) offOriginRequests.push(request.url()); });
  await page.goto("/?fixture=ready");
  await page.getByRole("button", { name: "Sign and submit prepared candidate" }).first().click();
  await page.getByRole("button", { name: "Confirm fixture presentation" }).click();
  await expect(page.getByRole("status")).toContainText("no external operation submitted");
  expect(offOriginRequests).toEqual([]);
});

test("Demo Lifecycle uses audience language while internal lifecycle codes stay hidden", async ({ page }) => {
  await page.goto("/?fixture=ready");
  await page.getByRole("button", { name: /AosEdge Software Evolution Demo/ }).click();
  const lifecycle = page.getByTestId("global-lifecycle-page");
  await expect(lifecycle).toContainText("Produce Test and Production Vehicles");
  await expect(lifecycle).toContainText("Bring Vehicles Under AosEdge Management");
  await expect(lifecycle).toContainText("Managed Vehicles Ready");
  await expect(lifecycle).not.toContainText("READY_FOR_M0");
  await expect(lifecycle.getByText("M0", { exact: true })).toHaveCount(0);
  await expect(lifecycle.getByText("M1", { exact: true })).toHaveCount(0);
  await expect(lifecycle.getByText("G0", { exact: true })).toHaveCount(0);
  await expect(lifecycle.getByText("R0", { exact: true })).toHaveCount(0);
});

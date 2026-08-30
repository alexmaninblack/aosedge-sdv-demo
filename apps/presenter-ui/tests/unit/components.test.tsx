import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { PresenterApp } from "../../src/app/PresenterApp";
import { PresenterReadModelProvider } from "../../src/app/state/PresenterReadModelProvider";
import { FixturePresenterReadAdapter } from "../../src/adapters/fixtures";
import { FixtureReadOnlyAdapter } from "../../src/adapters/read-only";

function renderFixture(id = "ready") {
  return render(<PresenterReadModelProvider dependencies={{ readPort: new FixturePresenterReadAdapter(id) }}><PresenterApp /></PresenterReadModelProvider>);
}

function renderReadOnly(id = "ready") {
  const shell = new FixturePresenterReadAdapter(id);
  const readPort = new FixtureReadOnlyAdapter(shell, id, () => "2026-08-30T09:00:02.000Z");
  return render(<PresenterReadModelProvider dependencies={{ readPort }}><PresenterApp /></PresenterReadModelProvider>);
}

describe("Presenter application components", () => {
  it("renders three producer perspectives and a separate Release Authority", async () => {
    renderFixture();
    expect(await screen.findByRole("button", { name: /Platform Team/ })).toBeVisible();
    expect(screen.getByRole("button", { name: /Brake Team/ })).toBeVisible();
    expect(screen.getByRole("button", { name: /Tire Team/ })).toBeVisible();
    expect(screen.getByLabelText("OEM Release Authority")).toHaveTextContent("Independent from producer teams");
  });

  it("normalizes vehicle wording and reserves native surfaces", async () => {
    renderFixture();
    expect(await screen.findByText("Current vehicle · Test Vehicle")).toBeVisible();
    expect(screen.getByText("Reserved for native CARLA window")).toBeVisible();
    expect(screen.getByText("TEXT-ONLY NATIVE TERMINAL")).toBeVisible();
    expect(document.querySelector("[data-native-surface='carla'] img[src*='screenshot']")).toBeNull();
  });

  it("shows Service quota only in Brake and Tire Details", async () => {
    const user = userEvent.setup();
    renderFixture();
    await screen.findByText("VDP v1");
    await user.click(screen.getAllByRole("button", { name: "Details" })[0]!);
    expect(screen.getByRole("dialog")).not.toHaveTextContent("Approved Service quota");
    await user.click(screen.getByRole("button", { name: "Close dialog" }));
    await user.click(screen.getByRole("button", { name: /Brake Team/ }));
    await user.click(screen.getAllByRole("button", { name: "Details" })[0]!);
    expect(screen.getByRole("dialog")).toHaveTextContent("Approved Service quota");
  });

  it("confirms fixture actions without changing observed lifecycle", async () => {
    const user = userEvent.setup();
    renderFixture();
    await screen.findByText("VDP v1");
    const stage = screen.getAllByText("Producer Team publishes candidate")[0]!.closest("li")!;
    await user.click(within(stage).getByRole("button", { name: "Sign and submit prepared candidate" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("External submissionImpossible in IMP-01");
    await user.click(screen.getByRole("button", { name: "Confirm fixture presentation" }));
    expect(screen.getByRole("status")).toHaveTextContent("no external operation submitted");
    expect(screen.getAllByText("Test authorization ready")[0]).toBeVisible();
  });

  it("renders the GET-only Cloud source projection separately from friendly lifecycle state", async () => {
    const user = userEvent.setup();
    renderReadOnly();
    await user.click(await screen.findByRole("button", { name: /AosEdge Software Evolution Demo/ }));
    expect(screen.getByTestId("read-only-cloud-state")).toHaveTextContent("fixture — not live");
    expect(screen.getByTestId("read-only-cloud-state")).toHaveTextContent("Test Vehicle");
    expect(screen.getByTestId("read-only-cloud-state")).toHaveTextContent("AosEdge SDV Demo / Production Vehicles");
    expect(screen.getByTestId("read-only-cloud-state")).toHaveTextContent("VERIFICATION_BATCH");
    expect(screen.getAllByText(/CONTRACT_SYNTHETIC/).length).toBeGreaterThan(0);
  });

  it("shows sanitized read provenance in Details without privileged material", async () => {
    const user = userEvent.setup();
    renderReadOnly();
    await screen.findByText("VDP v1");
    await user.click(screen.getAllByRole("button", { name: "Details" })[0]!);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveTextContent("CONTRACT_SYNTHETIC · fixture — not live");
    expect(dialog).toHaveTextContent("Effective read permissions");
    expect(dialog).not.toHaveTextContent(/BEGIN PRIVATE KEY|Bearer\s|https?:\/\//i);
  });

  it("shows exact native log metadata states but no raw log content", async () => {
    const user = userEvent.setup();
    renderReadOnly();
    await screen.findByText("VDP v1");
    await user.click(screen.getByRole("button", { name: /Platform Logs/ }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveTextContent("waiting unit");
    expect(dialog).toHaveTextContent("empty log has been provided");
    expect(dialog).toHaveTextContent("Retention policy not exposed by current API");
    expect(dialog).toHaveTextContent("Raw contentNot exposed");
  });

  it("renders Brake records for the current Unit without converting them to Unit readiness", async () => {
    const user = userEvent.setup();
    renderReadOnly();
    await user.click(await screen.findByRole("button", { name: /Brake Team/ }));
    const projection = screen.getByTestId("brake-read-projection");
    expect(projection).toHaveTextContent("PENDING_ASSESSMENT_CORRELATION");
    expect(projection).not.toHaveTextContent(/Unit ready|Cloud lifecycle/i);
  });
});

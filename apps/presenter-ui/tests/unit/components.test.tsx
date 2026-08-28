import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { PresenterApp } from "../../src/app/PresenterApp";
import { PresenterReadModelProvider } from "../../src/app/state/PresenterReadModelProvider";
import { FixturePresenterReadAdapter } from "../../src/adapters/fixtures";

function renderFixture(id = "ready") {
  return render(<PresenterReadModelProvider dependencies={{ readPort: new FixturePresenterReadAdapter(id) }}><PresenterApp /></PresenterReadModelProvider>);
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
});

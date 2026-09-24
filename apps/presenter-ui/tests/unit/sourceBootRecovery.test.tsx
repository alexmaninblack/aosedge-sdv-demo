// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { PresenterControls, usePresenterControls } from "../../src/app/state/PresenterControls";
vi.mock("../../src/app/state/PresenterReadModelProvider", () => ({ usePlatformObservation: () => ({ afterAction: vi.fn() }) }));
afterEach(cleanup);
function Probe() {
  const c = usePresenterControls();
  return <><p>{c.blockReason}</p><button disabled={c.blocked}>Change</button><button disabled={c.readBlocked}>Read</button></>;
}
test("controller restoration is not mislabeled as desktop layout recovery", async () => {
  const port = { read: vi.fn().mockResolvedValue({ sessionId: "session", active: null, uncertain: false, jobs: [], sourceRecoveryBusy: true }), submit: vi.fn() };
  render(<PresenterControls port={port}><Probe /></PresenterControls>);
  expect(await screen.findByText(/Restoring the controller connection/)).toHaveTextContent("Autopilot will not resume automatically");
  expect(screen.getByRole("button", { name: "Change" })).toBeDisabled();
  expect(screen.queryByText(/desktop window layout/)).not.toBeInTheDocument();
  expect(port.submit).not.toHaveBeenCalled();
});
test("uncertain recovery blocks writes but keeps read observations available", async () => {
  const port = { read: vi.fn().mockResolvedValue({ sessionId: "session", active: null, uncertain: false, jobs: [], sourceRecovery: { state: "FAILED" } }), submit: vi.fn() };
  render(<PresenterControls port={port}><Probe /></PresenterControls>);
  expect(await screen.findByText(/Controller connection recovery is incomplete/)).toBeVisible();
  expect(screen.getByRole("button", { name: "Change" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Read" })).toBeEnabled();
  expect(port.submit).not.toHaveBeenCalled();
});

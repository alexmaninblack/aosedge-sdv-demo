import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { PresenterControls, OperationProgress, usePresenterControls } from "../../src/app/state/PresenterControls";
import { LocalPresenterCommandAdapter } from "../../src/adapters/local/LocalPresenterCommandAdapter";
import type { DemoCommand, OperationSession } from "../../src/domain/presenterCommandPort";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function Buttons() {
  const controls = usePresenterControls();
  return <><button disabled={controls.blocked} onClick={() => controls.request({ action: "create", image: "31/arm64" })}>Create</button>
    <button disabled={controls.blocked} onClick={() => controls.request({ action: "approve", version: "13.0.0" })}>Approve</button>
    <button disabled={controls.blocked} onClick={() => controls.request({ action: "observe-test" })}>Observe</button><OperationProgress /></>;
}
function setup() {
  const state: OperationSession = { sessionId: "native-generation", active: null, uncertain: false, jobs: [] };
  const port = { read: vi.fn().mockResolvedValue(state), submit: vi.fn(async (command: DemoCommand, id: string, _sessionId: string) => ({ id, ...command,
    state: "ACCEPTED", startedAt: "now", progress: [], results: [] })) };
  render(<div className="browser-workspace"><PresenterControls port={port}><Buttons /></PresenterControls></div>);
  return port;
}
describe("protected Presenter controls", () => {
  it("cancel has no effect; confirmed double click submits exactly one bound action", async () => {
    const port = setup();
    await waitFor(() => expect(screen.getByText("Create")).toBeEnabled());
    fireEvent.click(screen.getByText("Create"));
    expect(screen.getByRole("dialog")).toHaveTextContent("31/arm64");
    expect(port.submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Cancel"));
    expect(port.submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Create"));
    const button = within(screen.getByRole("dialog")).getByRole("button", { name: "Create Test and Production Vehicles" });
    fireEvent.click(button); fireEvent.click(button);
    await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(1));
    expect(port.submit.mock.calls[0]).toEqual([{ action: "create", image: "31/arm64" }, expect.any(String), "native-generation"]);
    await waitFor(() => expect(screen.getByText(/Create Test and Production Vehicles · ACCEPTED/)).toBeInTheDocument());
    expect(screen.getByText("Create")).toBeDisabled();
  });
  it("approval identifies OEM authority and the exact Test release", async () => {
    const port = setup();
    await waitFor(() => expect(screen.getByText("Approve")).toBeEnabled());
    fireEvent.click(screen.getByText("Approve"));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveTextContent("OEM Release Authority");
    expect(dialog).toHaveTextContent("13.0.0");
    expect(dialog).toHaveTextContent("Production rollout is excluded");
    expect(port.submit).not.toHaveBeenCalled();
  });
  it("explicit read requires no mutation confirmation", async () => {
    const port = setup();
    await waitFor(() => expect(screen.getByText("Observe")).toBeEnabled());
    fireEvent.click(screen.getByText("Observe"));
    await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(1));
    expect(port.submit.mock.calls[0]?.[0]).toEqual({ action: "observe-test" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
  it("a lost submit response blocks further clicks instead of replaying", async () => {
    const port = setup();
    port.submit.mockRejectedValueOnce(new Error("UNCERTAIN"));
    await waitFor(() => expect(screen.getByText("Observe")).toBeEnabled());
    fireEvent.click(screen.getByText("Observe"));
    await screen.findByText(/Submission response lost/);
    expect(screen.getByText("Create")).toBeDisabled();
    expect(port.submit).toHaveBeenCalledTimes(1);
  });
  it("uses only the fixed same-origin route with no automatic retry", async () => {
    const request = vi.fn().mockResolvedValue({ status: 503 });
    vi.stubGlobal("fetch", request);
    const adapter = new LocalPresenterCommandAdapter();
    await expect(adapter.submit({ action: "approve", version: "13.0.0" }, "request", "generation")).rejects.toThrow("UNCERTAIN");
    expect(request).toHaveBeenCalledTimes(1);
    expect(request.mock.calls[0]![0]).toBe("/api/presenter/operations");
    expect(JSON.parse(request.mock.calls[0]![1].body)).toEqual({ action: "approve", version: "13.0.0", requestId: "request", sessionId: "generation" });
  });
});

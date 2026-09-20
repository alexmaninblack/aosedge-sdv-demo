import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { PresenterControls, OperationProgress, preparationRecovery, usePresenterControls } from "../../src/app/state/PresenterControls";
import { LocalPresenterCommandAdapter } from "../../src/adapters/local/LocalPresenterCommandAdapter";
import type { DemoCommand, OperationSession } from "../../src/domain/presenterCommandPort";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function Buttons() {
  const controls = usePresenterControls();
  return <><button disabled={controls.blocked} onClick={() => controls.request({ action: "create", image: "31/arm64" })}>Create</button>
    <button disabled={controls.blocked} onClick={() => controls.request({ action: "upload", version: "13.0.0" })}>Publish</button>
    <button disabled={controls.blocked} onClick={() => controls.request({ action: "service-publish", team: "brake", release: "brake/70" })}>Publish service</button>
    <button disabled={controls.blocked} onClick={() => controls.request({ action: "observe-test" })}>Observe</button><OperationProgress /></>;
}
function setup(jobs: OperationSession["jobs"] = []) {
  const state: OperationSession = { sessionId: "native-generation", cloudDomain: "selected.stage.example", active: null, uncertain: false, jobs };
  const port = { read: vi.fn().mockResolvedValue(state), submit: vi.fn(async (command: DemoCommand, id: string, _sessionId: string) => ({ id, ...command,
    state: "ACCEPTED", startedAt: "now", progress: [], results: [] })) };
  render(<div className="browser-workspace"><PresenterControls port={port}><Buttons /></PresenterControls></div>);
  return port;
}
describe("protected Presenter controls", () => {
  it("explains engineering prerequisites without bypassing or retrying preparation", () => {
    const job: any = { action: "service-prepare", state: "BLOCKED", results: [], reason: "SERVICE_COMMITTED_SOURCE_REQUIRED" };
    expect(preparationRecovery(job)).toContain("Retrying Prepare unchanged cannot succeed");
    job.reason = "SERVICE_BUILD_REQUIRED:democtl service build brake --content-profile v1";
    expect(preparationRecovery(job)).toContain("Engineering must build it before the demo");
    job.state = "COMPLETED"; expect(preparationRecovery(job)).toBeNull();
  });
  it("cancel has no effect; confirmed double click submits exactly one bound action", async () => {
    const port = setup();
    await waitFor(() => expect(screen.getByText("Create")).toBeEnabled());
    fireEvent.click(screen.getByText("Create"));
    expect(screen.getByRole("dialog")).toHaveTextContent("31/arm64");
    expect(port.submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Cancel"));
    expect(port.submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Create"));
    const button = within(screen.getByRole("dialog")).getByRole("button", { name: "Create controller" });
    fireEvent.click(button); fireEvent.click(button);
    await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(1));
    expect(port.submit.mock.calls[0]).toEqual([{ action: "create", image: "31/arm64" }, expect.any(String), "native-generation"]);
    await waitFor(() => expect(screen.getByText(/Create controller · ACCEPTED/)).toBeInTheDocument());
    expect(screen.getByText("Create")).toBeDisabled();
  });
  it("publication identifies OEM authority and immediate Test eligibility without an approval gate", async () => {
    const port = setup();
    await waitFor(() => expect(screen.getByText("Publish")).toBeEnabled());
    fireEvent.click(screen.getByText("Publish"));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveTextContent("selected session OEM");
    expect(dialog).toHaveTextContent("selected.stage.example");
    expect(dialog).toHaveTextContent("Selected session OEM certificate");
    expect(dialog).toHaveTextContent("13.0.0");
    expect(dialog).toHaveTextContent("no Production membership or assignment is changed");
    expect(dialog).toHaveTextContent("no batch-approval step is required");
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
  it.each([
    ["selected.stage.example", "brake/70", true],
    ["other.cloud.example", "brake/70", false],
    ["selected.stage.example", "brake/old", false],
  ])("service confirmation scopes the SP receipt to Cloud %s and release %s", async (cloudDomain, release, matching) => {
    const port = setup([{ id: "prepared", action: "service-prepare", cloudDomain, release, state: "COMPLETED", startedAt: "now", progress: [],
      results: [{ operation: "service.prepare", state: "COMPLETED", message: "Prepared", facts: { serviceProviderId: "verified-provider" } }] }] as any);
    await waitFor(() => expect(screen.getByText("Publish service")).toBeEnabled());
    fireEvent.click(screen.getByText("Publish service"));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveTextContent("selected.stage.example");
    expect(dialog).toHaveTextContent("Selected session Service Provider certificate");
    if (matching) expect(dialog).toHaveTextContent("verified-provider · last preparation/publication receipt");
    else { expect(dialog).not.toHaveTextContent("verified-provider"); expect(dialog).toHaveTextContent("Not yet reported for this release"); }
    expect(port.submit).not.toHaveBeenCalled();
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

import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { CloudConnectionPanel } from "../../src/app/CloudConnectionPanel";
import { PresenterControls } from "../../src/app/state/PresenterControls";
import type { DemoCommand, DemoJob, OperationSession } from "../../src/domain/presenterCommandPort";

afterEach(cleanup);

function setup(failure = false) {
  const state: OperationSession = { sessionId: "session", active: null, uncertain: false, jobs: [] };
  const port = { read: vi.fn(async () => state), submit: vi.fn(async (command: DemoCommand, id: string) => {
    if (["cloud-check", "cloud-prepare"].includes(command.action)) {
      const job: DemoJob = { id, action: command.action, state: "COMPLETED", startedAt: "now", progress: [], results: [{
        operation: command.action.replace("-", "."), state: "OBSERVED", message: "Test setup",
        facts: { stage: command.action === "cloud-check" ? "MISSING" : "READY", checks: [
          { key: "model", label: "Factory model", state: "MISSING", detail: "Single-node configuration required" }] },
      }] };
      state.jobs.push(job); return job;
    }
    const result = { operation: command.action === "cloud-select" ? "cloud.select" : "cloud.inspect",
      state: failure ? "BLOCKED" : command.action === "cloud-select" ? "COMPLETED" : "OBSERVED",
      message: failure ? "CLOUD_CERTIFICATE_UNAVAILABLE" : "Local certificate selection",
      facts: failure ? {} : { domain: "developer.aos-dev.test", certificateName: "oem.p12",
        selectedDomain: command.action === "cloud-select" ? "developer.aos-dev.test" : "aoscloud.io",
        applied: command.action === "cloud-select" } };
    const job: DemoJob = { id, action: command.action, state: failure ? "BLOCKED" : "COMPLETED", startedAt: "now", progress: [], results: [result] };
    state.jobs.push(job);
    return job;
  }) };
  render(<div className="browser-workspace"><PresenterControls port={port}><CloudConnectionPanel /></PresenterControls></div>);
  return port;
}

it("previews locally once, then confirms the exact preview without a browser credential or URL", async () => {
  const port = setup();
  await screen.findByText("developer.aos-dev.test");
  expect(port.submit).toHaveBeenCalledTimes(1);
  expect(port.submit.mock.calls[0]?.[0]).toEqual({ action: "cloud-inspect" });
  fireEvent.click(screen.getByRole("button", { name: "Use this Cloud" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("developer.aos-dev.test");
  expect(screen.getByRole("dialog")).toHaveTextContent("No provisioning, publication or VM restart");
  fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
  expect(port.submit).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Use this Cloud" }));
  fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Use this Cloud" }));
  await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(2));
  expect(port.submit.mock.calls[1]?.[0]).toEqual({ action: "cloud-select", selectionId: port.submit.mock.calls[0]?.[1] });
  expect(document.querySelector('input[type="file"]')).toBeNull();
});

it("a failed preview cannot enable selection; native chooser receives no path from the browser", async () => {
  const port = setup(true);
  await screen.findByRole("alert");
  expect(screen.getByRole("button", { name: "Use this Cloud" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Choose certificate…" }));
  await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(2));
  expect(port.submit.mock.calls[1]?.[0]).toEqual({ action: "cloud-choose" });
});

it("only checks on request and confirms preparation without paths or owner IDs", async () => {
  const port = setup();
  await screen.findByText("developer.aos-dev.test");
  expect(port.submit).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Check Cloud setup" }));
  await screen.findByText("Single-node configuration required", { exact: false });
  expect(port.submit.mock.calls[1]?.[0]).toEqual({ action: "cloud-check" });
  expect(screen.queryByRole("dialog")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Prepare Test Cloud" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("No Unit provisioning, package upload, Subject assignment or Production change");
  expect(port.submit).toHaveBeenCalledTimes(2);
  fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Prepare Test Cloud" }));
  await waitFor(() => expect(port.submit).toHaveBeenCalledTimes(3));
  expect(port.submit.mock.calls[2]?.[0]).toEqual({ action: "cloud-prepare" });
});

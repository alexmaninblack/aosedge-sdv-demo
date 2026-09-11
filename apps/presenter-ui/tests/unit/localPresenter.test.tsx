import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { LocalPresenterReadAdapter, composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";
import { createPresenterDependencies } from "../../src/app/composition/createPresenterDependencies";
import { PresenterReadModelProvider } from "../../src/app/state/PresenterReadModelProvider";
import { PresenterApp } from "../../src/app/PresenterApp";
import { SharedHeader } from "../../src/app/SharedHeader";
import { projectCloudPlatform } from "../../src/domain";
import type { PlatformCloudObservation } from "../../src/domain";
import userEvent from "@testing-library/user-event";

const data = { mode: "LOCAL_READ_ONLY", observedAt: "2026-09-06T12:00:00Z", available: true,
  vehicles: { test: { state: "CURRENT", reason: null, process: "NOT_CREATED", imageVersion: null, overlayExists: false },
    production: { state: "CURRENT", reason: null, process: "NOT_CREATED", imageVersion: null, overlayExists: false } },
  images: [{ selector: "factory-31/arm64", version: "factory-31", architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] }],
  source: { state: "NOT_PREPARED", currentVehicle: null }, access: { "oem-delivery": { present: true, state: "NOT_REQUESTED" } } };

afterEach(() => vi.unstubAllGlobals());

describe("local composition preview", () => {
  const cloud: PlatformCloudObservation = { state: "CURRENT", observedAt: new Date().toISOString(), reason: null, value: {
    target: "test", source: "Aos Cloud", online: "Online", lifecycle: "provisioned", installedVersion: "15.0.0",
    pendingVersion: null, updateStatus: "installed", latestPublishedVersion: "15.0.0", releases: [],
    runtimeState: "NOT_REPORTED_BY_CLOUD", dataReadiness: "NOT_REPORTED_BY_CLOUD" } };
  it("reads Cloud on Platform entry and reentry, never a guest endpoint", async () => {
    const snapshot = composeLocalSnapshot(data);
    const readPlatform = vi.fn().mockResolvedValue(cloud);
    const dependencies = { readPort: { read: async () => snapshot, subscribe: () => () => {}, readPlatform } };
    render(<PresenterReadModelProvider dependencies={dependencies}><PresenterApp /></PresenterReadModelProvider>);
    await screen.findByTestId("studio-workspace");
    // The architecture's Cloud card is also a visible subscriber.
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /Platform Team/ }));
    expect(await screen.findByText("VDP 15.0.0 · Cloud installed")).toBeInTheDocument();
    expect(readPlatform).toHaveBeenCalledTimes(2);
    expect(screen.queryByText("Refresh running Test VDP")).not.toBeInTheDocument();
    expect(screen.queryByText("Read Test VDP logs")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Brake Team/ }));
    expect(readPlatform).toHaveBeenCalledTimes(3);
    await user.click(screen.getByRole("button", { name: /Platform Team/ }));
    expect(readPlatform).toHaveBeenCalledTimes(4);
  });
  it("does not infer running, READY or functional profile from Cloud installed", () => {
    const team = projectCloudPlatform(composeLocalSnapshot(data).teams.platform, cloud);
    expect(team.evidenceBody).toContain("no direct VM probe");
    expect(team.productStatus).not.toMatch(/READY|Running|v3/);
    expect(team.releases.every((release) => release.status === "Content profile reference")).toBe(true);
    const stale = projectCloudPlatform(team, { ...cloud, state: "STALE" });
    expect(stale.backendStatus).toBe("STALE");
    expect(stale.productStatus).toBe("VDP 15.0.0 · Cloud installed · last known");
  });
  it("deduplicates the in-flight fixed Cloud-only read and sanitizes failure", async () => {
    const request = vi.fn().mockResolvedValue({ ok: true, json: async () => cloud });
    vi.stubGlobal("fetch", request);
    const adapter = new LocalPresenterReadAdapter();
    await Promise.all([adapter.readPlatform(), adapter.readPlatform()]);
    expect(request).toHaveBeenCalledTimes(1);
    expect(request.mock.calls[0][0]).toBe("/api/presenter/platform");
    request.mockRejectedValue(new Error("private"));
    expect(await adapter.readPlatform()).toEqual({ state: "UNAVAILABLE", value: null, observedAt: null, reason: "AOS_CLOUD_STATE_UNAVAILABLE" });
  });
  it.each(["test", "production"])("shows the accepted %s assignment without inventing a live probe", (role) => {
    const snapshot = composeLocalSnapshot({ ...data, source: { state: "SELECTED_NOT_PROBED", selectedVehicle: role, currentVehicle: null } });
    expect(snapshot.vehicle.value).toBe(role);
    expect(snapshot.vehicle.state).toBe("CURRENT");
    render(<SharedHeader snapshot={snapshot} perspective="global" onNavigate={() => {}} />);
    expect(screen.getByText(`Current vehicle · ${role === "test" ? "Test" : "Production"} Vehicle`)).toBeInTheDocument();
    expect(screen.queryByText("Connection not rechecked")).not.toBeInTheDocument();
    expect(screen.queryByText("Connection confirmed")).not.toBeInTheDocument();
  });
  it("keeps connection diagnostics out of the header even after a confirmed selection", () => {
    const snapshot = composeLocalSnapshot({ ...data, source: { state: "CONNECTED", selectedVehicle: "test", currentVehicle: "test" } });
    render(<SharedHeader snapshot={snapshot} perspective="global" onNavigate={() => {}} />);
    expect(screen.queryByText("Connection confirmed")).not.toBeInTheDocument();
    expect(snapshot.vehicle.value).toBe("test");
  });
  it("shows only the demo title, assignment and team names without subtitles", () => {
    const snapshot = composeLocalSnapshot(data);
    const { container } = render(<SharedHeader snapshot={snapshot} perspective="global" onNavigate={() => {}} />);
    expect(screen.getByRole("button", { name: "AosEdge Software Evolution Demo" })).toBeInTheDocument();
    for (const team of Object.values(snapshot.teams)) expect(screen.getByText(team.name)).toBeInTheDocument();
    expect(screen.queryByText("Open the run-wide Demo Lifecycle")).not.toBeInTheDocument();
    expect(screen.queryByText("Test Vehicle pass")).not.toBeInTheDocument();
    expect(screen.queryByText("Not connected")).not.toBeInTheDocument();
    expect(container.querySelector("header small")).toBeNull();
  });
  it("updates assignment from Demo Control across handover, reload and stop without making requests", () => {
    const request = vi.fn();
    vi.stubGlobal("fetch", request);
    const snapshot = (source: typeof data.source & { selectedVehicle?: string }) => composeLocalSnapshot({ ...data, source });
    const props = { perspective: "global" as const, onNavigate: () => {} };
    const { rerender } = render(<SharedHeader {...props} snapshot={snapshot({ state: "SELECTED_NOT_PROBED", selectedVehicle: "test", currentVehicle: null })} />);
    expect(screen.getByText("Current vehicle · Test Vehicle")).toBeInTheDocument();
    rerender(<SharedHeader {...props} snapshot={snapshot({ state: "SELECTED_NOT_PROBED", selectedVehicle: "production", currentVehicle: null })} />);
    expect(screen.getByText("Current vehicle · Production Vehicle")).toBeInTheDocument();
    rerender(<SharedHeader {...props} snapshot={snapshot({ state: "STOPPED", currentVehicle: null })} />);
    expect(screen.getByText("Current vehicle · Not assigned")).toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });
  it.each([
    { state: "UNKNOWN", selectedVehicle: "test", currentVehicle: null },
    { state: "SELECTED_NOT_PROBED", selectedVehicle: "test", currentVehicle: null, reason: "SOURCE_LIVE_ASSIGNMENT_CONTRADICTORY" },
    { state: "CONNECTED", selectedVehicle: "test", currentVehicle: "production" },
    { state: "SELECTED_NOT_PROBED", selectedVehicle: "invalid", currentVehicle: null },
    { state: "UNKNOWN", selectedVehicle: null, currentVehicle: null },
  ])("does not turn unknown/conflicting source state into a current vehicle: %j", (source) => {
    const snapshot = composeLocalSnapshot({ ...data, source });
    expect(snapshot.vehicle.value).toBe("unavailable");
    expect(snapshot.vehicle.state).toBe("UNAVAILABLE");
  });
  it("defaults to the live local adapter, with fixtures selected only explicitly", async () => {
    expect(createPresenterDependencies({ search: "" }).readPort).toBeInstanceOf(LocalPresenterReadAdapter);
    expect((await createPresenterDependencies({ search: "?fixture=ready" }).readPort.read()).fixtureId).toBe("ready");
  });
  it("keeps local observations separate from Cloud, qualification and release readiness", () => {
    const snapshot = composeLocalSnapshot(data);
    expect(snapshot.vehicle.value).toBe("not-assigned");
    expect(snapshot.vehicle.source.fixture).toBe(false);
    expect(snapshot.global.provisioned).toBe(false);
    expect(snapshot.global.qualification.value?.status).toBe("NOT_QUALIFIED");
    expect(snapshot.teams.platform.releases).toHaveLength(3);
    for (const release of snapshot.teams.platform.releases) {
      expect(release.status).toBe("Not observed");
      expect(release.stages).toHaveLength(5);
      expect(release.stages.every((stage) => !stage.action)).toBe(true);
      expect(release.stages[3].explanation).toContain("Production FOTA is unavailable");
    }
    expect(snapshot.teams.brake.releases).toEqual([]);
    expect(snapshot.teams.tire.releases).toEqual([]);
  });
  it("reads one fixed same-origin route and fails without retaining fixture greens", async () => {
    const request = vi.fn().mockResolvedValue({ ok: true, json: async () => data });
    vi.stubGlobal("fetch", request);
    const adapter = new LocalPresenterReadAdapter();
    expect((await adapter.read()).localDemo?.available).toBe(true);
    expect(request.mock.calls[0][0]).toBe("/api/presenter/snapshot");
    request.mockRejectedValue(new Error("no connection"));
    const failed = await adapter.read();
    expect(failed.localDemo?.available).toBe(false);
    expect(failed.vehicle.value).toBe("unavailable");
    expect(failed.global.manufactured).toBe(false);
    expect(failed.fixtureId).toBe("local");
  });
  it("renders the catalog and Test-only Studio; Production stays deferred and protected actions cannot submit", async () => {
    const snapshot = composeLocalSnapshot(data);
    const dependencies = { readPort: { read: async () => snapshot, subscribe: () => () => {} } };
    render(<PresenterReadModelProvider dependencies={dependencies}><PresenterApp /></PresenterReadModelProvider>);
    expect(await screen.findByTestId("studio-workspace")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Factory image" })).toHaveValue("factory-31/arm64");
    expect(screen.getByRole("option", { name: "Production · Deferred" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Create controller" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Finish demo" })).toBeDisabled();
    expect(screen.queryByText("FIXTURE ONLY")).not.toBeInTheDocument();
  });
});

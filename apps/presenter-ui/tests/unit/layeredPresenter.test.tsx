// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { composeLocalSnapshot } from "../../src/adapters/local/LocalPresenterReadAdapter";
import { StudioWorkspace } from "../../src/app/StudioWorkspace";
import { selectedPackageStatus } from "../../src/domain/studioPresentation";
import { BackendEvidence } from "../../src/features/service-team/BackendEvidence";
import { binding } from "./backendFixture";

const cloud = vi.hoisted(() => ({ observation: null as any, loading: false, refresh: vi.fn(), enter: () => () => {} }));
const controls = vi.hoisted(() => ({ blocked: false, readBlocked: false, blockReason: null, request: vi.fn(), session: { jobs: [], active: null, cloudDomain: "aoscloud.io" } as any }));
vi.mock("../../src/app/state/PresenterReadModelProvider", () => ({ usePlatformObservation: () => cloud }));
vi.mock("../../src/app/state/PresenterControls", async original => ({ ...await original<any>(), usePresenterControls: () => controls }));
afterEach(() => { cleanup(); vi.clearAllMocks(); cloud.observation = null; });
const local: any = { mode: "LOCAL_READ_ONLY", observedAt: new Date().toISOString(), runId: "test-run", registrationComplete: true,
  lifecycle: { action: "create", state: "COMPLETED" }, access: { "oem-delivery": { present: true }, "service-provider": { present: true } },
  images: [{ selector: "base/arm64", version: "Supplied base", architecture: "arm64", state: "METADATA_AVAILABLE", problems: [] }],
  vehicles: { test: { state: "CURRENT", overlayExists: true, process: "RUNNING", imageVersion: "Supplied base" }, production: { state: "NOT_APPLICABLE" } },
  source: { state: "CONNECTED", currentVehicle: "test", selectedVehicle: "test" } };
function view() { return render(<StudioWorkspace snapshot={composeLocalSnapshot(local)} perspective="global" navigate={vi.fn()} />); }

test("Layered uses one execution boundary, independent peer services, shared VDP and runtime base", () => {
  const { container } = view();
  const controller = screen.getByRole("region", { name: "ARM64 virtual controller" });
  expect(controller.querySelectorAll(".studio-service-slots > article")).toHaveLength(2);
  expect(controller.querySelector(".studio-data-dependencies")).toHaveAccessibleName("Both independent services use Vehicle Data Platform");
  expect(controller.querySelector(".studio-vdp-slot")).toBeTruthy();
  expect(controller).toHaveTextContent("Factory base · Linux + AosCore");
  expect(controller).not.toHaveTextContent("AosCore running");
  expect(container.querySelectorAll(".studio-wires")).toHaveLength(0);
  expect(controller.contains(container.querySelector(".studio-backends"))).toBe(false);
  const platform = screen.getByRole("button", { name: "Platform Team" });
  const vdp = screen.getByRole("button", { name: "Vehicle Data Platform installed details" });
  expect(platform.querySelector(".b2-component")).toBeTruthy();
  expect(vdp.querySelector(".b2-component")).toBeTruthy();
  expect(controller.querySelector("h2 .b2-platform")).toBeTruthy();
  expect(controls.request).not.toHaveBeenCalled();
});

test("opening ordinary Cloud access has no automatic operation or certificate picker", () => {
  view(); fireEvent.click(screen.getByRole("button", { name: "Demo controls" }));
  fireEvent.click(screen.getByRole("button", { name: "Advanced settings" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("aoscloud.io");
  expect(screen.getByRole("dialog")).toHaveTextContent("Open AosEdge SDV Lab Setup");
  expect(screen.queryByRole("button", { name: "Choose OEM certificate…" })).toBeNull();
  expect(controls.request).not.toHaveBeenCalled();
});

const selected = { prepared: true, submitted: true, stage: "READY", installed: false, selectedVersion: "95.0.0", installedVersion: "98.0.0", installedCurrent: true, pendingVersion: null, activePublication: false, assignmentAbsent: false };
test("a published selection different from installed is not an inferred downgrade or pending request", () => {
  expect(selectedPackageStatus(selected)).toEqual({ title: "Published", detail: "This Test currently runs release 98.0.0. This selection is not an installation request." });
});
test("even a higher selected number without exact pending evidence is not waiting for installation", () => {
  expect(selectedPackageStatus({ ...selected, selectedVersion: "100.0.0" }).title).toBe("Published");
});
test("only the exact pending target gets a pending selected-package label", () => {
  expect(selectedPackageStatus({ ...selected, pendingVersion: "96.0.0" }).title).toBe("Published");
  expect(selectedPackageStatus({ ...selected, pendingVersion: "95.0.0" }).title).toBe("Published · delivery pending");
});
test("stale installed reports are qualified, not silently absent", () => {
  expect(selectedPackageStatus({ ...selected, installedCurrent: false }).detail).toContain("last reported release 98.0.0");
});
test("active publication takes precedence over prepared package guidance without implying installation", () => {
  const status=selectedPackageStatus({ ...selected, stage: null, activePublication: true });
  expect(status.title).toBe("Publication in progress");expect(status.detail).toContain("Submitted once");
});

test("bounded backend history filters releases without deleting data; child details are inline", () => {
  const rows=["7.0.0","6.0.0"].map((serviceVersion,index)=>({backendReceivedAt:`2026-10-26T10:4${index}:00.000Z`,deliveryState:"DURABLY_RECEIVED",message:{messageType:"BRAKE_HEALTH_ASSESSMENT",serviceVersion,content:{currentBand:"GOOD"}}}));
  const observation: any={busy:false,error:false,refresh:vi.fn(),data:{observedAt:"2026-10-26T10:42:00.000Z",observations:{mockData:{state:"OBSERVED",data:{counts:[{count:2}],records:rows}}}}};
  render(<BackendEvidence team="brake" expectedVersion="7.0.0" binding={binding} observation={observation} />);
  fireEvent.click(screen.getByRole("button",{name:"Records"}));
  expect(screen.getByRole("combobox",{name:"Service release"})).toHaveValue("current");
  expect(screen.getAllByRole("button",{name:/Brake condition assessment/})).toHaveLength(1);
  fireEvent.change(screen.getByRole("combobox",{name:"Service release"}),{target:{value:"earlier"}});
  const record=screen.getByRole("button",{name:/Brake condition assessment/});
  expect(record).toHaveTextContent("6.0.0");fireEvent.click(record);
  expect(screen.queryByRole("dialog")).toBeNull();
  fireEvent.click(screen.getByRole("button",{name:"← Back to Brake backend"}));
  expect(screen.getByRole("combobox",{name:"Service release"})).toHaveValue("earlier");
  expect(rows).toHaveLength(2);
});

test("Cloud child detail shows one dialog and Back returns to the preserved parent", () => {
  cloud.observation={state:"CURRENT",observedAt:new Date().toISOString(),bindingKey:"test-run:unit",value:{online:"ONLINE",installedVersion:"7.0.0",inventory:{unitId:"unit",components:{state:"CURRENT",value:[{type:"demo-vehicle-data-provider",reported_component_id:"vdp",installed_component:{version:"7.0.0"}}]},services:{state:"CURRENT",value:[]}}}};
  view();fireEvent.click(screen.getByRole("button",{name:"Aos Cloud Unit monitoring"}));
  fireEvent.click(within(screen.getByRole("dialog")).getByRole("button",{name:/Vehicle Data Platform/}));
  expect(screen.getAllByRole("dialog")).toHaveLength(1);
  fireEvent.click(screen.getByRole("button",{name:"← Back"}));
  expect(screen.getAllByRole("dialog")).toHaveLength(1);
  expect(screen.getByRole("dialog")).toHaveAccessibleName("Cloud monitoring");
});

test("Back restores the same history record after a background insertion, not its former row number", () => {
  const rows=["2026-10-26T10:42:00.000Z","2026-10-26T10:41:00.000Z"].map(backendReceivedAt=>({backendReceivedAt,deliveryState:"DURABLY_RECEIVED",message:{messageType:"BRAKE_HEALTH_ASSESSMENT",serviceVersion:"7.0.0",content:{currentBand:"GOOD"}}}));
  const observation: any={busy:false,error:false,refresh:vi.fn(),data:{observedAt:"2026-10-26T10:42:00.000Z",observations:{mockData:{state:"OBSERVED",data:{counts:[{count:2}],records:rows}}}}};
  const view=render(<BackendEvidence team="brake" expectedVersion="7.0.0" binding={binding} observation={observation} />);
  fireEvent.click(screen.getByRole("button",{name:"Records"}));
  fireEvent.click(screen.getAllByRole("button",{name:/Brake condition assessment/})[1]);
  rows.unshift({...rows[0],backendReceivedAt:"2026-10-26T10:43:00.000Z"});
  view.rerender(<BackendEvidence team="brake" expectedVersion="7.0.0" binding={binding} observation={observation} />);
  fireEvent.click(screen.getByRole("button",{name:"← Back to Brake backend"}));
  expect(screen.getAllByRole("button",{name:/Brake condition assessment/})[2]).toHaveFocus();
});

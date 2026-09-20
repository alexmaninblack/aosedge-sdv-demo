// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { useEffect, useState } from "react";
import { readBackendObservation } from "../../adapters/local/LocalPresenterReadAdapter";
import { productRows, productSourceTime, type ProductRow, type Resource } from "./backendProduct";
import { selectProduct, sameInstance, type BackendBinding, type ResetCommand } from "./backendSelection";
import { functionPage, selectFunction } from "./functionObservation";
import { emptyResultGuidance } from "./emptyResultGuidance";
import { recordingLabel } from "./windowPresentation";

export type Team = "brake" | "tire";
export type RecordRow = ProductRow;
export type BackendData = { source: "DEMO_MOCK" | "VEHICLE_DATA"; vehicleTelemetry: boolean; unitSystemUid: string;
  counts: { kind?: string; message_type?: string; count: number }[]; records: RecordRow[] };
export type BackendObservation = { state: string; team: Team; source: "REAL_BACKEND_HTTP"; observedAt: string; recordsObservedAt?: string;
  partialResources?: string[]; productResources?: Record<string, Resource>;
  observations: { readiness?: { state: string; reason?: string; data?: { ready?: boolean; reason?: string } };
    mockData?: { state: string; reason?: string; data?: BackendData };
    functionObservations?: Resource;
    demoReset?: { state: string; data?: { schemaVersion: number; unitSystemUid: string; connected: boolean;
      command: null | ResetCommand } } } };

export const recordObject = (value: unknown): Record<string, unknown> => value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
export const readable = (value: unknown) => typeof value === "string" ? value.replaceAll("_", " ") : typeof value === "number" ? String(value) : "Not reported";

/** Reset commands only move forward. A delayed projection must not revive an
 * old command or turn a terminal acknowledgement back into PENDING. */
export function monotonicReset(incoming: BackendObservation["observations"]["demoReset"], prior: BackendObservation["observations"]["demoReset"]) {
  if (!incoming?.data) return { state: "UNAVAILABLE", data: prior?.data };
  const next = incoming.data.command, old = prior?.data?.command;
  if (old && (!next || Date.parse(next.issuedAt) < Date.parse(old.issuedAt)
      || next.commandId === old.commandId && old.state !== "PENDING" && next.state === "PENDING")) {
    return { ...incoming, data: { ...incoming.data, command: old } };
  }
  return incoming;
}

/** Preserve each resource's read outcome. History/reset failure cannot invalidate a valid function report. */
export function mergeProductResources(value: BackendObservation, prior: BackendObservation | null, team: Team, uid: string) {
  const resources = value.observations as unknown as Record<string, Resource>;
  functionPage(resources.functionObservations, team, uid);
  productRows(resources, uid); // Reject foreign/malformed supplied rows, even on a partial response.
  const names = team === "brake" ? ["productData", "assessments", "events", "advisories"] : ["assessments", "events", "advisories", "functionStatus"];
  const productResources = Object.fromEntries(names.map(name => [name, resources[name]?.state === "OBSERVED" && resources[name]?.data
    ? resources[name] : { state: "UNAVAILABLE", data: prior?.productResources?.[name]?.data }]));
  const current = names.every(name => productResources[name]?.state === "OBSERVED");
  const records = productRows(productResources, uid);
  return { ...value, productResources,
    partialResources: [...new Set([...Object.keys(resources), ...names, "demoReset", "functionObservations"])]
      .filter(name => resources[name]?.state !== "OBSERVED" || !resources[name]?.data),
    recordsObservedAt: current ? value.observedAt : prior?.recordsObservedAt,
    observations: { ...value.observations, mockData: { state: current ? "OBSERVED" : "UNAVAILABLE", data: {
      source: "VEHICLE_DATA" as const, vehicleTelemetry: true, unitSystemUid: uid, records, counts: [{ count: records.length }],
    } } } };
}

/** One observer per team/current Test, shared by its summary and detail dialog. */
export function useBackendObservation(team: Team, unitSystemUid?: string, enabled = true, mockMode = false, scope = "") {
  const identity = `${scope}:${team}:${unitSystemUid ?? ""}:${mockMode}`;
  const [stored, setStored] = useState<{ identity: string; data: BackendObservation | null; error: boolean }>({ identity, data: null, error: false });
  const [busy, setBusy] = useState(false);
  const [generation, setGeneration] = useState(0);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    if (!enabled || !unitSystemUid) { setBusy(false); return; }
    const read = async () => {
      if (!active) return;
      if (document.visibilityState !== "hidden") {
        setBusy(true);
        try {
          const value = await readBackendObservation(team, controller.signal) as BackendObservation;
          const suppliedMock = value.observations?.mockData?.data;
          const reset = value.observations?.demoReset?.data;
          if (reset && (reset.schemaVersion !== 1 || reset.unitSystemUid !== unitSystemUid || typeof reset.connected !== "boolean"
              || (reset.command && (reset.command.unitSystemUid !== unitSystemUid || !["PENDING", "CLEARED", "EXPIRED", "FAILED", "REJECTED"].includes(reset.command.state))))) throw new Error("BACKEND_RESET_SCOPE_MISMATCH");
          if (value.team !== team || value.source !== "REAL_BACKEND_HTTP" || !value.observations
              || (suppliedMock && (suppliedMock.source !== "DEMO_MOCK" || suppliedMock.vehicleTelemetry !== false
                || suppliedMock.unitSystemUid !== unitSystemUid || !Array.isArray(suppliedMock.records) || !Array.isArray(suppliedMock.counts)
                || suppliedMock.records.some(row => row.message.unitSystemUid !== unitSystemUid)))) throw new Error("BACKEND_SCOPE_MISMATCH");
          // Validate outside the React state updater so failures take the fail-closed path.
          if (!mockMode) mergeProductResources(value, null, team, unitSystemUid);
          if (active) setStored(previous => {
            const prior = previous.identity === identity ? previous.data : null;
            if (prior && Date.parse(value.observedAt) < Date.parse(prior.observedAt)) return previous;
            const next = mockMode ? value : mergeProductResources(value, prior, team, unitSystemUid);
            return { identity, error: false, data: { ...next,
              recordsObservedAt: value.observations.mockData?.state === "OBSERVED" && value.observations.mockData.data ? value.observedAt : prior?.recordsObservedAt,
              ...(!mockMode ? { recordsObservedAt: next.recordsObservedAt } : {}),
              observations: { ...next.observations,
                demoReset: monotonicReset(value.observations.demoReset, prior?.observations.demoReset),
                functionObservations: value.observations.functionObservations?.data ? value.observations.functionObservations
                  : { state: "UNAVAILABLE", data: prior?.observations.functionObservations?.data },
                mockData: next.observations.mockData?.data ? next.observations.mockData
                : { ...next.observations.mockData, state: next.observations.mockData?.state ?? "UNAVAILABLE", data: prior?.observations.mockData?.data } } } };
          });
        } catch { if (active) setStored(previous => ({ identity, error: true, data: previous.identity === identity ? previous.data : null })); }
        finally { if (active) setBusy(false); }
      }
      if (active) timer = setTimeout(read, 5000);
    };
    void read();
    return () => { active = false; controller.abort(); clearTimeout(timer); };
  }, [team, unitSystemUid, identity, generation, enabled, mockMode]);
  return { data: stored.identity === identity ? stored.data : null, error: stored.identity === identity && stored.error,
    busy, refresh: () => setGeneration(value => value + 1) };
}
export type BackendModel = ReturnType<typeof useBackendObservation>;

export function backendSummary(model: BackendModel, team: Team, version?: string, binding?: BackendBinding) {
  const payload = model.data?.observations.mockData;
  const reset = model.data?.observations.demoReset;
  const productsAvailable = !model.error && payload?.state === "OBSERVED" && payload.data?.source === "VEHICLE_DATA";
  const available = productsAvailable && reset?.state === "OBSERVED";
  const command = reset?.data?.command;
  const selected = selectProduct(payload?.data?.records ?? [], team, version, binding, command);
  const { rows } = selected;
  const functionResource = model.data?.observations.functionObservations;
  const functional = selectFunction(model.error && functionResource ? { ...functionResource, state: "UNAVAILABLE" } : functionResource, team, binding);
  const ambiguous = selected.ambiguous || functional.state === "AMBIGUOUS" || !!(selected.result && functional.item
    && !sameInstance(selected.result.message.serviceInstance, functional.item.message.serviceInstance));
  const result = ambiguous ? undefined : selected.result;
  const integrityConflict = result?.deliveryState === "CONFLICT";
  const guidance = emptyResultGuidance(ambiguous ? { state: "AMBIGUOUS" } : functional, team);
  const content = recordObject(result?.message.content);
  const proof = available && reset?.state === "OBSERVED" && !ambiguous ? selected.proof : undefined;
  const lastKnown = !productsAvailable || binding?.current === false;
  const status = !version ? "Release not observed" : integrityConflict ? `Result conflict${lastKnown ? " · last known" : ""}` : lastKnown ? "Last known / incomplete" : !available ? "Reset state not observed"
    : selected.reset.state === "PENDING" ? "Resetting" : selected.reset.state === "UNCERTAIN" ? "Reset needs attention"
    : ambiguous ? "Instance not confirmed" : result ? "Result received" : guidance.status;
  const contact = model.error || reset?.state !== "OBSERVED" ? "Not observed" : reset.data?.connected ? "Recent" : "Not recent";
  // Capability explanation, not an assertion about a retained condition or a
  // live warning. Only native telemetry establishes the current advisory.
  const continuityNote = team === "brake" && binding?.profile === "v3" && available && !lastKnown && !ambiguous && !result
    && functional.state === "CURRENT" && functional.item?.message.content.input.state === "RECEIVING"
    && ["NONE", "HISTORICAL"].includes(selected.reset.state)
    ? "Brake V3 can continue advisory from a retained condition before a new assessment. Check vehicle telemetry for the current advisory."
    : undefined;
  return { available, productsAvailable, lastKnown, rows, result, content, proof, status, integrityConflict, reset: command, resetState: selected.reset.state, functional, continuityNote,
    guidance: integrityConflict ? "Conflicting content for this record. Inspect Records; this is not a confirmed result."
      : model.error ? "Backend read failed. Earlier records do not confirm live input."
      : !model.data ? "Waiting for the first backend observation. No product history has been confirmed."
      : !productsAvailable ? "Product history is incomplete. Input and activity have independent observation states."
      : reset?.state !== "OBSERVED" ? "Reset state is not observed. The retained result cannot yet confirm this demo step."
      : selected.reset.state === "PENDING" ? "Reset is pending. Wait for confirmation before starting the next demonstration drive."
      : selected.reset.state === "UNCERTAIN" ? "Reset outcome is unconfirmed. Earlier results remain in Records."
      : guidance.text,
    contact,
    title: integrityConflict ? "Result not trusted" : result ? result.message.messageType === "WINDOW_COMPLETION" ? recordingLabel(content.status)
      : readable(content.currentBand ?? content.condition ?? content.status ?? result.message.messageType)
      : selected.reset.state === "CLEARED" ? "No new result after reset" : selected.reset.state === "PENDING" ? "Reset pending"
        : selected.reset.state === "UNCERTAIN" ? "Reset outcome unconfirmed"
        : version ? "No current-release result" : "Waiting for service",
    observedAt: model.data?.observedAt, sourceAt: result ? productSourceTime(result) : undefined,
    receivedAt: result?.backendReceivedAt };
}

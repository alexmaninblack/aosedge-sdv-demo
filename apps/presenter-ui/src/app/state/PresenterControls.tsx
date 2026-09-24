import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { DemoCommand, DemoJob, OperationSession, PresenterCommandPort } from "../../domain/presenterCommandPort";
import { Modal } from "../../shared/components/Modal";
import { createPortal } from "react-dom";
import { usePlatformObservation } from "./PresenterReadModelProvider";

export const actionLabels: Record<DemoCommand["action"], string> = {
  "workspace-restore": "Restore window layout",
  "cloud-inspect": "Read OEM certificate", "cloud-choose": "Choose OEM certificate", "cloud-select": "Use this Cloud",
  "cloud-check": "Check Cloud setup", "cloud-prepare": "Prepare Test Cloud",
  "backend-reset": "Reset Driver Advisory",
  publish: "Sign & publish VDP", "service-prepare": "Prepare service", "service-publish": "Sign & publish service",
  "service-observe": "Refresh service publication", "service-assign": "Deploy service to Test",
  "prepare-demo": "Prepare demo",
  create: "Create controller", "start-vms": "Start Test controller", "stop-vms": "Stop Test controller", provision: "Provision Test Vehicle",
  "start-simulation": "Start simulator", "stop-simulation": "Stop simulator", "connect-test": "Connect in Manual", "reconnect-test": "Reconnect Test Vehicle", park: "Park demo", resume: "Resume demo", reset: "Finish demo",
  prepare: "Prepare VDP", unpack: "Unpack VDP", sign: "Sign VDP", upload: "Publish VDP to Aos Cloud", approve: "Authorize Test VDP deployment",
  inspect: "Inspect VDP", verify: "Verify VDP signature", "cloud-status": "Read Cloud release state", "observe-test": "Read Test VDP state", "test-logs": "Read Test VDP logs", "cloud-access": "Check OEM and Service Provider access",
};
const reads = new Set<DemoCommand["action"]>(["inspect", "verify", "cloud-status", "observe-test", "test-logs", "cloud-access", "service-observe", "cloud-inspect", "cloud-choose", "cloud-check"]);
export function preparationRecovery(job?: DemoJob | null) {
  if (!job || !["prepare", "service-prepare"].includes(job.action) || !["BLOCKED", "FAILED"].includes(job.state)) return null;
  const reason = [job.reason, ...job.results.map(result => result.message)].join(" ");
  if (reason.includes("SERVICE_COMMITTED_SOURCE_REQUIRED")) return "Service source has uncommitted changes. Engineering must review and checkpoint it, then build the selected profile. Retrying Prepare unchanged cannot succeed; the current Test is preserved.";
  if (reason.includes("SERVICE_BUILD_REQUIRED")) return "The selected service profile has no compiled package for its source checkpoint. Engineering must build it before the demo; then use Prepare again. No upload or assignment has started.";
  return null;
}
export type ResetSubmission = { id: string; sessionId: string; scope?: string; phase: "SUBMITTING" | "ACCEPTED" | "UNKNOWN" | "REJECTED" };
interface Controls { session: OperationSession | null; blocked: boolean; readBlocked: boolean; blockReason: string | null; error: string | null; resetSubmissions?: Partial<Record<"brake" | "tire", ResetSubmission>>; request: (command: DemoCommand, resetScope?: string) => void }
const unavailable: Controls = { session: null, blocked: true, readBlocked: true, blockReason: "Demo Control unavailable", error: null, request: () => {} };
const Context = createContext<Controls>(unavailable);
export const usePresenterControls = () => useContext(Context);

export function PresenterControls({ port, children }: { port?: PresenterCommandPort; children: ReactNode }) {
  const [session, setSession] = useState<OperationSession | null>(null);
  const [reachable, setReachable] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<DemoCommand | null>(null);
  const submitting = useRef(false);
  const unresolved = useRef<{ id: string; sessionId: string; action: DemoCommand["action"] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [resetSubmissions, setResetSubmissions] = useState<Controls["resetSubmissions"]>({});
  const connectionFailure = useRef(false);
  const cloud = usePlatformObservation();
  const seenJobs = useRef<{ sessionId: string; terminal: Set<string> } | null>(null);
  useEffect(() => {
    if (!session) return;
    const terminal = new Set(session.jobs.filter((job) => !["ACCEPTED", "RUNNING"].includes(job.state)).map((job) => job.id));
    const previous = seenJobs.current;
    if (previous?.sessionId === session.sessionId && session.jobs.some((job) => terminal.has(job.id)
      && !previous.terminal.has(job.id) && !reads.has(job.action))) cloud.afterAction();
    seenJobs.current = { sessionId: session.sessionId, terminal };
  }, [session, cloud.afterAction]);
  useEffect(() => {
    if (!port) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      let delay = 5000;
      try {
        const value = await port.read();
        if (!active) return;
        setSession(value); setReachable(true);
        if (connectionFailure.current && !unresolved.current) setError(null);
        connectionFailure.current = false;
        if (unresolved.current) {
          const pending = unresolved.current;
          if (pending.sessionId === value.sessionId && (value.jobs.some((job) => job.id === pending.id) || value.recordedRequestIds?.includes(pending.id))) {
            unresolved.current = null; setError(null);
          } else setError(`Submission outcome unknown: ${actionLabels[pending.action]}. Request ${pending.id}. Do not repeat it; reconcile native state. Cloud reads remain available.`);
        }
        if (value.active || value.workspaceBusy || value.sourceRecoveryBusy || value.workspace?.retryPending) delay = 1000;
      } catch {
        if (active) { connectionFailure.current = true; setReachable(false); setError("Demo Control session unavailable. No action will be retried automatically."); }
      }
      if (active) timer = setTimeout(poll, delay);
    };
    void poll();
    return () => { active = false; clearTimeout(timer); };
  }, [port]);
  const recoveryUncertain = session?.sourceRecovery?.state === "FAILED" || session?.sourceRecovery?.state === "ATTEMPTED";
  const blocked = !port || !reachable || !session || Boolean(session.active) || Boolean(session.workspaceBusy) || Boolean(session.sourceRecoveryBusy) || recoveryUncertain || session.uncertain || busy || Boolean(unresolved.current);
  const readBlocked = !port || !reachable || !session || Boolean(session.active) || Boolean(session.workspaceBusy) || Boolean(session.sourceRecoveryBusy) || busy;
  const blockReason = !port || !reachable || !session ? "Demo Control unavailable; reconnect before changing the environment."
    : session.sourceRecoveryBusy ? "Restoring the controller connection after startup. The vehicle stays in Safe Stop; Autopilot will not resume automatically."
    : recoveryUncertain ? "Controller connection recovery is incomplete. Reconcile the existing attempt before changing the environment. Read-only observations remain available."
    : session.workspaceBusy ? "Restoring the desktop window layout; the demo continues running."
    : session.active || busy ? "An operation is in progress; open Trace for its current step."
    : session.uncertain || unresolved.current ? "An operation outcome is unknown. Finish cannot safely overlap it; inspect Trace and reconcile the original operation before continuing. Read-only observations remain available." : null;
  useEffect(() => {
    document.documentElement.dataset.submissionPending = String(busy || Boolean(unresolved.current) || Boolean(session?.uncertain));
    return () => { delete document.documentElement.dataset.submissionPending; };
  }, [busy, error, session]);
  const submit = useCallback(async (command: DemoCommand, resetScope?: string) => {
    if (!port || !session || (reads.has(command.action) ? readBlocked : blocked) || submitting.current) return;
    submitting.current = true; setBusy(true); setError(null); setConfirmation(null);
    const id = crypto.randomUUID();
    const resetPhase = (phase: ResetSubmission["phase"]) => {
      if (command.action === "backend-reset" && command.team) setResetSubmissions(previous => ({ ...previous, [command.team!]: { id, sessionId: session.sessionId, scope: resetScope, phase } }));
    };
    resetPhase("SUBMITTING");
    const originalPending = unresolved.current;
    if (!originalPending) unresolved.current = { id, sessionId: session.sessionId, action: command.action };
    try {
      const job = await port.submit(command, id, session.sessionId);
      resetPhase("ACCEPTED");
      if (!originalPending) unresolved.current = null;
      setSession((previous) => previous ? { ...previous, active: ["ACCEPTED", "RUNNING"].includes(job.state) ? id : null,
        jobs: [...previous.jobs.filter((item) => item.id !== id), job] } : previous);
    } catch (problem) {
      if (problem instanceof Error && problem.message === "REJECTED") {
        resetPhase("REJECTED");
        if (!originalPending) unresolved.current = null; setError("Operation rejected or another operation is running. Refresh the state before continuing.");
      } else { resetPhase("UNKNOWN"); setError("Submission response lost. Checking the original request; it will not be submitted again."); }
    } finally { submitting.current = false; setBusy(false); }
  }, [port, session, blocked, readBlocked]);
  const request = (command: DemoCommand, resetScope?: string) => {
    if (reads.has(command.action) ? readBlocked : blocked) return;
    if (reads.has(command.action) || command.action === "backend-reset") void submit(command, resetScope); else setConfirmation(command);
  };
  const close = useCallback(() => setConfirmation(null), []);
  const bundleRead = confirmation?.version ? [...(session?.jobs ?? [])].reverse().find((job) => job.cloudDomain === session?.cloudDomain && job.version === confirmation.version && job.results.some((result) => typeof result.facts.sha256 === "string")) : undefined;
  const bundleDigest = bundleRead?.results.find((result) => typeof result.facts.sha256 === "string")?.facts.sha256;
  const publishing = confirmation && ["upload", "publish", "service-publish"].includes(confirmation.action);
  const providerReceipt = confirmation?.release ? [...(session?.jobs ?? [])].reverse().find(job => job.cloudDomain === session?.cloudDomain
    && (job.release === confirmation.release || job.results.some(result => result.facts.releaseHandle === confirmation.release))
    && job.state === "COMPLETED" && job.results.some(result => typeof result.facts.serviceProviderId === "string")) : undefined;
  const providerId = providerReceipt?.results.find(result => typeof result.facts.serviceProviderId === "string")?.facts.serviceProviderId;
  return <Context.Provider value={{ session, blocked, readBlocked, blockReason, error, resetSubmissions, request }}>{children}
    {confirmation && createPortal(<Modal title={actionLabels[confirmation.action]} subtitle="Protected operation · explicit confirmation required" onClose={close}
      footer={<><button className="button" onClick={close}>Cancel</button><button className="button button-primary" disabled={blocked} onClick={() => void submit(confirmation)}>{actionLabels[confirmation.action]}</button></>}>
      <dl className="detail-grid"><dt>Actor</dt><dd>{confirmation.action === "service-assign" ? "OEM · dedicated service Subject" : confirmation.action.startsWith("service-") ? `${confirmation.team ?? confirmation.release?.split("/")[0] ?? "Service"} Team · configured Service Provider` : ["prepare", "unpack", "sign", "upload", "publish"].includes(confirmation.action) ? "Platform Team · selected session OEM" : "Demo operator · current owned environment"}</dd>
        <dt>Target</dt><dd>{confirmation.action === "workspace-restore" ? "Owned demo windows on this Mac's built-in display. No vehicle or Cloud changes." : ["upload", "publish", "service-publish"].includes(confirmation.action) ? "Configured Cloud publication context. Cloud distributes to eligible recipients; no Production membership or assignment is changed." : "Current Test Vehicle only. Production remains unchanged."}</dd>
        {publishing && <><dt>Selected Cloud</dt><dd>{session?.cloudDomain ?? "Not observed — execution must verify the configured destination"}</dd>
          <dt>Signing authority</dt><dd>{confirmation.action === "service-publish" ? "Selected session Service Provider certificate" : "Selected session OEM certificate"}</dd>
          {confirmation.action === "service-publish" && <><dt>Service Provider identity</dt><dd>{typeof providerId === "string" ? `${providerId} · last preparation/publication receipt` : "Not yet reported for this release; authenticated and checked during publication."}</dd></>}</>}
        {confirmation.image && <><dt>Factory image</dt><dd>{confirmation.image}</dd></>}
        {confirmation.action === "cloud-select" && <><dt>Cloud domain</dt><dd>{String(session?.jobs.find(job => job.id === confirmation.selectionId)?.results.at(-1)?.facts.domain ?? "Preview unavailable")}</dd><dt>Effect</dt><dd>Select the Cloud from this OEM certificate for Test. Keep Production unchanged. No provisioning, publication or VM restart. Finish a provisioned Test before switching Clouds. SP access requires a certificate for the same Cloud.</dd></>}
        {confirmation.profile && <><dt>Capability profile</dt><dd>{confirmation.profile}</dd></>}
        {confirmation.action === "backend-reset" && <><dt>Team</dt><dd>{confirmation.team === "brake" ? "Brake" : "Tire"}</dd><dt>Driver advisory reset</dt><dd>Reset this service's demo model and capture, then request CLEAR from the Gateway. Success requires a matching CLEARED acknowledgement. Preserve identity, releases, history and pending deliveries. This is not a repair or a healthy-vehicle assessment; the other service is unchanged.</dd></>}
        {confirmation.action === "cloud-prepare" && <><dt>Cloud setup</dt><dd>Authenticate the selected OEM and SP. Reuse Default fleet; create only a missing matching Factory model/configuration and Test verification set. Recheck existing settings; stop on conflicts or an unknown creation outcome. No Unit provisioning, package upload, Subject assignment or Production change.</dd></>}
        {confirmation.release && <><dt>Prepared release</dt><dd>{confirmation.release}</dd></>}
        {confirmation.serviceId && <><dt>Service identity</dt><dd>{confirmation.serviceId}</dd><dt>Assignment</dt><dd>Bind this service's retained Group Subject to current Test, preserving the peer service. No version or instance count is sent. No Safe Stop is required.</dd></>}
        {confirmation.action.startsWith("service-") && confirmation.action !== "service-assign" && <><dt>Data mode</dt><dd>{confirmation.action === "service-prepare" ? "Native KUKSA permissions and real-data bootstrap." : "The prepared package retains its declared data mode; see Package details."} Publication alone does not establish vehicle telemetry or advisory.</dd></>}
        {confirmation.action === "prepare-demo" && <><dt>Scenario</dt><dd>Create or continue this Test controller, start or reuse the local simulator without a Unit attachment, prepare, sign and publish VDP v1, then provision into Test Vehicles. After Cloud Online, enroll and connect the running Gateway in stationary Manual without restarting the simulator. Installation requires operator Safe Stop. No validation-batch approval is required for verification-set delivery.</dd></>}
        {confirmation.action === "provision" && <><dt>Gateway connection</dt><dd>After Cloud Online, enroll this Test identity and connect the running Gateway in stationary Manual. CARLA, Driving Control and the scene are preserved. Press Safe Stop separately to permit the VDP update.</dd></>}
        {confirmation.action === "workspace-restore" && <><dt>Window layout only</dt><dd>Place the owned Presenter, CARLA and Driving Control windows on the built-in display. Wait if the desktop is locked, then verify their positions. No VM, simulator, driving-mode, Cloud or scene restart.</dd></>}
        {confirmation.version && <><dt>Cloud release</dt><dd>{confirmation.version}{confirmation.profile ? ` · content ${confirmation.profile}` : ""}</dd></>}
        {confirmation.version && <><dt>Last observed bundle SHA</dt><dd>{bundleDigest ? String(bundleDigest) : "Not yet observed — inspect/sign the selected release to see its digest"}</dd></>}
        <dt>Checks</dt><dd>Demo Control checks current ownership, exact target, required access and prerequisites when executing. UI state is not permission to bypass them.</dd>
        <dt>Effect</dt><dd>{confirmation.action === "workspace-restore" ? "Restore and verify window positions. If locked, defer until unlock; retry window readiness at most three times. No lifecycle action is retried." : confirmation.action === "reset" ? "Retire the owned Test run through Demo Control: detach and stop, clear its Subject bindings, deprovision/delete the Unit, remove its local working files and scoped backend data. Permanent, no backup. Factory originals, published releases and release continuity remain. Production is untouched." : ["upload", "publish"].includes(confirmation.action) ? "Sign if needed and publish this exact bundle to Aos Cloud. An eligible verification-set Unit can receive it immediately; no batch-approval step is required. Installed and Running remain separate observations." : confirmation.action === "service-publish" ? "Sign and publish this prepared service through its configured Service Provider. Already assigned recipients can receive a higher release without another Deploy and without Safe Stop. Publication alone does not create a first assignment." : "Execute the named existing Demo Control operation once. No automatic retry or additional provisioning is implied."}</dd></dl>
      {["create", "start-vms", "prepare-demo"].includes(confirmation.action) && <p>VM access opens a macOS password dialog if it is not in Keychain. Choose Use once or Save in Keychain. Cancel stops preparation; no password enters this page.</p>}
    </Modal>, document.querySelector(".browser-workspace") ?? document.body)}
  </Context.Provider>;
}

export function OperationProgress({ job: selectedJob }: { job?: DemoJob | null } = {}) {
  const { session, error } = usePresenterControls();
  const job = selectedJob === undefined ? session?.jobs.at(-1) : selectedJob;
  const [clock, setClock] = useState(Date.now());
  const active = job && ["ACCEPTED", "RUNNING"].includes(job.state);
  useEffect(() => { if (!active) return; const timer = setInterval(() => setClock(Date.now()), 1000); return () => clearInterval(timer); }, [active]);
  const elapsed = job ? Math.max(0, Math.floor(((job.finishedAt ? Date.parse(job.finishedAt) : clock) - Date.parse(job.startedAt)) / 1000)) : NaN;
  const recovery = preparationRecovery(job);
  if (!job && !error) return null;
  return <section className="operation-progress" aria-live="polite" role="status">
    {error && <p className="operation-error">{error}</p>}
    {job && <><strong>{actionLabels[job.action]} · {job.state}{Number.isFinite(elapsed) ? ` · ${elapsed}s` : ""}</strong>{active && <p>{job.progress.at(-1)}</p>}
      {job.reason && <p>{job.reason}</p>}
      {recovery && <p className="operation-recovery">{recovery}</p>}
      {job.results.at(-1) && <p>{job.results.at(-1)!.message}</p>}
      <details><summary>Operation steps and observed result</summary><ol>{job.progress.map((entry, index) => <li key={index}>{entry}</li>)}</ol>
        <pre>{JSON.stringify(job.results, null, 2)}</pre><small>Observed {job.finishedAt ?? job.startedAt}. Completion of this operation is not full demo qualification.</small></details></>}
  </section>;
}

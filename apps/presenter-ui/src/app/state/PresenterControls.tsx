import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { DemoCommand, DemoJob, OperationSession, PresenterCommandPort } from "../../domain/presenterCommandPort";
import { Modal } from "../../shared/components/Modal";
import { createPortal } from "react-dom";
import { usePlatformObservation } from "./PresenterReadModelProvider";

export const actionLabels: Record<DemoCommand["action"], string> = {
  "cloud-inspect": "Read OEM certificate", "cloud-choose": "Choose OEM certificate", "cloud-select": "Use this Cloud",
  "cloud-check": "Check Cloud setup", "cloud-prepare": "Prepare Test Cloud",
  publish: "Sign & publish VDP", "service-prepare": "Prepare service", "service-publish": "Sign & publish service",
  "service-observe": "Refresh service publication", "service-assign": "Deploy service to Test",
  "prepare-demo": "Prepare demo",
  create: "Create controller", "start-vms": "Start Test controller", "stop-vms": "Stop Test controller", provision: "Provision Test Vehicle",
  "start-simulation": "Start simulator", "stop-simulation": "Stop simulator", "connect-test": "Connect in Manual", "reconnect-test": "Reconnect Test Vehicle", park: "Park demo", resume: "Resume demo", reset: "Finish demo",
  prepare: "Prepare VDP", unpack: "Unpack VDP", sign: "Sign VDP", upload: "Publish VDP to Aos Cloud", approve: "Authorize Test VDP deployment",
  inspect: "Inspect VDP", verify: "Verify VDP signature", "cloud-status": "Read Cloud release state", "observe-test": "Read Test VDP state", "test-logs": "Read Test VDP logs", "cloud-access": "Check OEM and Service Provider access",
};
const reads = new Set<DemoCommand["action"]>(["inspect", "verify", "cloud-status", "observe-test", "test-logs", "cloud-access", "service-observe", "cloud-inspect", "cloud-choose", "cloud-check"]);
interface Controls { session: OperationSession | null; blocked: boolean; readBlocked: boolean; blockReason: string | null; error: string | null; request: (command: DemoCommand) => void }
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
        if (value.active) delay = 1000;
      } catch {
        if (active) { connectionFailure.current = true; setReachable(false); setError("Demo Control session unavailable. No action will be retried automatically."); }
      }
      if (active) timer = setTimeout(poll, delay);
    };
    void poll();
    return () => { active = false; clearTimeout(timer); };
  }, [port]);
  const blocked = !port || !reachable || !session || Boolean(session.active) || session.uncertain || busy || Boolean(unresolved.current);
  const readBlocked = !port || !reachable || !session || Boolean(session.active) || busy;
  const blockReason = !port || !reachable || !session ? "Demo Control unavailable; reconnect before changing the environment."
    : session.active || busy ? "An operation is in progress; open Trace for its current step."
    : session.uncertain || unresolved.current ? "An operation outcome is unknown. Finish cannot safely overlap it; inspect Trace and reconcile the original operation before continuing. Read-only observations remain available." : null;
  useEffect(() => {
    document.documentElement.dataset.submissionPending = String(busy || Boolean(unresolved.current) || Boolean(session?.uncertain));
    return () => { delete document.documentElement.dataset.submissionPending; };
  }, [busy, error, session]);
  const submit = useCallback(async (command: DemoCommand) => {
    if (!port || !session || (reads.has(command.action) ? readBlocked : blocked) || submitting.current) return;
    submitting.current = true; setBusy(true); setError(null); setConfirmation(null);
    const id = crypto.randomUUID();
    const originalPending = unresolved.current;
    if (!originalPending) unresolved.current = { id, sessionId: session.sessionId, action: command.action };
    try {
      const job = await port.submit(command, id, session.sessionId);
      if (!originalPending) unresolved.current = null;
      setSession((previous) => previous ? { ...previous, active: ["ACCEPTED", "RUNNING"].includes(job.state) ? id : null,
        jobs: [...previous.jobs.filter((item) => item.id !== id), job] } : previous);
    } catch (problem) {
      if (problem instanceof Error && problem.message === "REJECTED") {
        if (!originalPending) unresolved.current = null; setError("Operation rejected or another operation is running. Refresh the state before continuing.");
      } else setError("Submission response lost. Checking the original request; it will not be submitted again.");
    } finally { submitting.current = false; setBusy(false); }
  }, [port, session, blocked, readBlocked]);
  const request = (command: DemoCommand) => {
    if (reads.has(command.action) ? readBlocked : blocked) return;
    if (reads.has(command.action)) void submit(command); else setConfirmation(command);
  };
  const close = useCallback(() => setConfirmation(null), []);
  const bundleRead = confirmation?.version ? [...(session?.jobs ?? [])].reverse().find((job) => job.cloudDomain === session?.cloudDomain && job.version === confirmation.version && job.results.some((result) => typeof result.facts.sha256 === "string")) : undefined;
  const bundleDigest = bundleRead?.results.find((result) => typeof result.facts.sha256 === "string")?.facts.sha256;
  return <Context.Provider value={{ session, blocked, readBlocked, blockReason, error, request }}>{children}
    {confirmation && createPortal(<Modal title={actionLabels[confirmation.action]} subtitle="Protected operation · explicit confirmation required" onClose={close}
      footer={<><button className="button" onClick={close}>Cancel</button><button className="button button-primary" disabled={blocked} onClick={() => void submit(confirmation)}>{actionLabels[confirmation.action]}</button></>}>
      <dl className="detail-grid"><dt>Actor</dt><dd>{confirmation.action === "service-assign" ? "OEM · dedicated service Subject" : confirmation.action.startsWith("service-") ? `${confirmation.team ?? confirmation.release?.split("/")[0] ?? "Service"} Team · configured Service Provider` : ["prepare", "unpack", "sign", "upload", "publish"].includes(confirmation.action) ? "Platform Team · fixed OEM publication context" : "Demo operator · current owned environment"}</dd>
        <dt>Target</dt><dd>{["upload", "publish", "service-publish"].includes(confirmation.action) ? "Configured Cloud publication context. Cloud distributes to eligible recipients; no Production membership or assignment is changed." : "Current Test Vehicle only. Production remains unchanged."}</dd>
        {confirmation.image && <><dt>Factory image</dt><dd>{confirmation.image}</dd></>}
        {confirmation.action === "cloud-select" && <><dt>Cloud domain</dt><dd>{String(session?.jobs.find(job => job.id === confirmation.selectionId)?.results.at(-1)?.facts.domain ?? "Preview unavailable")}</dd><dt>Effect</dt><dd>Select the Cloud from this OEM certificate for Test. Keep Production unchanged. No provisioning, publication or VM restart. Finish a provisioned Test before switching Clouds. SP access requires a certificate for the same Cloud.</dd></>}
        {confirmation.profile && <><dt>Capability profile</dt><dd>{confirmation.profile}</dd></>}
        {confirmation.action === "cloud-prepare" && <><dt>Cloud setup</dt><dd>Authenticate the selected OEM and SP. Reuse Default fleet; create only a missing matching Factory model/configuration and Test verification set. Recheck existing settings; stop on conflicts or an unknown creation outcome. No Unit provisioning, package upload, Subject assignment or Production change.</dd></>}
        {confirmation.release && <><dt>Prepared release</dt><dd>{confirmation.release}</dd></>}
        {confirmation.serviceId && <><dt>Service identity</dt><dd>{confirmation.serviceId}</dd><dt>Assignment</dt><dd>Bind this service's retained Group Subject to current Test, preserving the peer service. No version or instance count is sent. No Safe Stop is required.</dd></>}
        {confirmation.action.startsWith("service-") && confirmation.action !== "service-assign" && <><dt>Data mode</dt><dd>Synthetic service data; native KUKSA permissions remain blocked. Publication does not establish vehicle telemetry or advisory.</dd></>}
        {confirmation.action === "prepare-demo" && <><dt>Scenario</dt><dd>Create or continue this Test controller, connect the simulator in stationary Manual, prepare, sign and publish VDP v1, then provision into Test Vehicles. Installation follows the native Safe Stop policy. No validation-batch approval is required for verification-set delivery.</dd></>}
        {confirmation.version && <><dt>Cloud release</dt><dd>{confirmation.version}{confirmation.profile ? ` · content ${confirmation.profile}` : ""}</dd></>}
        {confirmation.version && <><dt>Last observed bundle SHA</dt><dd>{bundleDigest ? String(bundleDigest) : "Not yet observed — inspect/sign the selected release to see its digest"}</dd></>}
        <dt>Checks</dt><dd>Demo Control checks current ownership, exact target, required access and prerequisites when executing. UI state is not permission to bypass them.</dd>
        <dt>Effect</dt><dd>{confirmation.action === "reset" ? "Retire the owned Test run through Demo Control: detach and stop, clear its Subject bindings, deprovision/delete the Unit, remove its local working files and scoped backend data. Permanent, no backup. Factory originals, published releases and release continuity remain. Production is untouched." : ["upload", "publish"].includes(confirmation.action) ? "Sign if needed and publish this exact bundle to Aos Cloud. An eligible verification-set Unit can receive it immediately; no batch-approval step is required. Installed and Running remain separate observations." : confirmation.action === "service-publish" ? "Sign and publish this prepared service through its configured Service Provider. Already assigned recipients can receive a higher release without another Deploy and without Safe Stop. Publication alone does not create a first assignment." : "Execute the named existing Demo Control operation once. No automatic retry or additional provisioning is implied."}</dd></dl>
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
  if (!job && !error) return null;
  return <section className="operation-progress" aria-live="polite" role="status">
    {error && <p className="operation-error">{error}</p>}
    {job && <><strong>{actionLabels[job.action]} · {job.state}{Number.isFinite(elapsed) ? ` · ${elapsed}s` : ""}</strong>{active && <p>{job.progress.at(-1)}</p>}
      {job.reason && <p>{job.reason}</p>}
      {job.results.at(-1) && <p>{job.results.at(-1)!.message}</p>}
      <details><summary>Operation steps and observed result</summary><ol>{job.progress.map((entry, index) => <li key={index}>{entry}</li>)}</ol>
        <pre>{JSON.stringify(job.results, null, 2)}</pre><small>Observed {job.finishedAt ?? job.startedAt}. Completion of this operation is not full demo qualification.</small></details></>}
  </section>;
}

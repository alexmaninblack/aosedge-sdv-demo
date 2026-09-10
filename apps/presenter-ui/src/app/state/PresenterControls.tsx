import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { DemoCommand, OperationSession, PresenterCommandPort } from "../../domain/presenterCommandPort";
import { Modal } from "../../shared/components/Modal";
import { createPortal } from "react-dom";
import { usePlatformObservation } from "./PresenterReadModelProvider";

export const actionLabels: Record<DemoCommand["action"], string> = {
  "prepare-demo": "Prepare demo",
  create: "Create Test and Production Vehicles", "start-vms": "Start both VMs", "stop-vms": "Stop both VMs", provision: "Provision both Vehicles",
  "start-simulation": "Start simulator", "stop-simulation": "Stop simulator", "connect-test": "Connect Test Vehicle", reset: "End and reset both Vehicles",
  prepare: "Prepare VDP", unpack: "Unpack VDP", sign: "Sign VDP", upload: "Publish VDP to Aos Cloud", approve: "Authorize Test VDP deployment",
  inspect: "Inspect VDP", verify: "Verify VDP signature", "cloud-status": "Read Cloud release state", "observe-test": "Read Test VDP state", "test-logs": "Read Test VDP logs", "cloud-access": "Check OEM and Service Provider access",
};
const reads = new Set<DemoCommand["action"]>(["inspect", "verify", "cloud-status", "observe-test", "test-logs", "cloud-access"]);
interface Controls { session: OperationSession | null; blocked: boolean; error: string | null; request: (command: DemoCommand) => void }
const unavailable: Controls = { session: null, blocked: true, error: null, request: () => {} };
const Context = createContext<Controls>(unavailable);
export const usePresenterControls = () => useContext(Context);

export function PresenterControls({ port, children }: { port?: PresenterCommandPort; children: ReactNode }) {
  const [session, setSession] = useState<OperationSession | null>(null);
  const [reachable, setReachable] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<DemoCommand | null>(null);
  const submitting = useRef(false);
  const unresolved = useRef<{ id: string; sessionId: string } | null>(null);
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
          if (pending.sessionId === value.sessionId && value.jobs.some((job) => job.id === pending.id)) {
            unresolved.current = null; setError(null);
          } else setError("Submission outcome unknown. Do not repeat it; reconcile native state.");
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
  const submit = useCallback(async (command: DemoCommand) => {
    if (!port || !session || blocked || submitting.current) return;
    submitting.current = true; setBusy(true); setError(null); setConfirmation(null);
    const id = crypto.randomUUID();
    unresolved.current = { id, sessionId: session.sessionId };
    try {
      const job = await port.submit(command, id, session.sessionId);
      unresolved.current = null;
      setSession((previous) => previous ? { ...previous, active: ["ACCEPTED", "RUNNING"].includes(job.state) ? id : null,
        jobs: [...previous.jobs.filter((item) => item.id !== id), job] } : previous);
    } catch (problem) {
      if (problem instanceof Error && problem.message === "REJECTED") {
        unresolved.current = null; setError("Operation rejected or another operation is running. Refresh the state before continuing.");
      } else setError("Submission response lost. Checking the original request; it will not be submitted again.");
    } finally { submitting.current = false; setBusy(false); }
  }, [port, session, blocked]);
  const request = (command: DemoCommand) => {
    if (blocked) return;
    if (reads.has(command.action)) void submit(command); else setConfirmation(command);
  };
  const close = useCallback(() => setConfirmation(null), []);
  const bundleRead = confirmation?.version ? [...(session?.jobs ?? [])].reverse().find((job) => job.version === confirmation.version && job.results.some((result) => typeof result.facts.sha256 === "string")) : undefined;
  const bundleDigest = bundleRead?.results.find((result) => typeof result.facts.sha256 === "string")?.facts.sha256;
  return <Context.Provider value={{ session, blocked, error, request }}>{children}
    {confirmation && createPortal(<Modal title={actionLabels[confirmation.action]} subtitle="Protected operation · explicit confirmation required" onClose={close}
      footer={<><button className="button" onClick={close}>Cancel</button><button className="button button-primary" disabled={blocked} onClick={() => void submit(confirmation)}>{actionLabels[confirmation.action]}</button></>}>
      <dl className="detail-grid"><dt>Actor</dt><dd>{["prepare", "unpack", "sign", "upload"].includes(confirmation.action) ? "Platform Team · fixed OEM publication context" : confirmation.action === "approve" ? "OEM Release Authority · Test verification batch" : "Demo operator · current owned environment"}</dd>
        <dt>Target</dt><dd>{confirmation.action === "approve" || confirmation.version ? "VDP component · Test Vehicle only" : "Current Test and Production environment; only Test connects to CARLA"}</dd>
        {confirmation.image && <><dt>Factory image</dt><dd>{confirmation.image}</dd></>}
        {confirmation.action === "prepare-demo" && <><dt>Scenario</dt><dd>Create or continue the matching two-VM environment. Automatically reuse this run's v1 release or select the next Cloud release; prepare, sign, upload and approve Test v1, start/provision both VMs, start simulation and attach Test in stationary Manual. Production FOTA is excluded. Then you drive and press Safe Stop.</dd></>}
        {confirmation.version && <><dt>Cloud release</dt><dd>{confirmation.version}{confirmation.profile ? ` · content ${confirmation.profile}` : ""}</dd></>}
        {confirmation.version && <><dt>Last observed bundle SHA</dt><dd>{bundleDigest ? String(bundleDigest) : "Not yet observed — inspect/sign the selected release to see its digest"}</dd></>}
        <dt>Checks</dt><dd>Demo Control checks current ownership, exact target, required access and prerequisites when executing. UI state is not permission to bypass them.</dd>
        <dt>Effect</dt><dd>{confirmation.action === "reset" ? "Stop simulation → deprovision both Units → delete both Units → stop remaining VMs → retire local overlays, generated access and working image copy. Inapplicable stages are skipped only from the owned native journal. Permanent, no backup. Original images and published releases remain." : confirmation.action === "upload" ? "Publish this exact signed bundle to Aos Cloud. This is not deployment approval. Published release numbers are not reused." : confirmation.action === "approve" ? "Approve the exact Test verification batch. Cloud acceptance is not proof of installation or running VDP. Production rollout is excluded." : "Execute the named existing Demo Control operation once. No automatic retry or additional provisioning is implied."}</dd></dl>
      {["start-vms", "prepare-demo"].includes(confirmation.action) && <p>VM access opens a macOS password dialog if it is not in Keychain. Choose Use once or Save in Keychain. Cancel stops preparation; no password enters this page.</p>}
    </Modal>, document.querySelector(".browser-workspace") ?? document.body)}
  </Context.Provider>;
}

export function OperationProgress() {
  const { session, error } = usePresenterControls();
  const job = session?.jobs.at(-1);
  if (!job && !error) return null;
  return <section className="operation-progress" aria-live="polite" role="status">
    {error && <p className="operation-error">{error}</p>}
    {job && <><strong>{actionLabels[job.action]} · {job.state}</strong><p>{job.progress.at(-1)}</p>
      {job.reason && <p>{job.reason}</p>}
      {job.results.at(-1) && <p>{job.results.at(-1)!.message}</p>}
      <details><summary>Operation steps and observed result</summary><ol>{job.progress.map((entry, index) => <li key={index}>{entry}</li>)}</ol>
        <pre>{JSON.stringify(job.results, null, 2)}</pre><small>Observed {job.finishedAt ?? job.startedAt}. Completion of this operation is not full demo qualification.</small></details></>}
  </section>;
}

import { useEffect, useRef } from "react";
import { usePresenterControls } from "./state/PresenterControls";

export function CloudConnectionPanel({ section = "all" }: { section?: "connection" | "setup" | "all" }) {
  const controls = usePresenterControls();
  const started = useRef(false);
  useEffect(() => {
    if (section !== "setup" && !started.current && !controls.readBlocked) {
      started.current = true;
      controls.request({ action: "cloud-inspect" });
    }
  }, [controls, section]);
  const jobs = controls.session?.jobs ?? [];
  const preview = [...jobs].reverse().find(job => ["cloud-inspect", "cloud-choose"].includes(job.action));
  const result = preview?.results.at(-1);
  const facts = result?.facts;
  const selection = [...jobs].reverse().find(job => job.action === "cloud-select");
  // Configuration and certificate availability are independent facts. Old job
  // receipts cannot override the current session's selected Cloud.
  const currentDomain = controls.session?.cloudDomain;
  const ready = preview?.state === "COMPLETED" && typeof facts?.domain === "string";
  const setupJob = [...jobs].reverse().find(job => ["cloud-check", "cloud-prepare"].includes(job.action)
    && job.cloudDomain === controls.session?.cloudDomain);
  const setup = setupJob?.results.at(-1)?.facts;
  const setupRows = Array.isArray(setup?.checks) ? setup.checks as { key: string; label: string; state: string; detail: string }[] : [];
  return <section className="studio-cloud-connection" aria-label="Cloud connection">
    {section !== "setup" && <><h3>Cloud connection</h3>
    <p>Domain from the OEM certificate. Certificate and key stay on this Mac.</p>
    <dl className="detail-grid">
      <dt>Selected Cloud</dt><dd>{currentDomain ?? (controls.session ? "Not available" : "Reading configuration…")}</dd>
      <dt>Certificate domain</dt><dd>{String(facts?.domain ?? "Not available")}</dd>
      {Boolean(facts?.certificateName) && <><dt>Certificate</dt><dd>{String(facts?.certificateName)}</dd></>}
    </dl>
    {result?.state === "BLOCKED" && <p role="alert">{result.message}</p>}
    {preview?.reason && <p role="alert">{preview.reason}</p>}
    {selection?.state === "BLOCKED" && <p role="alert">{selection.reason ?? selection.results.at(-1)?.message}</p>}
    <div className="studio-cloud-actions">
      <button disabled={controls.readBlocked} onClick={() => controls.request({ action: "cloud-choose" })}>Choose certificate…</button>
      <button disabled={controls.readBlocked} onClick={() => controls.request({ action: "cloud-inspect" })}>Read configured certificate</button>
      <button className="button button-primary" disabled={controls.blocked || !ready}
        onClick={() => controls.request({ action: "cloud-select", selectionId: preview!.id })}>Use this Cloud</button>
    </div>
    <p>Reading the OEM certificate does not verify Cloud API or Service Provider access.</p></>}
    {section !== "connection" && <section aria-label="Test Cloud setup">
      <h3>Test Cloud setup</h3>
      <p>Check this OEM and Service Provider before provisioning. Preparation preserves existing campaigns and Production.</p>
      <div className="studio-cloud-actions">
        <button disabled={controls.readBlocked} onClick={() => controls.request({ action: "cloud-check" })}>Check Cloud setup</button>
        <button disabled={controls.blocked} onClick={() => controls.request({ action: "cloud-prepare" })}>Prepare Test Cloud</button>
      </div>
      {setupJob && <p role="status">{setupJob.state === "RUNNING" || setupJob.state === "ACCEPTED" ? "Checking selected Cloud…" : String(setup?.stage ?? setupJob.reason ?? setupJob.results.at(-1)?.message ?? setupJob.state)}</p>}
      {setupRows.length > 0 && <dl className="detail-grid">{setupRows.map(row => <div key={row.key} style={{ display: "contents" }}>
        <dt>{row.label}</dt><dd><strong>{row.state}</strong> · {row.detail}</dd>
      </div>)}</dl>}
      {typeof setup?.observedAt === "string" && <p>Last checked: {new Date(setup.observedAt).toLocaleTimeString()}. Refresh after changing credentials.</p>}
    </section>}
    {controls.blockReason && <p role="status">{controls.blockReason}</p>}
    {section !== "setup" && <details><summary>Connection details</summary><p>API :10000 · Service Discovery :9000 · Aos CA · TLS verification enabled.</p>
    <p>Production Cloud uses the normal startup path without guest overrides. For debug Cloud only, <code>democtl vm start test</code> applies host mappings before guest setup and restores the selected endpoint; this may restart CM once. Factory firmware is unchanged.</p></details>}
  </section>;
}

import { useState } from "react";
import { usePresenterControls, actionLabels } from "../../app/state/PresenterControls";
import type { DemoAction } from "../../domain/presenterCommandPort";

export function LocalPlatformControls() {
  const controls = usePresenterControls();
  const last = [...(controls.session?.jobs ?? [])].reverse().find((job) => job.version);
  const [draft, setDraft] = useState<string | null>(null);
  const [profile, setProfile] = useState<"v1" | "v2" | "v3">("v1");
  const version = draft ?? last?.version ?? "";
  const valid = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version) && version.length <= 32;
  const actions: DemoAction[] = ["prepare", "inspect", "unpack", "sign", "verify", "upload", "cloud-status", "approve"];
  return <section className="local-platform-controls" aria-label="Test VDP operations">
    <h2>Test VDP release</h2>
    <p>Functional profile and Cloud release are separate. Use a new, increasing release number for each replay; prepare v1 before provisioning.</p>
    <div className="local-release-inputs"><label>Content profile<select aria-label="VDP content profile" value={profile} onChange={(event) => setProfile(event.target.value as typeof profile)}>
      <option value="v1">v1 · baseline telemetry</option><option value="v2">v2 · local analysis inputs</option><option value="v3">v3 · tire telemetry</option></select></label>
      <label>Cloud release<input aria-label="VDP Cloud release" value={version} placeholder="major.minor.patch" onChange={(event) => setDraft(event.target.value)} /></label></div>
    <div className="local-action-row">{actions.map((action) => <button key={action} className="button" disabled={controls.blocked || !valid}
      onClick={() => controls.request(action === "prepare" ? { action, version, profile } : { action, version })}>{actionLabels[action]}</button>)}</div>
    <p>Current Test state is read from Aos Cloud above. This panel does not read the VM directly.</p>
  </section>;
}

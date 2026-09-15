import { useEffect, useRef, useState } from "react";
import { usePresenterControls } from "./state/PresenterControls";
import { readClientState } from "../adapters/local/LocalPresenterReadAdapter";

/** Ordinary browsers need the same build-awareness as the native wrapper.
 * Never reload automatically or while an operation/dialog is unresolved. */
export function ClientBuildNotice() {
  const initial = useRef<string | null>(null);
  const [changed, setChanged] = useState(false);
  const [reloadAllowed, setReloadAllowed] = useState(false);
  const controls = usePresenterControls();
  useEffect(() => {
    if (window.location.hash.startsWith("#native-")) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const read = async () => {
      if (document.visibilityState !== "hidden") {
        try {
          const value = await readClientState();
          if (active && typeof value.buildId === "string") {
            initial.current ??= value.buildId;
            setChanged(value.buildId !== initial.current);
            setReloadAllowed(value.canReload === true);
          }
        } catch { if (active) setReloadAllowed(false); }
      }
      if (active) timer = setTimeout(read, 5000);
    };
    void read();
    return () => { active = false; clearTimeout(timer); };
  }, []);
  if (!changed) return null;
  const blocked = !reloadAllowed || controls.blocked || Boolean(document.querySelector('[role="dialog"]'));
  return <aside className="studio-build-notice" role="status"><span>A newer Presenter UI is available.{blocked ? " Finish the current interaction before reloading." : " Reload to use the updated interface."}</span><button disabled={blocked} onClick={() => {
    if (document.documentElement.dataset.submissionPending !== "true" && !document.querySelector('[role="dialog"]')) window.location.reload();
  }}>Reload UI</button></aside>;
}

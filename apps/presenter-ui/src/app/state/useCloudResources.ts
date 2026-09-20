// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { useEffect, useState } from "react";
import { readCloudMonitoring } from "../../adapters/local/LocalPresenterReadAdapter";
import type { ResourceRead } from "../../domain/resourceHistory";

function useResourceChannel(unitId: string | undefined, enabled: boolean, identity: string, history: boolean, refreshKey?: number, generation = 0) {
  const [stored, setStored] = useState<{ identity: string; data: ResourceRead | null; error: boolean; reason: string | null }>({ identity, data: null, error: false, reason: null });
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    if (!unitId || !enabled) { setBusy(false); return; }
    const read = async () => {
      if (!active) return;
      if (document.visibilityState === "hidden") { timer = setTimeout(read, 1000); return; }
      setBusy(true);
      const started = Date.now();
      try {
        const incoming = await readCloudMonitoring(identity, history) as ResourceRead;
        if (!active) return;
        const section = history ? incoming.history : incoming.monitoring;
        const valid = incoming.unitId === unitId && section && (section.value === null || typeof section.value === "object");
        setStored(previous => {
          const old = previous.identity === identity ? previous.data : null;
          if (!valid) return { identity, data: incoming.unitId && incoming.unitId !== unitId ? null : old, error: true, reason: "Cloud resource scope or response unavailable." };
          if (old?.readCompletedAt && incoming.readCompletedAt && Date.parse(incoming.readCompletedAt) < Date.parse(old.readCompletedAt)) return previous;
          return { identity, data: section.value ? incoming : section.state === "CURRENT" ? incoming : old,
            error: section.state !== "CURRENT", reason: section.state !== "CURRENT" ? section.reason ?? "Cloud resources unavailable" : null };
        });
      } catch {
        if (active) setStored(previous => ({ identity, data: previous.identity === identity ? previous.data : null, error: true, reason: "Cloud resource read failed." }));
      } finally { if (active) setBusy(false); }
      if (active) timer = setTimeout(read, Math.max(1000, 30000 - (Date.now() - started)));
    };
    void read();
    return () => { active = false; clearTimeout(timer); };
  }, [unitId, enabled, identity, history, refreshKey, generation]);
  return { ...(stored.identity === identity ? stored : { data: null, error: false, reason: null }), busy };
}

export function useCloudResources(unitId?: string, enabled = true, refreshKey?: number, scope = "") {
  const [generation, setGeneration] = useState(0);
  const identity = `${scope}:${unitId ?? ""}`;
  const latest = useResourceChannel(unitId, enabled, identity, false, refreshKey, generation);
  const history = useResourceChannel(unitId, enabled, identity, true, refreshKey, generation);
  return { ...latest, history, refresh: () => setGeneration(value => value + 1) };
}
export type CloudResourcesModel = Omit<ReturnType<typeof useCloudResources>, "identity" | "history"> & { history?: ReturnType<typeof useResourceChannel> };

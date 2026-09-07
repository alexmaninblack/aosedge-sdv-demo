import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { PresenterSnapshot, PlatformCloudObservation } from "../../domain";
import type { PresenterDependencies } from "../composition/PresenterDependencies";

const PresenterReadModelContext = createContext<Readonly<PresenterSnapshot> | null>(null);
const PlatformContext = createContext<{ observation: PlatformCloudObservation | null; loading: boolean; refresh: () => void }>({ observation: null, loading: false, refresh: () => {} });
export const usePlatformObservation = () => useContext(PlatformContext);

export function PresenterReadModelProvider({ dependencies, children }: { dependencies: PresenterDependencies; children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<Readonly<PresenterSnapshot> | null>(null);
  const [platform, setPlatform] = useState<PlatformCloudObservation | null>(null);
  const [loading, setLoading] = useState(false);
  const pending = useRef(false);
  const refresh = useCallback(() => {
    if (!dependencies.readPort.readPlatform || pending.current) return;
    pending.current = true;
    setLoading(true);
    setPlatform((old) => old ? { ...old, state: "STALE" } : old);
    void dependencies.readPort.readPlatform().then(setPlatform).catch(() => setPlatform({ state: "UNAVAILABLE", observedAt: null,
      value: null, reason: "AOS_CLOUD_STATE_UNAVAILABLE" })).finally(() => { pending.current = false; setLoading(false); });
  }, [dependencies]);
  useEffect(() => {
    if (platform?.state !== "CURRENT" || !platform.observedAt) return;
    const remaining = Math.max(0, 60000 - (Date.now() - Date.parse(platform.observedAt)));
    const timer = setTimeout(() => setPlatform((old) => old ? { ...old, state: "STALE" } : old), remaining);
    return () => clearTimeout(timer);
  }, [platform]);
  useEffect(() => {
    let active = true;
    void dependencies.readPort.read().then((value) => { if (active) setSnapshot(value); });
    const unsubscribe = dependencies.readPort.subscribe((value) => { if (active) setSnapshot(value); });
    return () => { active = false; unsubscribe(); };
  }, [dependencies]);
  if (!snapshot) return <div role="status">Reading Presenter state…</div>;
  return <PresenterReadModelContext.Provider value={snapshot}><PlatformContext.Provider value={{ observation: platform, loading, refresh }}>{children}</PlatformContext.Provider></PresenterReadModelContext.Provider>;
}

export function usePresenterReadModel(): Readonly<PresenterSnapshot> {
  const value = useContext(PresenterReadModelContext);
  if (!value) throw new Error("PresenterReadModelProvider is missing");
  return value;
}

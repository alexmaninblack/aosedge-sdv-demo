import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { PresenterSnapshot, PlatformCloudObservation } from "../../domain";
import type { PresenterDependencies } from "../composition/PresenterDependencies";
import { VisibleCloudObserver, type CloudObserverState } from "../../domain/visibleCloudObserver";

const PresenterReadModelContext = createContext<Readonly<PresenterSnapshot> | null>(null);
const PlatformContext = createContext<CloudObserverState & { refresh: () => void; enter: () => () => void; afterAction: () => void }>({ observation: null, loading: false, refresh: () => {}, enter: () => () => {}, afterAction: () => {} });
export const usePlatformObservation = () => useContext(PlatformContext);

export function PresenterReadModelProvider({ dependencies, children }: { dependencies: PresenterDependencies; children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<Readonly<PresenterSnapshot> | null>(null);
  const observer = useMemo(() => new VisibleCloudObserver(() => dependencies.readPort.readPlatform?.() ?? Promise.resolve({
    state: "UNAVAILABLE", value: null, observedAt: null, reason: "AOS_CLOUD_READ_NOT_CONNECTED" })), [dependencies]);
  const [cloud, setCloud] = useState<CloudObserverState>({ observation: null, loading: false });
  useEffect(() => observer.subscribe(setCloud), [observer]);
  useEffect(() => {
    const visibility = () => observer.setForeground(document.visibilityState !== "hidden");
    visibility(); document.addEventListener("visibilitychange", visibility);
    return () => { document.removeEventListener("visibilitychange", visibility); observer.setForeground(false); };
  }, [observer]);
  useEffect(() => {
    let active = true;
    void dependencies.readPort.read().then((value) => { if (active) setSnapshot(value); });
    const unsubscribe = dependencies.readPort.subscribe((value) => { if (active) setSnapshot(value); });
    return () => { active = false; unsubscribe(); };
  }, [dependencies]);
  if (!snapshot) return <div role="status">Reading Presenter state…</div>;
  return <PresenterReadModelContext.Provider value={snapshot}><PlatformContext.Provider value={{ ...cloud, refresh: observer.refresh, enter: observer.enter, afterAction: observer.afterAction }}>{children}</PlatformContext.Provider></PresenterReadModelContext.Provider>;
}

export function usePresenterReadModel(): Readonly<PresenterSnapshot> {
  const value = useContext(PresenterReadModelContext);
  if (!value) throw new Error("PresenterReadModelProvider is missing");
  return value;
}

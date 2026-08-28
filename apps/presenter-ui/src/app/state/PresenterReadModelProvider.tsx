import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { PresenterSnapshot } from "../../domain";
import type { PresenterDependencies } from "../composition/PresenterDependencies";

const PresenterReadModelContext = createContext<Readonly<PresenterSnapshot> | null>(null);

export function PresenterReadModelProvider({ dependencies, children }: { dependencies: PresenterDependencies; children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<Readonly<PresenterSnapshot> | null>(null);
  useEffect(() => {
    let active = true;
    void dependencies.readPort.read().then((value) => { if (active) setSnapshot(value); });
    const unsubscribe = dependencies.readPort.subscribe((value) => { if (active) setSnapshot(value); });
    return () => { active = false; unsubscribe(); };
  }, [dependencies]);
  if (!snapshot) return <div role="status">Loading deterministic presenter fixture…</div>;
  return <PresenterReadModelContext.Provider value={snapshot}>{children}</PresenterReadModelContext.Provider>;
}

export function usePresenterReadModel(): Readonly<PresenterSnapshot> {
  const value = useContext(PresenterReadModelContext);
  if (!value) throw new Error("PresenterReadModelProvider is missing");
  return value;
}

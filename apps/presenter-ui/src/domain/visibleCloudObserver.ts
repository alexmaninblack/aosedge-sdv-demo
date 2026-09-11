import type { PlatformCloudObservation } from "./platformObservation";

export interface CloudObserverState { observation: PlatformCloudObservation | null; loading: boolean; refreshGeneration?: number }
const unavailable = (): PlatformCloudObservation => ({ state: "UNAVAILABLE", value: null, observedAt: null, reason: "AOS_CLOUD_STATE_UNAVAILABLE" });

/** One observation key per instance. Navigation never cancels an in-flight read. */
export class VisibleCloudObserver {
  private listeners = new Set<(value: CloudObserverState) => void>();
  private panels = 0;
  private foreground = true;
  private timer?: ReturnType<typeof setTimeout>;
  private flight: Promise<void> | null = null;
  private dirty = false;
  private pendingDelay = 2000;
  private state: CloudObserverState = { observation: null, loading: false };

  constructor(private read: () => Promise<PlatformCloudObservation>, private intervals = { pending: 2000, maximum: 10000, idle: 10000 }) {
    this.pendingDelay = intervals.pending;
  }
  subscribe = (listener: (state: CloudObserverState) => void) => {
    this.listeners.add(listener); listener(this.state);
    return () => { this.listeners.delete(listener); };
  };
  private emit() { this.listeners.forEach((listener) => listener(this.state)); }
  private visible() { return this.panels > 0 && this.foreground; }
  private cancelTimer() { clearTimeout(this.timer); this.timer = undefined; }
  private hidden() {
    this.cancelTimer();
    if (this.state.observation?.state === "CURRENT") {
      this.state = { ...this.state, observation: { ...this.state.observation, state: "STALE", reason: "OBSERVER_HIDDEN" } }; this.emit();
    }
  }
  enter = () => {
    this.panels += 1;
    if (this.panels === 1) { this.pendingDelay = this.intervals.pending; void this.refresh(); }
    let active = true;
    return () => { if (active) { active = false; this.panels -= 1; if (!this.visible()) this.hidden(); } };
  };
  setForeground = (value: boolean) => {
    if (this.foreground === value) return;
    this.foreground = value;
    if (this.visible()) void this.refresh(); else this.hidden();
  };
  afterAction = () => {
    this.dirty = true;
    this.pendingDelay = this.intervals.pending;
    if (this.state.observation) {
      this.state = { ...this.state, observation: { ...this.state.observation, state: "STALE", reason: "ACTION_COMPLETED_REFRESH_REQUIRED" } };
      this.emit();
    }
    if (this.visible()) void this.refresh();
  };
  refresh = (): Promise<void> => {
    if (!this.visible()) return Promise.resolve();
    if (this.flight) return this.flight;
    this.cancelTimer(); this.dirty = false;
    this.state = { ...this.state, loading: true }; this.emit();
    this.flight = Promise.resolve().then(this.read).catch(unavailable).then((incoming) => {
      const old = this.state.observation;
      // Failed reads do not erase inventory or manufacture Offline/absence.
      const sameBinding = !incoming.bindingKey || !old?.bindingKey || incoming.bindingKey === old.bindingKey;
      const observation = incoming.state !== "CURRENT" && old?.value && sameBinding
        ? { ...old, publication: incoming.publication ?? old.publication, publications: incoming.publications ?? old.publications, state: "STALE" as const, reason: incoming.reason ?? "AOS_CLOUD_STATE_UNAVAILABLE" }
        : incoming;
      this.state = { observation: this.dirty ? { ...observation, state: "STALE", reason: "ACTION_COMPLETED_REFRESH_REQUIRED" } : observation, loading: false, refreshGeneration: (this.state.refreshGeneration ?? 0) + 1 };
      if (!this.visible()) this.hidden();
      this.emit();
    }).finally(() => {
      this.flight = null;
      if (!this.visible()) return;
      if (this.dirty) { void this.refresh(); return; }
      const pending = Boolean(this.state.observation?.value?.pendingVersion) || ["ACCEPTED", "PROCESSING"].includes(this.state.observation?.publication?.stage ?? "");
      const delay = pending ? this.pendingDelay : this.intervals.idle;
      this.pendingDelay = pending ? Math.min(this.pendingDelay * 2, this.intervals.maximum) : this.intervals.pending;
      this.timer = setTimeout(() => { void this.refresh(); }, delay);
    });
    return this.flight;
  };
}

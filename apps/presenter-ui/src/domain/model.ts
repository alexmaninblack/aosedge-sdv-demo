export type TeamId = "platform" | "brake" | "tire";
export type Perspective = "global" | TeamId;
export type VehicleRole = "not-assigned" | "test" | "production" | "changing" | "unavailable";
export type ObservationState = "CURRENT" | "STALE" | "UNAVAILABLE" | "ERROR";
export type StageState =
  | "complete"
  | "current"
  | "ready"
  | "blocked"
  | "waiting"
  | "submitting"
  | "uncertain"
  | "reconciling"
  | "failed";

export interface SourceReference {
  owner: string;
  system: string;
  fixture: true;
}

export interface Observed<T> {
  value: T | null;
  source: SourceReference;
  observedAt: string | null;
  state: ObservationState;
  reason?: string;
}

export interface ReleaseStage {
  id: "publish" | "test-authorize" | "test-accept" | "production-authorize" | "production-live";
  label: string;
  actor: string;
  state: StageState;
  explanation: string;
  action?: string;
}

export interface ReleaseDetails {
  summary: string;
  artifact: string;
  digest: string;
  dependency: string;
  access: string;
  quota?: string;
  target: string;
  evidence: string;
}

export interface ReleaseView {
  id: string;
  version: number;
  title: string;
  subtitle: string;
  team: TeamId;
  motionPolicy: "Safe Stop required" | "In-motion update allowed";
  dependency?: string;
  status: string;
  stages: ReleaseStage[];
  details: ReleaseDetails;
}

export interface TeamView {
  id: TeamId;
  name: string;
  purpose: string;
  compactStatus: string;
  productStatus: string;
  lifecycleStatus: string;
  source: Observed<string>;
  evidenceTitle: string;
  evidenceBody: string;
  backendStatus: string;
  quota?: string;
  isolation?: {
    status: string;
    tireCpu: string;
    brake: string;
    platform: string;
  };
  releases: ReleaseView[];
}

export interface QualificationView {
  status: "QUALIFIED" | "ABSENT" | "STALE" | "WITHDRAWN" | "NOT_QUALIFIED";
  reason: string;
}

export interface GlobalLifecycleView {
  qualification: Observed<QualificationView>;
  stage: "READY_FOR_M0" | "M0" | "M1" | "G0" | "ACTIVE" | "R0" | "RECOVERY_REQUIRED";
  manufactured: boolean;
  provisioned: boolean;
  recovery: string;
  milestone: string;
}

export interface PresenterSnapshot {
  fixtureId: string;
  fixtureLabel: string;
  observedAt: string;
  vehicle: Observed<VehicleRole>;
  workspace: Observed<"READY" | "INCOMPLETE">;
  global: GlobalLifecycleView;
  teams: Record<TeamId, TeamView>;
  assetFailure: boolean;
  eventChain: string[];
  redactionNotice: string;
}

export interface PresentationState {
  perspective: Perspective;
  openOverlay: null | { kind: "details" | "logs" | "action"; team?: TeamId; releaseId?: string; action?: string };
  scrollByTeam: Record<TeamId, number>;
  focusByTeam: Record<TeamId, string | null>;
  actionNotice: string | null;
}

export type PresentationAction =
  | { type: "navigate"; perspective: Perspective }
  | { type: "remember-team"; team: TeamId; scroll: number; focus: string | null }
  | { type: "open-details"; team: TeamId; releaseId: string }
  | { type: "open-logs"; team: TeamId }
  | { type: "open-action"; team?: TeamId; releaseId?: string; action: string }
  | { type: "close-overlay" }
  | { type: "confirm-fixture-action"; action: string };

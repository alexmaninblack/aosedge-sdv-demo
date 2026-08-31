import type { ReadObservation, ReadObservationState } from "./sourceObservation";

export type TeamId = "platform" | "brake" | "tire";
export type Perspective = "global" | TeamId;
export type VehicleRole = "not-assigned" | "test" | "production" | "changing" | "unavailable";
export type ObservationState = ReadObservationState | "UNAVAILABLE" | "ERROR";
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
  logs?: ReadObservation<readonly NativeLogView[]>;
  brakeResources?: ReadObservation<readonly BrakeResourceView[]>;
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

export type AudienceVehicleRole = "TEST" | "PRODUCTION";

export interface SessionView {
  routeContext: "oem-delivery-read" | "brake-sp1-read";
  role: string;
  ownerFingerprint: string;
  effectivePermissions: readonly string[];
}

export interface VehicleBindingView {
  role: AudienceVehicleRole;
  label: "Test Vehicle" | "Production Vehicle";
  wireRole: "VALIDATION" | "PRODUCTION";
  systemUidFingerprint: string;
  unitFingerprint: string;
  mainNodeFingerprint: string;
  unitSetFingerprint: string;
}

export interface UnitView {
  role: AudienceVehicleRole;
  systemUidFingerprint: string;
  unitFingerprint: string;
  mainNodeFingerprint: string;
  connectionState: "Online" | "Offline";
  reportedState: "ready" | "error" | "unknown";
  desiredSoftware: readonly string[];
  actualSoftware: readonly string[];
  pendingComponentBatchFingerprints: readonly string[];
  pendingServiceBatchFingerprints: readonly string[];
}

export interface UnitSetView {
  role: AudienceVehicleRole;
  title: string;
  isValidationSet: boolean;
  memberUnitFingerprints: readonly string[];
  complete: boolean;
}

export interface ReleaseObjectView {
  kind: "CANDIDATE" | "VERIFICATION_BATCH" | "FLEET_VALIDATION_BATCH" | "CAMPAIGN";
  fingerprint: string;
  state: "published" | "waiting" | "valid" | "done" | "preview";
  targetFingerprints: readonly string[];
  result?: string;
  unresolvedShape?: "unit_ids" | "units_ids";
}

export interface NativeLogView {
  family: "unit-logs" | "service-logs";
  owner: "OEM" | "BRAKE_SP1";
  scopeFingerprint: string;
  requestFingerprint: string;
  cloudState: "created" | "sent" | "waiting unit" | "receiving" | "done" | "error" | "empty log has been provided";
  metadata: readonly string[];
  retentionNotice: "Retention policy not exposed by current API";
}

export interface BrakeResourceView {
  role: AudienceVehicleRole;
  unitSystemUidFingerprint: string;
  resourceType: "WINDOW" | "ASSESSMENT" | "EVENT" | "ADVISORY";
  state: "COMPLETE" | "PARTIAL" | "ASSESSED" | "PENDING_ASSESSMENT_CORRELATION" | "CORRELATED_ASSESSMENT" | "PUBLISHED";
  deliveryState: "RECEIVING" | "DELAYED" | "CONFLICT" | "DURABLY_RECEIVED";
  projectionState: "GROWING" | "PARTIAL" | "TERMINAL" | "QUARANTINED" | null;
  terminalState: "COMPLETE" | "TRUNCATED_MAX_DURATION" | "INCOMPLETE_SOURCE_GAP" | "ABORTED_SERVICE_STOP" | "ABORTED_RESTART" | null;
  count: number;
  limit: number;
  nextCursor: string | null;
  complete: boolean;
  sourceTime: string | null;
  backendReceivedAt: string | null;
  vdpVersion: string | null;
  vdpDigest: string | null;
}

export interface ReadOnlyPresenterView {
  contractClass: "CONTRACT_SYNTHETIC";
  session: ReadObservation<SessionView>;
  brakeSession: ReadObservation<SessionView>;
  bindings: ReadObservation<readonly VehicleBindingView[]>;
  units: ReadObservation<readonly UnitView[]>;
  unitSets: ReadObservation<readonly UnitSetView[]>;
  releases: ReadObservation<readonly ReleaseObjectView[]>;
  unitLogs: ReadObservation<readonly NativeLogView[]>;
  serviceLogs: ReadObservation<readonly NativeLogView[]>;
  brake: ReadObservation<readonly BrakeResourceView[]>;
  notificationRereads: number;
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
  readOnly?: ReadOnlyPresenterView;
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

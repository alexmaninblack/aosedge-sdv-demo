export type ReadObservationState =
  | "CURRENT"
  | "STALE"
  | "UNKNOWN"
  | "INCOMPLETE"
  | "REDACTED"
  | "NOT_APPLICABLE";

export type TransportClassification =
  | "AVAILABLE"
  | "UNAUTHENTICATED"
  | "FORBIDDEN"
  | "NOT_FOUND_OR_INACCESSIBLE"
  | "REJECTED"
  | "SCHEMA_INVALID"
  | "SOURCE_UNAVAILABLE"
  | "MALFORMED";

export type ReadSourceClass = "AOSCLOUD_OEM" | "AOSCLOUD_BRAKE_SP1" | "BRAKE_BACKEND";

export interface ReadSourceReference {
  owner: string;
  sourceClass: ReadSourceClass;
  contractClass: "CONTRACT_SYNTHETIC";
  freshnessPolicyId: string;
}

export interface ReadObservation<T> {
  value: T | null;
  source: ReadSourceReference;
  sourceTimestamp: string | null;
  readCompletedAt: string;
  state: ReadObservationState;
  transport: TransportClassification;
  reason?: string;
}

export type Clock = () => string;

export function readObservation<T>(input: ReadObservation<T>): ReadObservation<T> {
  return Object.freeze({ ...input });
}

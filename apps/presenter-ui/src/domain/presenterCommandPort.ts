export type DemoAction = "prepare-demo" | "create" | "start-vms" | "stop-vms" | "provision" | "start-simulation" | "stop-simulation" | "connect-test" | "reconnect-test" | "park" | "resume" | "reset"
  | "prepare" | "unpack" | "sign" | "upload" | "publish" | "approve" | "inspect" | "verify" | "cloud-status" | "observe-test" | "test-logs" | "cloud-access"
  | "service-prepare" | "service-publish" | "service-observe" | "service-assign" | "backend-reset" | "cloud-inspect" | "cloud-choose" | "cloud-select" | "cloud-check" | "cloud-prepare" | "workspace-restore";
export interface DemoCommand { action: DemoAction; image?: string; version?: string; profile?: "v1" | "v2" | "v3"; team?: "brake" | "tire"; release?: string; serviceId?: string; selectionId?: string }
export interface DemoJob { id: string; action: DemoAction; cloudDomain?: string; runId?: string | null; version?: string; profile?: string; team?: "brake" | "tire"; release?: string; serviceId?: string; state: string; startedAt: string; finishedAt?: string; reason?: string;
  progress: string[]; results: { operation: string; state: string; message: string; facts: Record<string, unknown> }[] }
export interface WorkspacePlacement { state?: string; observedAt?: string; retryPending?: boolean; problems?: string[]; zOrder?: { state: string; observedAt?: string; repairs?: number } }
export interface OperationSession { sessionId: string; cloudDomain?: string; active: string | null; uncertain: boolean; jobs: DemoJob[]; recordedRequestIds?: string[]; workspace?: WorkspacePlacement | null; workspaceBusy?: boolean;
  sourceRecoveryBusy?: boolean; sourceRecovery?: { state?: string; phase?: string; reason?: string; finishedAt?: string } | null }
export interface PresenterCommandPort {
  read(): Promise<OperationSession>;
  submit(command: DemoCommand, requestId: string, sessionId: string): Promise<DemoJob>;
}

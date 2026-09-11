export type DemoAction = "prepare-demo" | "create" | "start-vms" | "stop-vms" | "provision" | "start-simulation" | "stop-simulation" | "connect-test" | "reconnect-test" | "park" | "resume" | "reset"
  | "prepare" | "unpack" | "sign" | "upload" | "approve" | "inspect" | "verify" | "cloud-status" | "observe-test" | "test-logs" | "cloud-access";
export interface DemoCommand { action: DemoAction; image?: string; version?: string; profile?: "v1" | "v2" | "v3" }
export interface DemoJob { id: string; action: DemoAction; runId?: string | null; version?: string; profile?: string; state: string; startedAt: string; finishedAt?: string; reason?: string;
  progress: string[]; results: { operation: string; state: string; message: string; facts: Record<string, unknown> }[] }
export interface OperationSession { sessionId: string; active: string | null; uncertain: boolean; jobs: DemoJob[] }
export interface PresenterCommandPort {
  read(): Promise<OperationSession>;
  submit(command: DemoCommand, requestId: string, sessionId: string): Promise<DemoJob>;
}

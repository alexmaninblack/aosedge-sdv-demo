import type { DemoCommand, DemoJob, OperationSession, PresenterCommandPort } from "../../domain/presenterCommandPort";

export class LocalPresenterCommandAdapter implements PresenterCommandPort {
  async read(): Promise<OperationSession> {
    const response = await fetch("/api/presenter/operations", { cache: "no-store", signal: AbortSignal.timeout(6000) });
    if (!response.ok) throw new Error("Native session unavailable");
    const value = await response.json();
    if (typeof value.sessionId !== "string" || !Array.isArray(value.jobs) || typeof value.uncertain !== "boolean") throw new Error("Invalid session response");
    return value;
  }
  async submit(command: DemoCommand, requestId: string, sessionId: string): Promise<DemoJob> {
    // Same-origin backend only. No native-session capability enters this bundle.
    const response = await fetch("/api/presenter/operations", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...command, requestId, sessionId }), signal: AbortSignal.timeout(8000) });
    if (response.status === 400 || response.status === 403 || response.status === 409) throw new Error("REJECTED");
    if (response.status !== 202) throw new Error("UNCERTAIN");
    const result = await response.json();
    if (result.id !== requestId) throw new Error("UNCERTAIN");
    return result;
  }
}

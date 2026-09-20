// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { useEffect, useState } from "react";
import type { DemoJob } from "../domain/presenterCommandPort";

/** Short-lived acknowledgement of an actual receipt; never inferred from an empty controller. */
export function FinishAcknowledgement({ jobs, noController, emptyMessage }: { jobs: DemoJob[]; noController: boolean; emptyMessage?: string }) {
  const [now, setNow] = useState(Date.now());
  const [dismissed, setDismissed] = useState<string>();
  const job = [...jobs].reverse().find(row => row.action === "reset" && row.state === "COMPLETED"
    && row.results.some(result => result.operation === "demo.retire" && result.state === "COMPLETED"));
  const age = now - Date.parse(job?.finishedAt ?? "");
  const visible = noController && job && job.id !== dismissed && age >= 0 && age < 60000;
  useEffect(() => {
    if (!noController || !job) return;
    setNow(Date.now());
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [noController, job?.id]);
  if (!visible) return emptyMessage ? <p>{emptyMessage}</p> : null;
  return <div className="studio-finish-ack" role="status"><span><strong>Demo finished</strong> · {job.results.find(result => result.operation === "demo.retire" && result.state === "COMPLETED")?.message}</span><button onClick={() => setDismissed(job.id)}>Dismiss</button></div>;
}

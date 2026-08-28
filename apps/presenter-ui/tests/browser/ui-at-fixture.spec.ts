import { expect, test, type Page } from "@playwright/test";

type Interaction = "details" | "logs" | "action";
interface UiCase { id: number; title: string; fixture: string; view?: "global" | "platform" | "brake" | "tire"; expected: string; interaction?: Interaction; }

const cases: UiCase[] = [
  { id: 1, title: "Qualified full-screen composition", fixture: "ready", expected: "Reserved for native CARLA window" },
  { id: 2, title: "Fixed evidence, fixed team context and version-only scrolling", fixture: "ready", expected: "TEXT-ONLY NATIVE TERMINAL" },
  { id: 3, title: "Shared header and audience terminology", fixture: "ready", expected: "Current vehicle · Test Vehicle" },
  { id: 4, title: "Independent team-perspective navigation", fixture: "ready", view: "brake", expected: "Develops and releases predictive brake-maintenance Services" },
  { id: 5, title: "Release Authority remains separate", fixture: "ready", expected: "Independent from producer teams" },
  { id: 6, title: "Independent operations and scoped conflicts", fixture: "blocked", view: "brake", expected: "Candidate remains visible and inspectable" },
  { id: 7, title: "Details overlay preserves context", fixture: "ready", expected: "Read-only · selected release and stage context preserved", interaction: "details" },
  { id: 8, title: "Global Current Vehicle", fixture: "ready", expected: "Current vehicle · Test Vehicle" },
  { id: 9, title: "Test-to-Production handover", fixture: "changing", expected: "Changing vehicle..." },
  { id: 10, title: "Production-to-Test handover", fixture: "ready", expected: "Test Vehicle" },
  { id: 11, title: "Failed or uncertain handover", fixture: "unavailable", expected: "Current Vehicle unavailable" },
  { id: 12, title: "Platform FOTA and Safe Stop", fixture: "safe-stop", expected: "Waiting for Safe Stop before application" },
  { id: 13, title: "Service SOTA while driving", fixture: "ready", view: "brake", expected: "In-motion update allowed" },
  { id: 14, title: "Common five-stage release template", fixture: "ready", expected: "Production rollout and live operation" },
  { id: 15, title: "VDP v1-v3 story", fixture: "ready", expected: "VDP v3" },
  { id: 16, title: "Brake v1-v3 story", fixture: "ready", view: "brake", expected: "Brake v3" },
  { id: 17, title: "Tire v1 story", fixture: "ready", view: "tire", expected: "Tire v1" },
  { id: 18, title: "Dependencies and independent evolution", fixture: "blocked", view: "brake", expected: "Blocked · requires VDP v2" },
  { id: 19, title: "Protected action and credential boundary", fixture: "ready", expected: "Impossible in IMP-01", interaction: "action" },
  { id: 20, title: "Authoritative result, concurrency and reconciliation", fixture: "uncertain", view: "global", expected: "blind retry unavailable" },
  { id: 21, title: "Details content and stage binding", fixture: "ready", expected: "Deterministic fixture · current · not live AosEdge state", interaction: "details" },
  { id: 22, title: "Source, freshness and integrity", fixture: "stale", expected: "Last observation is outside the accepted freshness window" },
  { id: 23, title: "Access, dependency and quota presentation", fixture: "ready", view: "brake", expected: "Approved Service quota", interaction: "details" },
  { id: 24, title: "Disclosure, redaction and copy boundary", fixture: "ready", expected: "credentials, raw responses, private paths and private identities are excluded", interaction: "details" },
  { id: 25, title: "Perspective and evidence isolation", fixture: "ready", view: "brake", expected: "Current released Brake evidence remains separate from Platform and Tire state" },
  { id: 26, title: "Runtime Isolation Evidence", fixture: "ready", view: "tire", expected: "Runtime Isolation Evidence" },
  { id: 27, title: "Operational Logs workflow", fixture: "ready", view: "brake", expected: "This fixture cannot request, refresh or delete an external log", interaction: "logs" },
  { id: 28, title: "Separate state layers and source attribution", fixture: "uncertain", view: "global", expected: "authoritative reconciliation required" },
  { id: 29, title: "Scoped vocabulary and safe next action", fixture: "failed", view: "tire", expected: "Tire-owned fixture source unavailable" },
  { id: 30, title: "Known progress without resubmission", fixture: "submitting", expected: "VDP v1 · SUBMITTING" },
  { id: 31, title: "Vehicle offline and reconnect", fixture: "offline", view: "brake", expected: "Current queue occupancy is not observable while offline" },
  { id: 32, title: "Presenter-to-AosCloud failure", fixture: "stale", expected: "Stale authoritative state" },
  { id: 33, title: "Uncertain-operation reconciliation", fixture: "uncertain", view: "global", expected: "Outcome unknown" },
  { id: 34, title: "Run-exclusive recovery", fixture: "recovery", view: "global", expected: "resume from first unproven step" },
  { id: 35, title: "Auxiliary-surface failure states", fixture: "failed", view: "tire", expected: "ERROR" },
  { id: 36, title: "Stable accessible failure presentation", fixture: "failed", view: "tire", expected: "Tire v1 · FAILED" },
  { id: 37, title: "One evidence context and four-link chain", fixture: "ready", view: "global", expected: "Vehicle event · deterministic Test exercise" },
  { id: 38, title: "Test/Production exercise modes and no replay", fixture: "production", expected: "Show released behavior" },
  { id: 39, title: "Release-specific live evidence", fixture: "production", view: "brake", expected: "Brake v1" },
  { id: 40, title: "Fingerprints and source-owned time", fixture: "ready", view: "global", expected: "correlated fixture fingerprint" },
  { id: 41, title: "Duplicate, ordering and Service restart", fixture: "reconnected", view: "tire", expected: "Synchronized · bounded owner summary received" },
  { id: 42, title: "Test reference versus current Production evidence", fixture: "production", expected: "Current vehicle · Production Vehicle" },
  { id: 43, title: "Incomplete or contradictory evidence chain", fixture: "stale", expected: "STALE" },
  { id: 44, title: "Lifecycle-aware environment preflight", fixture: "ready", view: "global", expected: "Qualification Status · QUALIFIED" },
  { id: 45, title: "M0 manufacturing output", fixture: "m0", view: "global", expected: "Manufacturing output" },
  { id: 46, title: "M1 provisioning establishes G0", fixture: "m1", view: "global", expected: "Provision managed vehicles" },
  { id: 47, title: "R0 terminal reset and recovery", fixture: "r0", view: "global", expected: "R0 complete · READY_FOR_M0" },
  { id: 48, title: "Independent VDP/Brake releases and derived milestones", fixture: "production", view: "global", expected: "G3 capability · 2 of 2 releases ready" },
  { id: 49, title: "Composed workspace ownership and local restoration", fixture: "ready", expected: "Browser content intentionally absent" },
  { id: 50, title: "Global Demo Lifecycle page and Qualification Status", fixture: "ready", view: "global", expected: "Demo Lifecycle" },
];

async function selectView(page: Page, view: UiCase["view"]) {
  if (view === "global") await page.getByRole("button", { name: /AosEdge Software Evolution Demo/ }).click();
  if (view && view !== "global" && view !== "platform") await page.locator(`[data-team="${view}"]`).click();
}

for (const uiCase of cases) {
  const id = String(uiCase.id).padStart(3, "0");
  test(`UI-AT-${id} — ${uiCase.title}`, async ({ page }) => {
    await page.goto(`/?fixture=${uiCase.fixture}`);
    await selectView(page, uiCase.view);
    if (uiCase.interaction === "details") await page.getByRole("button", { name: "Details" }).first().click();
    if (uiCase.interaction === "logs") await page.getByRole("button", { name: /Operational Logs/ }).first().click();
    if (uiCase.interaction === "action") await page.getByRole("button", { name: "Sign and submit prepared candidate" }).first().click();
    await expect(page.getByText(uiCase.expected, { exact: false }).first()).toBeVisible();
    await expect(page.getByText(/FIXTURE ONLY/)).toBeVisible();
  });
}

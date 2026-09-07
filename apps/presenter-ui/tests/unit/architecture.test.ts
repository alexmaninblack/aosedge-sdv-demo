import { describe, expect, it } from "vitest";
import packageJson from "../../package.json";

const sources = import.meta.glob("../../src/**/*.{ts,tsx}", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

describe("module architecture", () => {
  it("allows fixture adapter wiring only at the application composition root", () => {
    const offenders = Object.entries(sources)
      .filter(([path, source]) => source.includes("adapters/fixtures") && !path.endsWith("app/composition/createPresenterDependencies.ts"));
    expect(offenders.map(([path]) => path)).toEqual([]);
  });

  it("allows read-only adapter wiring only at the application composition root", () => {
    const offenders = Object.entries(sources)
      .filter(([path, source]) => source.includes("adapters/read-only") && !path.endsWith("app/composition/createPresenterDependencies.ts"));
    expect(offenders.map(([path]) => path)).toEqual([]);
  });

  it("keeps Release Authority outside producer feature code", () => {
    const offenders = Object.entries(sources)
      .filter(([path, source]) => /features\/(platform-team|brake-team|tire-team)\//.test(path) && /release-authority|ReleaseAuthority/.test(source));
    expect(offenders.map(([path]) => path)).toEqual([]);
  });

  it("rejects browser-owned authority, external transports and persistence", () => {
    const forbidden = /\b(fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|localStorage|sessionStorage|indexedDB|serviceWorker)\b/;
    // Only the fixed same-origin local adapters own HTTP. No persistence.
    const offenders = Object.entries(sources).filter(([path, source]) => forbidden.test(
      /adapters\/local\/LocalPresenter(Read|Command)Adapter\.ts$/.test(path) ? source.replace(/\bfetch\b/g, "localRequest") : source));
    expect(offenders.map(([path]) => path)).toEqual([]);
  });

  it("allows POST only in the fixed local command adapter and no privileged material field", () => {
    const mutation = /["'](?:POST|PATCH|PUT|DELETE)["']/;
    const privilegedField = /\b(?:privateKey|private_key|certificate|certificateContent|token|credential|authHeader|authorizationHeader|password|rawResponse|helperCapability)\s*[?:]/i;
    expect(Object.entries(sources).filter(([path, source]) => mutation.test(source) && !path.endsWith("adapters/local/LocalPresenterCommandAdapter.ts")).map(([path]) => path)).toEqual([]);
    const command = Object.entries(sources).find(([path]) => path.endsWith("adapters/local/LocalPresenterCommandAdapter.ts"))![1];
    expect(command).not.toMatch(/["'](?:PATCH|PUT|DELETE)["']|https?:\/\//);
    expect(command.match(/fetch\("\/api\/presenter\/operations"/g)).toHaveLength(2);
    expect(Object.entries(sources).filter(([, source]) => privilegedField.test(source)).map(([path]) => path)).toEqual([]);
  });

  it("keeps runtime dependencies limited and exact", () => {
    expect(Object.keys(packageJson.dependencies)).toEqual(["react", "react-dom"]);
    for (const version of [...Object.values(packageJson.dependencies), ...Object.values(packageJson.devDependencies)]) {
      expect(version).not.toMatch(/^[~^]/);
    }
    expect(JSON.stringify(packageJson)).not.toMatch(/redux|zustand|mobx|recoil|jotai|xstate|storybook/i);
  });
});

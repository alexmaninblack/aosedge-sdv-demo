import { describe, expect, it } from "vitest";
import packageJson from "../../package.json";

const sources = import.meta.glob("../../src/**/*.{ts,tsx}", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

describe("module architecture", () => {
  it("allows fixture adapter wiring only at the application composition root", () => {
    const offenders = Object.entries(sources)
      .filter(([path, source]) => source.includes("adapters/fixtures") && !path.endsWith("app/composition/createPresenterDependencies.ts"));
    expect(offenders.map(([path]) => path)).toEqual([]);
  });

  it("keeps Release Authority outside producer feature code", () => {
    const offenders = Object.entries(sources)
      .filter(([path, source]) => /features\/(platform-team|brake-team|tire-team)\//.test(path) && /release-authority|ReleaseAuthority/.test(source));
    expect(offenders.map(([path]) => path)).toEqual([]);
  });

  it("rejects browser-owned authority and external transports", () => {
    const forbidden = /\b(fetch|XMLHttpRequest|WebSocket|EventSource|localStorage|sessionStorage|indexedDB|serviceWorker)\b/;
    const offenders = Object.entries(sources).filter(([, source]) => forbidden.test(source));
    expect(offenders.map(([path]) => path)).toEqual([]);
  });

  it("keeps runtime dependencies limited and exact", () => {
    expect(Object.keys(packageJson.dependencies)).toEqual(["react", "react-dom"]);
    for (const version of [...Object.values(packageJson.dependencies), ...Object.values(packageJson.devDependencies)]) {
      expect(version).not.toMatch(/^[~^]/);
    }
    expect(JSON.stringify(packageJson)).not.toMatch(/redux|zustand|mobx|recoil|jotai|xstate|storybook/i);
  });
});

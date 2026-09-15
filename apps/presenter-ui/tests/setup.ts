import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Layout is covered in real-browser tests; jsdom has no ResizeObserver.
globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };

afterEach(() => cleanup());

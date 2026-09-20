// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { afterEach, expect, test } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { formatResource } from "../../src/domain/resourceFormatting";
import { Monitoring } from "../../src/app/StudioReadViews";

afterEach(cleanup);
const time = "2026-09-19T23:59:00Z";
const metric = (value: any[], state = "CURRENT") => ({ state, unit: "bytes", value });
const sample = (value: number | null, partition?: string) => ({ value, partition, nodeId: "node", time });
function observation(metrics: any) {
  return { error: false, busy: false, reason: null, refresh() {}, data: { readCompletedAt: time, monitoring: { state: "CURRENT", value: metrics } } };
}
test.each(["disk", "usedDisk", "inTraffic", "outTraffic"])("%s formats verified bytes, not rates or unitless guesses", key => {
  expect(formatResource(0, "bytes", key)).toBe("0 B");
  expect(formatResource(1, "bytes", key)).toBe("1 B");
  expect(formatResource(138240, "bytes", key)).toBe("135 KiB");
  expect(formatResource(1048576, "bytes", key)).toBe("1 MiB");
  expect(formatResource(1073741824, "bytes", key)).toBe("1 GiB");
  expect(formatResource(1023, "bytes", key)).toBe("1,023 B");
  expect(formatResource(0.001, "bytes", key)).toBe("<0.01 B");
  expect(formatResource(null, "bytes", key)).toBe("Not reported");
  expect(formatResource(1024, null, key)).toBe("1024 · unit not specified");
  expect(formatResource(10, "DMIPS", "cpu")).toBe("10 DMIPS");
  expect(formatResource(1048576, "bytes", "ram")).toBe("1 MiB");
});
test("all four controller partitions and four instance readings remain available without paging", () => {
  const disk = [sample(138240, "states"), sample(417792, "storages"), sample(94048256, "var"), sample(621244416, "workdirs"),
    ...["brake", "tire"].flatMap(serviceId => [sample(0, "states"), sample(102400, "storages")].map(row => ({ ...row, serviceId, subjectId: serviceId + "-subject", instance: 0 })))];
  render(<Monitoring observation={observation({ disk: metric(disk) })} />);
  fireEvent.click(screen.getByRole("button", { name: "Disk" }));
  expect(screen.getByText("135 KiB")).toBeVisible();
  expect(screen.getByText("592.46 MiB")).toBeVisible();
  expect(screen.queryByRole("navigation", { name: "Resource pages" })).not.toBeInTheDocument();
  expect(screen.getAllByRole("article")).toHaveLength(4);
  fireEvent.click(screen.getByRole("button", { name: "Service instance" }));
  expect(screen.getAllByText("0 B")).toHaveLength(2);
  expect(screen.getAllByText("100 KiB")).toHaveLength(2);
  expect(screen.getAllByText(/Node: node · Subject: brake-subject/)).toHaveLength(2);
  expect(screen.queryByText(/unit not specified/)).not.toBeInTheDocument();
});
test("old traffic remains daily volume with local-network context, never labelled today's live throughput", () => {
  render(<Monitoring observation={observation({ inTraffic: metric([sample(0)], "STALE"), outTraffic: metric([sample(null)], "INCOMPLETE") })} />);
  fireEvent.click(screen.getByRole("button", { name: "Inbound" }));
  expect(screen.getByText("Received · daily total · Controller")).toBeVisible();
  expect(screen.getByText("0 B · last known / incomplete")).toBeVisible();
  expect(screen.getByText(/Local\/private network traffic is excluded/)).toBeVisible();
  expect(screen.getByText(/source sample's accounting day, not a transfer rate/)).toBeVisible();
  expect(screen.queryByText(/Received today|bytes\/s|No traffic/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Outbound" }));
  expect(screen.getByText("Sent · daily total · Controller")).toBeVisible();
  expect(screen.getByText("Not reported · last known / incomplete")).toBeVisible();
});

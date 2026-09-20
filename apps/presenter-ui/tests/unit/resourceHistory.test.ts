// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import { expect, test } from "vitest";
import { diskRows, windowPoints } from "../../src/domain/resourceHistory";
import { selectGraph } from "../../src/app/ResourceGraphs";
const t = "2026-09-20T10:00:00Z", now = Date.parse(t);
const metric = (value: any[]) => ({ value, state: "CURRENT", unit: null });
test("Disk resolves aliases per node, subject, instance and partition without adding them", () => {
  const sample = { nodeId: "n", value: 0, time: t, partition: "states" };
  const rows = diskRows({ usedDisk: metric([sample]), disk: metric([{ ...sample, parameter: "disk" },
    { ...sample, serviceId: "s", subjectId: "a", instance: 0 }, { ...sample, partition: "var" }]) });
  expect(rows).toHaveLength(3); expect(rows[0].sample.value).toBe(0); expect(rows[0].conflict).toBe(false);
  expect(rows[0].sources).toEqual(["usedDisk", "disk"]);
  expect(diskRows({ usedDisk: metric([sample]), disk: metric([{ ...sample, value: 1 }]) })[0].conflict).toBe(true);
});
test("History is anchored to now, deduplicates instants and leaves conflicts and missing values as gaps", () => {
  expect(windowPoints([[t, 0], ["2026-09-20T11:00:00+01:00", 0], ["2026-09-20T09:54:00Z", 3]], now)).toEqual([[now, 0]]);
  expect(windowPoints([[t, 1], [t, 2]], now)).toEqual([[now, null]]);
  expect(windowPoints([[t, 1]], now + 301000)).toEqual([]);
});
test("Graph ownership never combines nodes or attributes an old subject to a current service", () => {
  const inventory: any = { nodes: { value: [{ node_id: "n" }] }, teamServiceIds: { brake: "b" }, services: { value: [{ service: { id: "b" }, subject: "current", instances: { value: [{ instance_id: 0 }] } }] } };
  const model: any = { error: false, data: { monitoring: { value: { cpu: metric([{ nodeId: "n", value: 0, time: t }]) } } },
    history: { error: false, data: { history: { value: { series: [{ nodeId: "n", serviceId: "b", subjectId: "old", instance: 0, metric: "cpu", points: [[t, 9]], unit: null, state: "CURRENT" }] } } } } };
  expect(selectGraph(model, inventory, "controller", "cpu").points).toEqual([[t, 0]]);
  expect(selectGraph(model, inventory, "brake", "cpu").points).toEqual([]);
  expect(selectGraph(model, inventory, "controller", "cpu").unbound).toBe(true);
});

test("native latest measurementType is metadata, not a different CPU/RAM owner from dashboard history", () => {
  const inventory: any = { nodes: { value: [{ node_id: "n" }] } };
  const model: any = { error: false, data: { monitoring: { value: { cpu: { ...metric([{ nodeId: "n", measurementType: "node", parameter: "cpu", value: 3, time: t }]), unit: "DMIPS" } } } },
    history: { error: false, data: { history: { value: { series: [{ nodeId: "n", metric: "cpu", points: [[t, 3]], unit: "DMIPS", state: "CURRENT" }] } } } } };
  const selected = selectGraph(model, inventory, "controller", "cpu");
  expect(selected.ambiguous).toBe(false); expect(windowPoints(selected.points, now)).toEqual([[now, 3]]);
});

test("a successful history remains current when the independent latest read fails", () => {
  const inventory: any = { nodes: { value: [{ node_id: "n" }] } };
  const model: any = { error: true, data: null, history: { error: false, data: { history: { state: "CURRENT", value: { series: [
    { nodeId: "n", metric: "ram", unit: "bytes", points: [[t, 1048576]], state: "CURRENT" },
  ] } } } } };
  const selected = selectGraph(model, inventory, "controller", "ram");
  expect(selected.stale).toBe(false); expect(selected.unit).toBe("bytes"); expect(selected.points).toEqual([[t, 1048576]]);
  model.history.data.history.value.series = [];
  model.data = { monitoring: { value: { ram: { ...metric([{ nodeId: "n", value: 1048576, time: t }]), unit: "bytes" } } } };
  expect(selectGraph(model, inventory, "controller", "ram").stale).toBe(true);
});

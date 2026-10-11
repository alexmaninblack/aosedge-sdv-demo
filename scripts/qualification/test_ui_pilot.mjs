// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import test from 'node:test';
import { actions, mutation, owners, idle, acknowledgement } from './ui_pilot.mjs';
const id = '01234567-89ab-cdef-0123-456789abcdef';
const state = () => ({ identity: { localVmId: id, unitId: id, nodeId: id,
  systemUid: id.replaceAll('-', '') }, candidate: 'a'.repeat(64), dockerEngineId: id,
  dataPreserved: true, controller: 'STOPPED', backends: { brake: 'STOPPED', tire: 'STOPPED' },
  source: 'STOPPED', currentVehicle: null });
test('only the four ordered UI actions are allowed', () => {
  actions.forEach((action, index) => assert.equal(mutation({ action, requestId: id, sessionId: id }, index, id).action, action));
});
test('extra fields, wrong order, identity and fifth mutation are rejected', () => {
  const body = { action: actions[0], requestId: id, sessionId: id };
  for (const key of ['target', 'force', 'certificate', 'release', 'team'])
    assert.throws(() => mutation({ ...body, [key]: true }, 0, id));
  assert.throws(() => mutation(body, 1, id));
  assert.throws(() => mutation(body, 4, id));
  assert.throws(() => mutation(body, 0, 'different-session'));
  assert.throws(() => mutation({ ...body, requestId: 'bad' }, 0, id));
  assert.throws(() => mutation(null, 0, id));
});
test('stopped owners must retain the exact identities, journal and shared engine', () => {
  const before = state();
  owners(state(), before, 'STOPPED');
  for (const key of ['identity', 'candidate', 'dockerEngineId', 'dataPreserved', 'controller', 'backends', 'source'])
    assert.throws(() => owners({ ...state(), [key]: null }, before, 'STOPPED'));
  assert.throws(() => owners({ ...state(), currentVehicle: 'test' }, before, 'STOPPED'));
  assert.throws(() => owners({ ...state(), identity: { ...before.identity, unitId: id.replace('0', '1') } }, before, 'STOPPED'));
  assert.throws(() => owners(state(), { ...before, identity: {} }, 'STOPPED'));
});
test('connection is stationary Manual, not an implicit resume or stale frame', () => {
  const before = state();
  const running = { ...before, controller: 'RUNNING', backends: { brake: 'RUNNING', tire: 'RUNNING' },
    source: 'SELECTED_NOT_PROBED', currentVehicle: 'test',
    control: { fresh: true, held: false, mode: 'MANUAL', speed: 0, brake: 1 } };
  owners(running, before, 'RUNNING', true);
  for (const [key, value] of [['fresh', false], ['held', true], ['mode', 'Manual'], ['mode', 'AUTOPILOT'], ['speed', 2], ['speed', -2], ['brake', 0], ['brake', 100]])
    assert.throws(() => owners({ ...running, control: { ...running.control, [key]: value } }, before, 'RUNNING', true));
});
test('submission waits for complete owner quiescence without ignoring recovery failures', () => {
  const value = { sessionId: id, uncertain: false, active: null };
  assert.equal(idle(value, id), true);
  for (const key of ['workspaceBusy', 'sourceRecoveryBusy'])
    assert.equal(idle({ ...value, [key]: true }, id), false);
  assert.equal(idle({ ...value, active: id }, id), false);
  assert.equal(idle({ ...value, workspace: { retryPending: true } }, id), false);
  assert.throws(() => idle({ ...value, uncertain: true }, id));
  assert.throws(() => idle(value, 'changed'));
  for (const state of ['ATTEMPTED', 'FAILED'])
    assert.throws(() => idle({ ...value, sourceRecovery: { state } }, id));
});
test('rejected submission fails immediately instead of polling an absent job', () => {
  acknowledgement(202, { id }, { requestId: id });
  for (const status of [400, 403, 409])
    assert.throws(() => acknowledgement(status, null, { requestId: id }), /UI_ACTION_REJECTED/);
  for (const status of [200, 500, 503])
    assert.throws(() => acknowledgement(status, null, { requestId: id }), /SUBMISSION_UNCERTAIN/);
  assert.throws(() => acknowledgement(202, { id: 'other' }, { requestId: id }), /SUBMISSION_UNCERTAIN/);
});

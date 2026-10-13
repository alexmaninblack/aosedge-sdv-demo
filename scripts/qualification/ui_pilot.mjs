// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Test-only real browser driver. Never submits a product action outside the UI.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

export const actions = ['start-demo', 'start-simulation', 'connect-test', 'stop-demo'];
const origin = 'http://127.0.0.1:18080';
const uuid = /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/;
export function mutation(body, index, session) {
  assert(body && Object.keys(body).every(k => ['action', 'requestId', 'sessionId'].includes(k)), 'ACTION_FIELDS_REJECTED');
  assert(body.action === actions[index], 'ACTION_ORDER_REJECTED');
  assert(uuid.test(body.requestId) && body.sessionId === session, 'ACTION_BINDING_REJECTED');
  return { action: body.action, requestId: body.requestId, sessionId: body.sessionId };
}
export function idle(value, session) {
  assert(value.sessionId === session && !value.uncertain, 'UNKNOWN_OPERATION');
  assert(!['ATTEMPTED', 'FAILED'].includes(value.sourceRecovery?.state), 'SOURCE_RECOVERY_UNRESOLVED');
  return value.active === null && !value.workspaceBusy && !value.sourceRecoveryBusy
    && !value.workspace?.retryPending;
}
export function acknowledgement(status, receipt, request) {
  assert(![400, 403, 409].includes(status), 'UI_ACTION_REJECTED');
  assert.equal(status, 202, 'SUBMISSION_UNCERTAIN_NO_REPLAY');
  assert.equal(receipt?.id, request.requestId, 'SUBMISSION_UNCERTAIN_NO_REPLAY');
}
export function owners(value, before, state, connected = false) {
  assert(before?.identity && Object.keys(before.identity).length === 4
    && ['localVmId', 'unitId', 'nodeId'].every(key => uuid.test(before.identity[key]))
    && /^[a-f0-9]{32}$/.test(before.identity.systemUid), 'IDENTITY_REQUIRED');
  assert(/^[a-f0-9]{64}$/.test(before.candidate) && uuid.test(before.dockerEngineId), 'OWNER_PIN_REQUIRED');
  assert.deepEqual(value.identity, before.identity, 'IDENTITY_CHANGED');
  assert.equal(value.candidate, before.candidate, 'CANDIDATE_CHANGED');
  assert.equal(value.dockerEngineId, before.dockerEngineId, 'ENGINE_CHANGED');
  assert.equal(value.dataPreserved, true, 'JOURNAL_LOST');
  assert.equal(value.controller, state, 'CONTROLLER_STATE_MISMATCH');
  assert.deepEqual(value.backends, { brake: state, tire: state }, 'BACKEND_STATE_MISMATCH');
  if (state === 'STOPPED') {
    assert.equal(value.source, 'STOPPED', 'SOURCE_NOT_STOPPED');
    assert.equal(value.currentVehicle, null, 'SOURCE_STILL_ATTACHED');
  }
  if (connected) {
    assert.equal(value.currentVehicle, 'test', 'SOURCE_NOT_ATTACHED');
    const c = value.control;
    assert(c?.fresh === true && c.held === false && c.mode === 'MANUAL'
      && typeof c.speed === 'number' && Math.abs(c.speed) <= .5 && typeof c.brake === 'number'
      && c.brake >= .99 && c.brake <= 1,
    'STATIONARY_MANUAL_REQUIRED');
  }
}

export async function main(inputPath) {
  process.umask(0o077);
  const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const require = createRequire(path.join(input.repository, 'apps/presenter-ui/package.json'));
  const { chromium, expect } = require('@playwright/test');
  const output = input.records;
  const record = value => {
    const fd = fs.openSync(path.join(output, 'ui-events.jsonl'), 'a', 0o600);
    try {
      fs.writeSync(fd, JSON.stringify({ at: new Date().toISOString(), ...value }) + '\n');
      fs.fsyncSync(fd);
    } finally { fs.closeSync(fd); }
  };
  const observed = label => JSON.parse(execFileSync(input.python, [input.helper,
    '--config', input.config, '--journey', input.journey, '--test', input.test,
    '--observe', label], { encoding: 'utf8', timeout: 55000, maxBuffer: 65536 }));
  let browser, page, session, before, refused = false;
  const sent = [], stages = [];
  let current = 'browser-open', failed = false;
  // Close the owned browser before the outer watchdog can end this process.
  const deadline = setTimeout(() => {
    failed = true;
    record({ stage: current, state: 'PILOT_DEADLINE' });
    if (browser) void browser.close();
  }, 600000);
  deadline.unref();
  async function stage(name, action) {
    current = name;
    const start = performance.now();
    record({ stage: name, state: 'STARTED' });
    console.log(`${name}: started`);
    await action();
    const seconds = +( (performance.now() - start) / 1000 ).toFixed(3);
    stages.push({ stage: name, outcome: 'PASS', seconds });
    record(stages.at(-1));
    console.log(`${name}: PASS (${seconds}s)`);
  }
  async function read(resource) {
    const response = await page.request.get(`${origin}/api/presenter/${resource}`, { timeout: 15000 });
    assert(response.ok(), 'READ_UNAVAILABLE');
    return response.json(); // Not retained as raw evidence.
  }
  async function operate(name, click) {
    const index = sent.length;
    const readyDeadline = performance.now() + 30000;
    while (!idle(await read('operations'), session)) {
      assert(performance.now() < readyDeadline, 'OWNER_NOT_IDLE');
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    // Observe this button's actual submission response, not just network intent.
    // A rejected POST has no job to poll; waiting three minutes hides the fault.
    const response = page.waitForResponse(value => {
      const request = value.request();
      return request.method() === 'POST' && request.url() === `${origin}/api/presenter/operations`
        && request.postDataJSON()?.action === name;
    }, { timeout: 10000 });
    const [, reply] = await Promise.all([click(), response]);
    await expect.poll(() => sent.length, { timeout: 8000 }).toBe(index + 1);
    const request = sent[index];
    assert.equal(request.action, name);
    record({ action: name, requestId: request.requestId, httpStatus: reply.status() });
    acknowledgement(reply.status(), reply.status() === 202 ? await reply.json() : null, request);
    const deadline = performance.now() + 180000;
    while (true) {
      const value = await read('operations');
      assert(value.sessionId === session && !value.uncertain && !refused, 'UNKNOWN_OPERATION');
      const job = value.jobs.find(row => row.id === request.requestId);
      if (job && !['ACCEPTED', 'RUNNING'].includes(job.state)) {
        assert.equal(job.state, 'COMPLETED', 'PRODUCT_OPERATION_FAILED');
        assert(value.workspace?.state !== 'WAITING_FOR_UNLOCK', 'TARGET_DESKTOP_LOCKED');
        if (idle(value, session)) {
          record({ action: name, requestId: request.requestId, productState: job.state });
          break;
        }
      }
      assert(performance.now() < deadline, 'OPERATION_DEADLINE');
      await new Promise(resolve => setTimeout(resolve, 1000)); // Observe the original job; never resubmit.
    }
  }
  const button = name => page.getByRole('button', { name, exact: true });
  async function shot(name) {
    await page.screenshot({ path: path.join(output, name + '.png'),
      mask: [page.locator('input, textarea')], fullPage: true });
  }
  try {
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    page = await context.newPage();
    page.setDefaultTimeout(30000);
    await context.route('**/*', async route => {
      const request = route.request(), url = new URL(request.url());
      if (url.origin !== origin) { refused = true; return route.abort(); }
      if (request.method() === 'GET') return route.continue();
      try {
        assert(request.method() === 'POST' && url.pathname === '/api/presenter/operations', 'MUTATION_ENDPOINT_REJECTED');
        const value = mutation(request.postDataJSON(), sent.length, session);
        assert(!sent.some(row => row.requestId === value.requestId), 'REPEATED_REQUEST');
        record({ state: 'DISPATCH_INTENT', ...value }); // Durable intent before network dispatch.
        sent.push(value);
        return route.continue(); // No payload/header rewrite and no mocked response.
      } catch { refused = true; record({ state: 'FORBIDDEN_REQUEST_BLOCKED' }); return route.abort(); }
    });
    await stage('open-installed-presenter', async () => {
      await page.goto(origin + '/#native-browser');
      const ops = await read('operations'), snapshot = await read('snapshot');
      assert(snapshot.runId === input.test && ops.cloudDomain === 'aws-stage.epmp-aos.projects.epam.com'
        && !ops.uncertain && ops.active === null, 'PILOT_BINDING_REQUIRED');
      session = ops.sessionId;
      before = observed('before');
      owners(before, before, 'STOPPED');
      await expect(button('Start controller')).toBeEnabled();
    });
    await stage('start-controller', async () => {
      await operate('start-demo', () => button('Start controller').click());
      owners(observed('running'), before, 'RUNNING');
      await expect(button('Start simulator')).toBeEnabled();
    });
    await stage('start-simulator', async () => {
      await operate('start-simulation', () => button('Start simulator').click());
      await expect(button('Connect in Manual')).toBeEnabled();
    });
    await stage('connect-in-manual', async () => {
      await button('Connect in Manual').click();
      await operate('connect-test', () => page.getByRole('dialog').getByRole('button',
        { name: 'Connect in Manual', exact: true }).click());
      owners(observed('connected'), before, 'RUNNING', true);
    });
    await stage('installed-software-cards', async () => {
      for (const [name, text] of Object.entries(input.cards)) {
        await expect(button(name)).toContainText(text, { timeout: 65000 });
        await button(name).click();
        await expect(page.getByRole('dialog')).toBeVisible();
        await page.getByRole('dialog').getByRole('button', { name: 'Close dialog', exact: true }).click();
      }
      await shot('installed-cards');
    });
    async function stopDialog() {
      await button('Demo controls').click();
      await page.getByRole('dialog', { name: 'Demo controls', exact: true })
        .getByRole('button', { name: 'Stop demo and keep data', exact: true }).click();
      await expect(page.getByRole('dialog')).toContainText('Keep its Cloud identity');
    }
    await stage('cancel-stop-keeps-running', async () => {
      const count = sent.length;
      await stopDialog();
      await page.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
      assert.equal(sent.length, count, 'CANCEL_DISPATCHED_MUTATION');
      owners(observed('cancelled'), before, 'RUNNING', true);
      assert.equal(sent.length, count, 'CANCEL_DISPATCHED_MUTATION');
      await shot('cancelled-stop');
    });
    await stage('confirm-stop-keeps-test', async () => {
      await stopDialog();
      await operate('stop-demo', () => page.getByRole('dialog').getByRole('button',
        { name: 'Stop demo and keep data', exact: true }).click());
      owners(observed('stopped'), before, 'STOPPED');
      await expect(button('Start controller')).toBeEnabled();
      assert.deepEqual(sent.map(row => row.action), actions);
      assert.equal(refused, false);
      await shot('stopped-test-preserved');
    });
  } catch (error) {
    failed = true;
    const first = String(error.message).split('\n')[0];
    const code = /^[A-Z][A-Z0-9_]{1,100}$/.test(first) ? first : 'UI_PILOT_CHECK_FAILED';
    stages.push({ stage: current, outcome: 'FAIL', code });
    record(stages.at(-1));
    if (page && session) {
      const ops = await read('operations').catch(() => null);
      if (ops) record({ state: 'FAILURE_OWNER_STATE', sessionMatches: ops.sessionId === session,
        active: Boolean(ops.active), uncertain: Boolean(ops.uncertain),
        workspaceBusy: Boolean(ops.workspaceBusy), sourceRecoveryBusy: Boolean(ops.sourceRecoveryBusy),
        workspaceState: /^[A-Z_]+$/.test(ops.workspace?.state ?? '') ? ops.workspace.state : null,
        retryPending: Boolean(ops.workspace?.retryPending),
        sourceRecoveryState: /^[A-Z_]+$/.test(ops.sourceRecovery?.state ?? '') ? ops.sourceRecovery.state : null });
    }
    if (page) await shot('failure').catch(() => {});
    console.log(current + ': FAIL — inspect the bounded record and screenshot');
  } finally {
    clearTimeout(deadline);
    if (browser) await browser.close();
    fs.writeFileSync(path.join(output, 'browser-report.json'), JSON.stringify({
      outcome: failed ? 'FAIL' : 'PASS', stages, actions: sent, browserClosed: true,
      nativeAcceptance: 'NOT_RUN', fullE2E: 'NOT_COMPLETE', rawTraceRecorded: false,
    }, null, 2) + '\n', { mode: 0o600 });
  }
  return failed ? 1 : 0;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)
  process.exitCode = await main(process.argv[2]);

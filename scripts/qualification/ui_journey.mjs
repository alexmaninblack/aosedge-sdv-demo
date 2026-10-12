// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Real installed Presenter UI. No injected callbacks or mutation API adapters.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { idle, acknowledgement, owners } from './ui_pilot.mjs';

const origin = 'http://127.0.0.1:18080';
const uuid = /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/;
const version = /^[0-9]+\.[0-9]+\.[0-9]+$/;
const profiles = { platform: ['Braking telemetry', 'Brake analysis', 'Tire & advisory'],
  brake: ['Braking windows', 'Condition assessment', 'Driver advisory'], tire: ['Tire health'] };

export function command(body, expected, session, seen) {
  assert(expected && body && body.sessionId === session && uuid.test(body.requestId), 'UNARMED_UI_MUTATION');
  const { requestId, sessionId, ...actual } = body;
  assert.deepEqual(actual, expected, 'UI_COMMAND_CHANGED');
  assert(!seen.includes(requestId), 'REPEATED_REQUEST');
  return { ...actual, requestId, sessionId };
}
export function facts(job) {
  const value = Object.assign({}, ...job.results.map(row => row.facts ?? {}));
  const result = {};
  for (const key of ['version', 'releaseHandle', 'serviceId']) {
    const v = value[key] ?? job[key === 'releaseHandle' ? 'release' : key];
    if (v !== undefined && v !== null) result[key] = v;
  }
  if (result.version !== undefined) assert(version.test(result.version), 'VERSION_RECEIPT_INVALID');
  if (result.releaseHandle !== undefined)
    assert(/^(brake|tire)\/[0-9]+\.[0-9]+\.[0-9]+$/.test(result.releaseHandle), 'RELEASE_RECEIPT_INVALID');
  if (result.serviceId !== undefined) assert(uuid.test(result.serviceId), 'SERVICE_RECEIPT_INVALID');
  const ids = job.results.map(row => row.facts?.command?.commandId).filter(Boolean);
  if (ids.length) { assert(uuid.test(ids.at(-1)), 'RESET_RECEIPT_INVALID'); result.commandId = ids.at(-1); }
  return result;
}
export function installed(value, team, release) {
  if (team === 'platform') return value.activeVersion === release && value.vdpData === 'REPORTED_READY'
    && String(value.vdpRestarts) === '0' && value.processSlotMatches === true;
  return value.instances.some(row => row.version === release && row.run_state === 'active'
    && !row.error_message && [0, null, undefined].includes(row.error_exit_code));
}
export function autopilot(value, requireMotion = false) {
  const c = value?.controller;
  return c?.fresh === true && c.held === false && c.mode === 'AUTOPILOT'
    && typeof c.speed === 'number' && Number.isFinite(c.speed) && c.speed >= 0
    && (!requireMotion || c.speed > 3);
}
export function resetPreserved(before, after, team, commandId) {
  const peer = team === 'brake' ? 'tire' : 'brake';
  return after[team].resetState === 'CLEARED' && after[team].resetId === commandId
    && JSON.stringify(before.local.teams[peer].model) === JSON.stringify(after.local.teams[peer].model)
    && ['brake', 'tire'].every(t => before[t].productIds.every(id => after[t].productIds.includes(id)));
}
export function visibleWorkspace(value, session) {
  assert(idle(value, session), 'VISIBLE_WORKSPACE_OWNER_BUSY');
  assert(value.workspace?.state === 'PLACED_AWAITING_VISUAL_REVIEW'
    && value.workspace?.zOrder?.state === 'VERIFIED', 'VISIBLE_WORKSPACE_NOT_PLACED');
  // The native owner verifies CARLA/Driving Control geometry and ordering.
  // Its receipt is not a substitute for human readability/visual acceptance.
}
export function layoutSettlement(expected, job, value, session) {
  if (expected.action !== 'workspace-restore' || job.state !== 'PARTIAL') return null;
  assert(value.sessionId === session && !value.uncertain, 'UNKNOWN_OPERATION');
  const layout = value.workspace;
  if (layout?.state === 'WAITING_FOR_WINDOWS' && layout.retryPending === true) return 'PENDING';
  if (layout?.state === 'PLACED_AWAITING_VISUAL_REVIEW' && layout.zOrder?.state === 'VERIFIED'
      && !idle(value, session)) return 'PENDING';
  visibleWorkspace(value, session);
  return 'CONFIRMED';
}
export function transitionBaseline(value, test) {
  const v = value?.value, p = v?.installedProfile;
  return value?.state === 'CURRENT' && value.bindingKey?.startsWith(test + ':')
    && v?.target === 'test' && p?.state === 'CURRENT' && p.profile === 'v1'
    && p.releaseVersion === v.installedVersion && version.test(v.installedVersion)
    && !v.pendingVersion;
}

export async function nativeBrokerReply(id, fd = 0) {
  // Keep Playwright routing and the installed UI's polling alive while the
  // operator clicks a native control. A synchronous stdin read freezes both.
  let line = ''; const byte = Buffer.alloc(1);
  while (!line.endsWith('\n')) {
    const count = await new Promise((resolve, reject) => fs.read(fd, byte, 0, 1, null,
      (error, size) => error ? reject(error) : resolve(size)));
    assert(count === 1, 'NATIVE_UI_BROKER_CLOSED');
    line += byte.toString(); assert(line.length < 524288, 'NATIVE_UI_BROKER_TOO_LARGE');
  }
  const reply = JSON.parse(line);
  assert(reply.id === id && reply.ok === true, 'NATIVE_UI_BROKER_UNAVAILABLE');
  return reply.value;
}

export async function main(inputPath) {
  process.umask(0o077);
  const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  assert(['installed', 'release-story', 'vdp-transition', 'release-continuation', 'tire-review', 'road-return', 'moving-sota', 'native-controls'].includes(input.scenario), 'UI_SCENARIO_INVALID');
  if (input.nativeRunner) assert(input.visibleM1 && input.scenario === 'native-controls', 'NATIVE_RUNNER_SCOPE_INVALID');
  if (input.scenario === 'release-continuation')
    assert(version.test(input.continuation?.preparedV2), 'CONTINUATION_RECEIPT_REQUIRED');
  const require = createRequire(input.modulePath ?? path.join(input.repository, 'apps/presenter-ui/package.json'));
  const { chromium, expect } = require('@playwright/test');
  const record = value => {
    const fd = fs.openSync(path.join(input.records, 'ui-events.jsonl'), 'a', 0o600);
    try { fs.writeSync(fd, JSON.stringify({ at: new Date().toISOString(), ...value })+'\n'); fs.fsyncSync(fd); }
    finally { fs.closeSync(fd); }
  };
  let readSequence=0;
  function broker(kind,args) {
    const id=++readSequence;
    process.stdout.write(JSON.stringify({uiRead:true,id,kind,args})+'\n');
    let line='';const byte=Buffer.alloc(1);
    while(!line.endsWith('\n')) {
      assert(fs.readSync(0,byte,0,1,null)===1,'UI_READ_BROKER_CLOSED');
      line+=byte.toString();assert(line.length<524288,'UI_READ_BROKER_TOO_LARGE');
    }
    const reply=JSON.parse(line);assert(reply.id===id && reply.ok===true,'UI_READ_BROKER_UNAVAILABLE');
    return reply.value;
  }
  const observed = label => input.visibleM1 ? broker('observe',{label}) : JSON.parse(execFileSync(input.python, [input.helper,
    '--config', input.config, '--journey', input.journey, '--test', input.test, '--observe', label],
  { encoding: 'utf8', timeout: 55000, maxBuffer: 65536 }));
  const query = (name, team, release) => input.visibleM1 ? broker('query',{name,team,release}) : JSON.parse(execFileSync(input.python, [input.helper,
    '--config', input.config, '--journey', input.journey, '--test', input.test, '--query', name,
    ...(team ? ['--team', team] : []), ...(release ? ['--release', release] : [])],
  { encoding: 'utf8', timeout: 70000, maxBuffer: 524288 }));
  let browser, page, session, before, windowSession, windowId, workspaceRequired = false,
    armed = null, refused = false, failed = false, current = 'open';
  const sent = [], stages = [], cards = { ...input.cards };
  const watchdog = setTimeout(() => { failed = true; record({ stage: current, state: 'SCENARIO_DEADLINE' });
    if (browser) void browser.close(); }, 3500000);
  watchdog.unref();
  const button = name => page.getByRole('button', { name, exact: true });
  async function visible() {
    if (!input.visibleM1) return;
    await page.bringToFront();
    const placed = await windowSession.send('Browser.getWindowBounds', { windowId });
    assert(placed.bounds.windowState === 'normal', 'VISIBLE_BROWSER_NOT_NORMAL');
    for (const key of ['left', 'top', 'width', 'height'])
      assert(Math.abs(placed.bounds[key] - input.windowBounds[key]) <= 3, 'VISIBLE_BROWSER_PLACEMENT_FAILED');
    if (workspaceRequired) {
      let value = await read('operations');
      if (!idle(value, session)) record({ state: 'VISIBLE_WORKSPACE_SETTLING',
        sessionMatches: value.sessionId === session, activeOperation: Boolean(value.active),
        workspaceBusy: Boolean(value.workspaceBusy), sourceRecoveryBusy: Boolean(value.sourceRecoveryBusy),
        retryPending: Boolean(value.workspace?.retryPending), uncertain: Boolean(value.uncertain) });
      await until(async () => {
        assert(value.sessionId === session && !value.uncertain, 'VISIBLE_WORKSPACE_UNKNOWN_OPERATION');
        if (idle(value, session)) return true;
        value = await read('operations'); return idle(value, session);
      }, 'VISIBLE_WORKSPACE_OWNER_NOT_SETTLED', 30000, 250);
      visibleWorkspace(value, session);
    }
  }
  const dialog = () => page.getByRole('dialog');
  const close = async () => { await dialog().getByRole('button', { name: 'Close dialog', exact: true }).click();
    await expect(dialog()).toHaveCount(0); };
  const read = async name => {
    const r = await page.request.get(`${origin}/api/presenter/${name}`, { timeout: 15000 });
    assert(r.ok(), 'UI_READ_UNAVAILABLE'); return r.json();
  };
  const shot = async name => page.screenshot({ path: path.join(input.records, name+'.png'),
    mask: [page.locator('input, textarea')], fullPage: true });
  async function stage(name, fn) {
    current = name; const start = performance.now(); record({ stage: name, state: 'STARTED' });
    console.log(`${name}: started`); if(page) await visible();await fn();
    const row = { stage: name, outcome: 'PASS', seconds: +((performance.now()-start)/1000).toFixed(3) };
    stages.push(row); record(row); console.log(`${name}: PASS (${row.seconds}s)`);
  }
  async function until(fn, code, budget=90000, cadence=2000) {
    const end = performance.now()+budget;
    while (!(await fn())) { assert(performance.now()<end, code); await new Promise(r => setTimeout(r, cadence)); }
  }
  async function operate(expected, click, budget=360000) {
    await until(async () => idle(await read('operations'), session), 'OWNER_NOT_IDLE', 30000, 500);
    assert.equal(armed, null, 'UI_ACTION_ALREADY_ARMED'); armed = expected;
    const count = sent.length;
    const response = page.waitForResponse(r => r.request().method()==='POST'
      && r.url()===`${origin}/api/presenter/operations` && r.request().postDataJSON()?.action===expected.action,
    { timeout: 12000 });
    await visible();const [,reply] = await Promise.all([click(), response]);
    assert.equal(sent.length,count+1,'UI_SUBMISSION_MISSING'); armed = null;
    const request = sent.at(-1); record({ action: expected.action, requestId: request.requestId, httpStatus: reply.status() });
    acknowledgement(reply.status(), reply.status()===202 ? await reply.json() : null, request);
    let job;
    await until(async () => {
      const value = await read('operations'); assert(value.sessionId===session && !value.uncertain && !refused,'UNKNOWN_OPERATION');
      job = value.jobs.find(row => row.id===request.requestId);
      if (!job || ['ACCEPTED','RUNNING'].includes(job.state)) return false;
      // The existing window owner can return PARTIAL while its bounded native
      // recovery settles. Observe that same request's layout, never replay it or
      // relabel its receipt COMPLETED. All non-layout partial results fail below.
      const layout = layoutSettlement(expected, job, value, session);
      if (layout === 'PENDING') return false;
      if (layout === 'CONFIRMED') {
        record({state:'LAYOUT_RECOVERY_CONFIRMED',requestId:request.requestId,
          productState:job.state,workspaceState:value.workspace.state});
        return true;
      }
      if (job.state!=='COMPLETED') record({ state:'PRODUCT_FAILURE',action:expected.action,
        results: job.results.map(row => ({ state: row.state,
          code: /^[A-Z][A-Z0-9_]{1,100}$/.test(row.message??'') ? row.message : null })) });
      assert.equal(job.state,'COMPLETED','PRODUCT_OPERATION_FAILED');
      assert(value.workspace?.state!=='WAITING_FOR_UNLOCK','TARGET_DESKTOP_LOCKED');
      return idle(value, session);
    },'OPERATION_DEADLINE_NO_REPLAY',budget,1000);
    const value = facts(job); record({ action:expected.action,requestId:request.requestId,productState:job.state,...value });
    return value;
  }
  async function confirmed(expected, open, label) {
    await open(); await expect(dialog()).toBeVisible();
    return operate(expected, () => dialog().getByRole('button',{name:label,exact:true}).click());
  }
  async function native(label, action, check) {
    // The installed native controls are not HTML. A supported UI controller
    // clicks the named visible native button; this driver never substitutes RPC.
    const gate = { schemaVersion:1,stage:label,action,test:input.test,sessionId:session,state:'WAITING_FOR_UI_CLICK' };
    const gateFd=fs.openSync(path.join(input.records,'native-ui-gate.json'),'wx',0o600);
    try { fs.writeSync(gateFd,JSON.stringify(gate)+'\n');fs.fsyncSync(gateFd); }
    finally { fs.closeSync(gateFd); }
    record({ stage:label,state:'WAITING_FOR_NATIVE_UI',action }); console.log(`native-ui: ${label} · ${action}`);
    if(input.visibleM1) {
      const id=++readSequence;
      process.stdout.write(JSON.stringify({uiRead:true,id,kind:'native',args:gate})+'\n');
      const receipt=await nativeBrokerReply(id);
      if (input.nativeRunner) {
        assert(uuid.test(receipt.nativeRequestId), 'NATIVE_REQUEST_ID_INVALID');
        assert.deepEqual(receipt,{...gate,state:'INPUT_DISPATCHED_THROUGH_NATIVE_RUNNER',nativeRequestId:receipt.nativeRequestId},'NATIVE_UI_WITNESS_MISMATCH');
        record({stage:label,state:'NATIVE_MOUSE_RECEIPT',nativeRequestId:receipt.nativeRequestId});
      } else assert.deepEqual(receipt,{...gate,state:'CLICKED_THROUGH_CUA'},'NATIVE_UI_WITNESS_MISMATCH');
      fs.writeFileSync(path.join(input.records,'native-ui-click.json'),JSON.stringify(receipt)+'\n',{mode:0o600});
    }
    await until(async () => {
      const p = path.join(input.records,'native-ui-click.json');
      if (!fs.existsSync(p)) return false;
      const receipt = JSON.parse(fs.readFileSync(p,'utf8'));
      assert.deepEqual(receipt, input.nativeRunner
        ? {...gate,state:'INPUT_DISPATCHED_THROUGH_NATIVE_RUNNER',nativeRequestId:receipt.nativeRequestId}
        : {...gate,state:'CLICKED_THROUGH_CUA'},'NATIVE_UI_WITNESS_MISMATCH');
      return true;
    },'NATIVE_UI_GATE_NOT_EXECUTED',120000,500);
    await until(check,'NATIVE_UI_POSTCONDITION_FAILED',120000,2000);
    fs.unlinkSync(path.join(input.records,'native-ui-click.json'));
    fs.unlinkSync(path.join(input.records,'native-ui-gate.json'));
  }
  async function stopDialog() {
    await button('Demo controls').click(); await dialog().getByRole('button',{name:'Stop demo and keep data',exact:true}).click();
    await expect(dialog()).toContainText('Keep its Cloud identity');
  }
  try {
    let context;
    if(input.visibleM1) {
      assert(input.browserExecutable && input.profileDirectory && input.windowBounds,'VISIBLE_BROWSER_INPUT_REQUIRED');
      context=await chromium.launchPersistentContext(input.profileDirectory,{executablePath:input.browserExecutable,
        headless:false,chromiumSandbox:true,viewport:null,args:[`--app=${origin}/#native-browser`,'--no-first-run','--no-default-browser-check',
          '--disable-background-networking','--disable-component-update','--disable-sync','--disable-default-apps']});
      browser={close:()=>context.close()};page=context.pages()[0]??await context.newPage();
      windowSession=await context.newCDPSession(page);
      windowId=(await windowSession.send('Browser.getWindowForTarget')).windowId;
      await windowSession.send('Browser.setWindowBounds',{windowId,bounds:input.windowBounds});
      await visible();
    } else {
      browser=await chromium.launch({channel:'chrome',headless:true});
      context=await browser.newContext({viewport:{width:1440,height:1000}});page=await context.newPage();
    }
    page.setDefaultTimeout(30000);
    const readStarts = new WeakMap();
    const isSnapshot = req => req.method() === 'GET' && req.url() === `${origin}/api/presenter/snapshot`;
    page.on('request', req => { if (isSnapshot(req)) readStarts.set(req, performance.now()); });
    page.on('requestfailed', req => {
      if (isSnapshot(req) && readStarts.has(req)) record({ state: 'UI_LOCAL_READ_FAILED', milliseconds: Math.round(performance.now() - readStarts.get(req)) });
    });
    page.on('response', async response => {
      const req = response.request();
      if (!isSnapshot(req) || !readStarts.has(req)) return;
      const event = { state: 'UI_LOCAL_READ', httpStatus: response.status(), milliseconds: Math.round(performance.now() - readStarts.get(req)) };
      try {
        const data = await response.json();
        record({ ...event, runState: data.runId === input.test ? 'MATCHING' : data.runId ? 'OTHER' : 'MISSING' });
      } catch { record({ ...event, runState: 'UNREADABLE' }); }
    });
    await context.route('**/*',async route => {
      const req=route.request(), url=new URL(req.url());
      if (url.origin!==origin) { refused=true; return route.abort(); }
      if (req.method()==='GET') return route.continue();
      try {
        assert(req.method()==='POST' && url.pathname==='/api/presenter/operations','MUTATION_ENDPOINT_REJECTED');
        const value=command(req.postDataJSON(),armed,session,sent.map(row=>row.requestId));
        record({state:'DISPATCH_INTENT',...value}); sent.push(value); armed=null; return route.continue();
      } catch (error) {
        refused=true;
        const code=String(error.message).split('\n')[0];
        let body;
        try { body=req.postDataJSON(); } catch { /* Never retain malformed raw input. */ }
        const profile=v=>['v1','v2','v3'].includes(v)?v:null;
        record({state:'FORBIDDEN_REQUEST_BLOCKED',
          code:/^[A-Z][A-Z0-9_]{1,100}$/.test(code)?code:'UI_REQUEST_REJECTED',
          expectedProfile:profile(armed?.profile),actualProfile:profile(body?.profile),
          sessionMatches:body?.sessionId===session});
        return route.abort();
      }
    });
    await stage('open-installed-presenter',async () => {
      await page.goto(origin+'/#native-browser');
      const [ops,snapshot]=await Promise.all([read('operations'),read('snapshot')]);
      assert(snapshot.runId===input.test && ops.cloudDomain==='aws-stage.epmp-aos.projects.epam.com','TEST_BINDING_REQUIRED');
      session=ops.sessionId; before=observed('before'); owners(before,before,'STOPPED');
      await expect(button('Start controller')).toBeEnabled();
    });
    await stage('start-controller',async () => {
      await operate({action:'start-demo'},()=>button('Start controller').click()); owners(observed('running'),before,'RUNNING');
    });
    await stage('start-simulator',async () => {
      await expect(button('Start simulator')).toBeEnabled(); await operate({action:'start-simulation'},()=>button('Start simulator').click());
    });
    await stage('connect-in-manual',async () => {
      await confirmed({action:'connect-test'},()=>button('Connect in Manual').click(),'Connect in Manual');
      owners(observed('connected'),before,'RUNNING',true);
    });
    if (input.visibleM1) {
      // A clean API shutdown intentionally closes the native workspace. Starting
      // the browser/controller/simulator does not itself request window placement.
      // Use the existing visible UI owner once before requiring its receipt.
      await stage('restore-window-layout', async () => {
        await button('Demo controls').click();
        // This tab performs one existing read-only certificate inspection on
        // mount. Arm that exact request before the tab click, not a blanket POST
        // exception; never persist its certificate/PIN facts in the UI report.
        await operate({ action: 'cloud-inspect' }, () =>
          dialog().getByRole('button', { name: 'Advanced settings', exact: true }).click());
        await operate({ action: 'workspace-restore' }, () =>
          dialog().getByRole('button', { name: 'Restore window layout', exact: true }).click());
        await close();
      });
      workspaceRequired = true;
      await stage('visible-m1-workspace', async () => {
        await visible();
        record({ state: 'M1_WINDOW_COMPOSITION_CONFIRMED', browser: 'VISIBLE_APP_MODE',
          nativeOwners: 'PLACEMENT_AND_ORDERING_CONFIRMED', visualAcceptance: 'SEPARATE_CUA_REVIEW' });
      });
    }
    if (input.scenario === 'vdp-transition') {
      await stage('vdp-v1-current-baseline', async () => {
        await until(async () => transitionBaseline(await read('platform'), input.test), 'CURRENT_VDP_V1_REQUIRED', 65000);
        assert(await query('component-idle').idle, 'COMPONENT_PENDING');
      });
      await stage('vdp-v2-prepare-only', async () => {
        await button('Platform Team').click();
        const selected = button('v2 Brake analysis');
        await selected.click(); await expect(selected).toHaveAttribute('aria-pressed', 'true');
        const prepared = await operate({ action: 'prepare', profile: 'v2' }, () => button('Prepare v2').click());
        assert(version.test(prepared.version), 'PREPARED_VERSION_REQUIRED');
        await expect(selected).toHaveAttribute('aria-pressed', 'true');
        record({ state: 'VDP_V2_PREPARATION_CONFIRMED', version: prepared.version, publication: 'NOT_REQUESTED' });
        await shot('vdp-v2-prepared');
      });
    }
    if (['release-story','release-continuation'].includes(input.scenario)) {
      if (input.scenario === 'release-continuation') await stage('continuation-current-v1', async () => {
        assert(transitionBaseline(await read('platform'),input.test),'CURRENT_VDP_V1_REQUIRED');
        assert(query('component-idle').idle,'COMPONENT_PENDING');
      });
      const platform=async (profile, existingVersion) => {
        await stage('vdp-'+profile,async () => {
          await native('vdp-'+profile+'-safe','Safe Stop',()=>{
            const c=query('local').controller;return c.fresh && !c.held && c.mode==='SAFE_STOP' && c.speed<=.5 && c.brake>=.99;
          });
          await until(()=>query('component-idle').idle,'COMPONENT_PENDING',180000);
          await button('Platform Team').click();
          await page.getByRole('group',{name:'Capability profile',exact:true}).getByRole('button',
            {name:`${profile} ${profiles.platform[Number(profile[1])-1]}`,exact:true}).click();
          let prepared;
          if (existingVersion) {
            // Require the current UI candidate to agree with the prior completed receipt.
            await expect(page.getByText(`Selected candidate · ${profile} · ${existingVersion}`,{exact:true})).toBeVisible();
            prepared={version:existingVersion};
            record({state:'PREPARED_VERSION_REUSED',profile,version:existingVersion});
          } else prepared=await operate({action:'prepare',profile},()=>button('Prepare '+profile).click());
          assert(version.test(prepared.version),'PREPARED_VERSION_REQUIRED');
          await expect(page.getByText(`Selected candidate · ${profile} · ${prepared.version}`,{exact:true})).toBeVisible();
          await confirmed({action:'publish',version:prepared.version},()=>button('Sign & publish').click(),'Sign & publish VDP');
          await until(()=>installed(query('component'),'platform',prepared.version),'VDP_INSTALL_NOT_CONFIRMED',180000);
          cards['Vehicle Data Platform installed details']=`${profile} · ${prepared.version}`;
        });
      };
      const service=async(team,profile) => {
        await stage(team+'-'+profile,async () => {
          await button(team==='brake'?'Brake Team':'Tire Team').click();
          await page.getByRole('group',{name:'Capability profile',exact:true}).getByRole('button',
            {name:`${profile} ${profiles[team][Number(profile[1])-1]}`,exact:true}).click();
          const prepared=await operate({action:'service-prepare',team,profile},()=>button('Prepare '+profile).click());
          assert(prepared.releaseHandle && prepared.version,'PREPARED_SERVICE_REQUIRED');
          await expect(page.getByText(`Selected candidate · ${profile} · ${prepared.version}`,{exact:true})).toBeVisible();
          const action={action:'service-publish',release:prepared.releaseHandle};
          await confirmed(action,()=>button('Sign & publish').click(),'Sign & publish service');
          await until(()=>query('publication',null,prepared.releaseHandle).stage==='READY','SERVICE_PUBLICATION_NOT_READY',180000);
          // Retained Test already has both Subjects assigned; do not assign again.
          await until(()=>installed(query('service',team),team,prepared.version),'SERVICE_INSTALL_NOT_CONFIRMED',180000);
          cards[team==='brake'?'Brake service details':'Tire service details']=`${profile} · ${prepared.version}`;
          const old=query('backend',team);
          await native(team+'-'+profile+'-maneuver',team==='brake'?'Brake maneuver':'Tire maneuver',()=>{
            const after=query('backend',team); return after.products.some(p=>!old.productIds.includes(p.id) && p.version===prepared.version);
          });
        });
      };
      for (const p of input.scenario === 'release-continuation' ? ['v2','v3'] : ['v1','v2','v3']) {
        await platform(p, p === 'v2' ? input.continuation?.preparedV2 : undefined); await service('brake',p);
      }
      await service('tire','v1');
      await stage('return-to-road',async () => {
        await native('return-to-road','Return to road',()=>{
          const c=query('local').controller;return c.fresh && !c.held && c.mode==='MANUAL' && c.speed<=.5 && c.brake>=.99;
        });
      });
    }
    if (['tire-review', 'road-return', 'moving-sota'].includes(input.scenario)) {
      await stage('current-installed-releases',async () => {
        for (const [team,name] of [['platform','Vehicle Data Platform installed details'],
          ['brake','Brake service details'],['tire','Tire service details']]) {
          const release = cards[name].split(' · ')[1];
          assert(version.test(release),'PINNED_RELEASE_REQUIRED');
          await until(()=>installed(query(team==='platform'?'component':'service',
            team==='platform'?undefined:team),team,release),'CURRENT_INSTALLED_RELEASE_REQUIRED',180000);
        }
      });
    }
    if (input.scenario === 'moving-sota') {
      await stage('moving-sota-autopilot', async () => {
        await native('moving-sota-autopilot', 'Autopilot', () => autopilot(query('local'), true));
      });
      const original = query('local');
      for (const [team, profile] of [['brake', 'v3'], ['tire', 'v1']]) {
        await stage(team+'-moving-sota', async () => {
          const motion = () => {
            const value = query('local');
            assert.deepEqual(value.identity, original.identity, 'MOVING_TEST_IDENTITY_CHANGED');
            assert(value.bootId === original.bootId, 'MOVING_BOOT_CHANGED');
            assert(autopilot(value), 'AUTOPILOT_NOT_CURRENT');
            record({state:'MOVING_SOTA_OBSERVATION', team, moving:autopilot(value,true), mode:value.controller.mode});
            return autopilot(value, true);
          };
          await until(motion, 'MOVING_BASELINE_REQUIRED', 45000);
          await button(team==='brake'?'Brake Team':'Tire Team').click();
          await page.getByRole('group',{name:'Capability profile',exact:true}).getByRole('button',
            {name:`${profile} ${profiles[team][Number(profile[1])-1]}`,exact:true}).click();
          const prepared=await operate({action:'service-prepare',team,profile},()=>button('Prepare '+profile).click());
          assert(prepared.releaseHandle && prepared.version, 'PREPARED_SERVICE_REQUIRED');
          await expect(page.getByText(`Selected candidate · ${profile} · ${prepared.version}`,{exact:true})).toBeVisible();
          await until(motion, 'MOVING_PUBLICATION_REQUIRED', 45000);
          await confirmed({action:'service-publish',release:prepared.releaseHandle},()=>button('Sign & publish').click(),'Sign & publish service');
          await until(() => {
            const moving = motion();
            return installed(query('service',team),team,prepared.version) && moving;
          }, 'MOVING_SERVICE_INSTALL_NOT_CONFIRMED', 180000);
          assert(installed(query('component'),'platform',cards['Vehicle Data Platform installed details'].split(' · ')[1]),
            'MOVING_PLATFORM_CHANGED');
          record({state:'MOVING_SOTA_INSTALLED',team,profile,version:prepared.version,releaseHandle:prepared.releaseHandle});
          await shot(team+'-moving-installed');
        });
      }
      await stage('moving-sota-safe-stop',async () => {
        await native('moving-sota-safe-stop','Safe Stop',()=>{
          const c=query('local').controller;return c.fresh && !c.held && c.mode==='SAFE_STOP' && c.speed<=.5 && c.brake>=.99;
        });
      });
    }
    if (input.scenario === 'tire-review') {
      await stage('tire-current-maneuver',async () => {
        const release=cards['Tire service details'].split(' · ')[1], old=query('backend','tire');
        await native('tire-current-maneuver','Tire maneuver',()=>{
          const after=query('backend','tire');
          return after.products.some(p=>!old.productIds.includes(p.id) && p.version===release);
        });
      });
    }
    if (input.scenario === 'native-controls') {
      // Read the installed successor's owners now. Earlier-candidate receipts
      // cannot qualify this package; no release is prepared/published here.
      const baseline = {};
      await stage('native-controls-installed-baseline', async () => {
        const component = query('component');
        assert(version.test(component.activeVersion) && installed(component,'platform',component.activeVersion), 'LIVE_VDP_REQUIRED');
        baseline.platform = component.activeVersion;
        for (const team of ['brake','tire']) {
          const rows = query('service',team).instances;
          assert(rows.length === 1 && version.test(rows[0].version) && rows[0].run_state === 'active'
            && !rows[0].error_message && [0,null,undefined].includes(rows[0].error_exit_code),'LIVE_SERVICE_REQUIRED');
          baseline[team] = rows[0].version;
        }
        record({state:'LIVE_INSTALLED_BASELINE',versions:baseline,publication:'NOT_REQUESTED'});
      });
      await stage('native-controls-autopilot', async () => {
        await native('native-controls-autopilot','Autopilot',()=>autopilot(query('local'),true));
      });
      await stage('native-controls-safe-stop', async () => {
        await native('native-controls-safe-stop','Safe Stop',()=>{
          const c=query('local').controller;return c.fresh && !c.held && c.mode==='SAFE_STOP' && c.speed<=.5 && c.brake>=.99;
        });
      });
      for (const team of ['brake','tire']) {
        await stage('native-controls-'+team,async () => {
          const old=query('backend',team);
          await native('native-controls-'+team,team==='brake'?'Brake maneuver':'Tire maneuver',()=>{
            const after=query('backend',team);
            return after.products.some(p=>!old.productIds.includes(p.id) && p.version===baseline[team]);
          });
        });
        await stage('native-controls-'+team+'-return',async () => {
          await native('native-controls-'+team+'-return','Return to road',()=>{
            const c=query('local').controller;return c.fresh && !c.held && c.mode==='MANUAL' && c.speed<=.5 && c.brake>=.99;
          });
        });
      }
      await stage('native-controls-releases-preserved',async () => {
        assert(installed(query('component'),'platform',baseline.platform),'LIVE_PLATFORM_CHANGED');
        for(const team of ['brake','tire']) assert(installed(query('service',team),team,baseline[team]),'LIVE_SERVICE_CHANGED');
      });
    }
    if (['tire-review','road-return'].includes(input.scenario)) {
      await stage('return-to-road',async () => {
        await native('return-to-road','Return to road',()=>{
          const c=query('local').controller;return c.fresh && !c.held && c.mode==='MANUAL' && c.speed<=.5 && c.brake>=.99;
        });
      });
    }
    if (!['vdp-transition','road-return','moving-sota','native-controls'].includes(input.scenario)) {
    await stage('installed-details',async () => {
      await button('Vehicle').click();
      for (const [name,text] of Object.entries(cards)) {
        await expect(button(name)).toContainText(text,{timeout:65000}); await button(name).click();
        await expect(dialog()).toBeVisible(); await close();
      }
      await shot('installed-cards');
    });
    for (const name of ['Platform Team','Brake Team','Tire Team']) {
      await stage(name.replaceAll(' ','-').toLowerCase(),async () => {
        await button(name).click(); await expect(page.getByRole('group',{name:'Capability profile',exact:true})).toBeVisible();
        await expect(button('Sign & publish')).toBeVisible(); await expect(button('Prepare v1').or(button('Prepare v2')).or(button('Prepare v3'))).toBeVisible();
        await shot(name.split(' ')[0].toLowerCase()+'-team');
      });
    }
    await button('Vehicle').click();
    await stage('cloud-software-and-resources',async () => {
      await button('Aos Cloud Unit monitoring').click(); await expect(dialog()).toContainText('Components');
      await dialog().getByRole('button',{name:'Resources',exact:true}).click();
      await expect(dialog()).toContainText('CPU'); await shot('cloud-resources');
      for(const name of ['Disk','Inbound','Outbound']) {
        await dialog().getByRole('button',{name,exact:true}).click();
        await expect(dialog().getByRole('button',{name,exact:true})).toHaveAttribute('aria-pressed','true');
      }
      await close();
    });
    for (const team of ['brake','tire']) {
      await stage(team+'-backend-evidence',async () => {
        await button((team==='brake'?'Brake':'Tire')+' backend Open dashboard').click();
        await expect(dialog()).toBeVisible(); await expect(dialog().getByRole('button',{name:'Refresh backend',exact:true})).toBeVisible();
        await shot(team+'-backend');
        await dialog().getByRole('button',{name:'Records',exact:true}).click();
        await expect(dialog().getByRole('button',{name:'Records',exact:true})).toHaveAttribute('aria-pressed','true');
        if(team==='brake') {
          await dialog().getByRole('combobox',{name:'Record type',exact:true}).selectOption('windows');
          await expect(dialog().getByRole('combobox',{name:'Record type',exact:true})).toHaveValue('windows');
        }
        await shot(team+'-records');await close();
      });
      await stage(team+'-independent-reset',async () => {
        const old=query('combined');
        const reset=await operate({action:'backend-reset',team},()=>button('Reset Driver Advisory — '+(team==='brake'?'Brake':'Tire')).click());
        assert(reset.commandId,'RESET_COMMAND_REQUIRED');
        await until(()=>resetPreserved(old,query('combined'),team,reset.commandId),'RESET_NOT_INDEPENDENT',90000);
      });
    }
    await stage('activity-receipts',async () => {
      await until(async()=>{
        const snapshot=await read('snapshot');assert(!snapshot.runId || snapshot.runId===input.test,'TEST_BINDING_CHANGED');
        return snapshot.runId===input.test;
      },'CURRENT_UI_RUN_UNAVAILABLE',30000,1000);
      await expect(page.getByRole('button',{name:/^Activity · [1-9][0-9]*$/})).toBeVisible();
      await page.getByRole('button',{name:/^Activity · /}).click(); await expect(dialog()).toContainText('Connect in Manual');
      await shot('activity'); await close();
    });
    await stage('cancel-stop',async () => {
      const count=sent.length; await stopDialog(); await dialog().getByRole('button',{name:'Cancel',exact:true}).click();
      assert.equal(sent.length,count,'CANCEL_DISPATCHED_MUTATION'); owners(observed('cancelled'),before,'RUNNING',true);
    });
    }
    await stage('confirmed-stop',async () => {
      await stopDialog(); workspaceRequired = false; // Stopping deliberately removes native surfaces.
      await operate({action:'stop-demo'},()=>dialog().getByRole('button',{name:'Stop demo and keep data',exact:true}).click());
      owners(observed('stopped'),before,'STOPPED'); await expect(button('Start controller')).toBeEnabled(); await shot('stopped');
    });
    assert.equal(refused,false); assert.equal(armed,null);
  } catch(error) {
    failed=true;const code=String(error.message).split('\n')[0];
    stages.push({stage:current,outcome:'FAIL',code:/^[A-Z][A-Z0-9_]{1,100}$/.test(code)?code:'UI_JOURNEY_CHECK_FAILED'});
    if(page && session) {
      try {
        const [snapshot,ops]=await Promise.all([read('snapshot'),read('operations')]);
        record({state:'FAILURE_OWNER_PROJECTION',expectedRunMatches:snapshot.runId===input.test,
          snapshotObserved:snapshot.state??null,sessionMatches:ops.sessionId===session,
          activeOperation:Boolean(ops.active),uncertain:Boolean(ops.uncertain),
          workspaceBusy:Boolean(ops.workspaceBusy),sourceRecoveryBusy:Boolean(ops.sourceRecoveryBusy),
          workspaceRetryPending:Boolean(ops.workspace?.retryPending),
          workspaceState:ops.workspace?.state??null,currentJobRecorded:ops.jobs.some(j=>j.id===sent.at(-1)?.requestId)});
      } catch { record({state:'FAILURE_OWNER_PROJECTION_UNAVAILABLE'}); }
    }
    record(stages.at(-1)); if(page) await shot('failure').catch(()=>{});
    console.log(`${current}: FAIL · ${stages.at(-1).code}`);
  } finally {
    clearTimeout(watchdog);if(browser)await browser.close();
    fs.writeFileSync(path.join(input.records,'browser-report.json'),JSON.stringify({outcome:failed?'FAIL':'PASS',
      scenario:input.scenario,stages,actions:sent,browserClosed:true,nativeAcceptance:'NOT_RUN',fullE2E:'NOT_COMPLETE',
      browserLocation:input.visibleM1?'M1_VISIBLE':'DEVELOPMENT_MAC_HEADLESS',
      rawTraceRecorded:false},null,2)+'\n',{mode:0o600});
  }
  return failed?1:0;
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) process.exitCode=await main(process.argv[2]);

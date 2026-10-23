// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Visible, read-only installed Presenter during engineering recovery checks.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {watchPresentation} from './ui_geometry.mjs';
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const origin='http://127.0.0.1:18080';
const {chromium}=createRequire(input.modulePath)('@playwright/test');
let context,presentation;
try {
  context=await chromium.launchPersistentContext(input.profileDirectory,{
    executablePath:input.browserExecutable,headless:false,chromiumSandbox:true,viewport:null,
    args:[`--app=${origin}/#native-browser`,'--no-first-run','--no-default-browser-check',
      '--disable-background-networking','--disable-component-update','--disable-sync','--disable-default-apps']});
  await context.route('**/*',route=>route.request().method()==='GET'
    && new URL(route.request().url()).origin===origin ? route.continue() : route.abort());
  const page=context.pages()[0]??await context.newPage();
  await page.goto(origin+'/#native-browser');
  const response=await page.request.get(origin+'/api/presenter/snapshot');
  assert(response.ok() && (await response.json()).runId===input.test,'OBSERVER_TEST_CHANGED');
  const cdp=await context.newCDPSession(page);
  const window=await cdp.send('Browser.getWindowForTarget');
  await cdp.send('Browser.setWindowBounds',{windowId:window.windowId,bounds:{windowState:'normal'}});
  await cdp.send('Browser.setWindowBounds',{windowId:window.windowId,bounds:input.windowBounds});
  const placed=await cdp.send('Browser.getWindowBounds',{windowId:window.windowId});
  assert(Object.entries(input.windowBounds).every(([k,v])=>Math.abs(placed.bounds[k]-v)<=3),'OBSERVER_PLACEMENT_FAILED');
  await page.bringToFront();
  presentation=watchPresentation(page,row=>fs.appendFileSync(path.join(input.records,'presentation.jsonl'),JSON.stringify({at:new Date().toISOString(),...row})+'\n',{mode:0o600}));
  process.stdout.write('OBSERVER_READY\n');
  const deadline=Date.now()+1800000;
  while (!fs.existsSync(path.join(input.records,'observer-stop.json'))) {
    assert(Date.now()<deadline,'OBSERVER_DEADLINE');
    await page.bringToFront();
    await new Promise(resolve=>setTimeout(resolve,2000));
  }
} catch {
  process.exitCode=1;process.stdout.write('OBSERVER_FAILED\n');
} finally {
  if(presentation)fs.writeFileSync(path.join(input.records,'presentation-report.json'),JSON.stringify(await presentation.close())+'\n',{mode:0o600});
  if(context)await context.close();
  process.stdout.write('OBSERVER_CLOSED\n');
}

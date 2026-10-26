// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import test from 'node:test';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import {candidateText,displayedConnection} from './ui_journey.mjs';
import { command, facts, installed, failedWindow, resetPreserved, visibleWorkspace, layoutSettlement, transitionBaseline, autopilot, completedExercise, nativeVersions,continuousSections,movingWindowMs,lifecyclePreserved,lifecycleChecks,continuousActions,restartActions,statusObservation,browserFailure,releaseViewSpec,selectReleaseView,qualificationCloud,assertBrowserIdentities,visibleCardText } from './ui_journey.mjs';
const id='01234567-89ab-cdef-0123-456789abcdef';
const ref='ref_'+'a'.repeat(32);
test('all publication paths use the semantic Prepare target and explicit candidate labels',()=>{
  const source=fs.readFileSync(new URL('./ui_journey.mjs',import.meta.url),'utf8');
  assert(!source.includes("button('Prepare '+profile)"));
  assert(!source.includes('Selected candidate · ${profile}'));
  for(const profile of ['v1','v2','v3'])
    assert.equal(candidateText(profile,'172.0.0'),`Selected candidate · Capability ${profile.toUpperCase()} · Cloud release 172.0.0`);
});
test('display observation keeps connection distinct from freshness without copying arbitrary text',()=>{
  assert.equal(displayedConnection('Test Vehicle · Online'),'Online');
  assert.equal(displayedConnection('Last confirmed connection · Offline'),'Offline');
  assert.equal(displayedConnection('Test Vehicle · Cloud not yet observed'),'Cloud not yet observed');
  assert.equal(displayedConnection('private unexpected text'),'UNRECOGNIZED');
});
test('traffic-light motion window stays bounded and cannot replace actual fresh motion',()=>{
  assert.equal(movingWindowMs,120000);
  const value={controller:{fresh:true,held:false,mode:'AUTOPILOT',speed:0}};
  assert.equal(autopilot(value),true);
  for(const speed of [0,1,3]) assert.equal(autopilot({controller:{...value.controller,speed}},true),false);
  assert.equal(autopilot({controller:{...value.controller,speed:3.1}},true),true);
  for(const change of [{fresh:false},{held:true},{mode:'MANUAL'}])
    assert.equal(autopilot({controller:{...value.controller,speed:30,...change}},true),false);
});
test('live browser reads reject known private Test and Cloud UUIDs, including composite values',()=>{
  const value={runId:ref,sessionId:'11234567-89ab-cdef-0123-456789abcdef'};
  assert.equal(assertBrowserIdentities(value,[id]),value);
  for(const leaked of [{runId:id},{value:{unitId:id}},{bindingKey:id+':test'}])
    assert.throws(()=>assertBrowserIdentities(leaked,[id]),/BROWSER_PRIVATE_IDENTITY_LEAK/);
});
test('browser uses only an explicitly allowed qualification Cloud',()=>{
  assert.equal(qualificationCloud({}),'aws-stage.epmp-aos.projects.epam.com');
  assert.equal(qualificationCloud({cloudDomain:'aoscloud.io'}),'aoscloud.io');
  for(const cloudDomain of ['other.example','https://aoscloud.io',[]])
    assert.throws(()=>qualificationCloud({cloudDomain}),/QUALIFICATION_CLOUD_NOT_ALLOWED/);
});
test('each published release checks its exact team stages, installed card and capability',()=>{
  assert.deepEqual(releaseViewSpec('platform','v2','172.0.0'),{
    teamTab:'Platform Team',profileButton:'v2 Brake analysis',stages:['Published','Installed'],card:'Vehicle Data Platform installed details',
    cardText:'Capability V2 · release 172.0.0',profile:'v2',release:'172.0.0'});
  assert.equal(visibleCardText('v2 · 172.0.0'),'Capability V2 · release 172.0.0');
  assert.equal(visibleCardText('installed · 172.0.0'),'release 172.0.0');
  assert.equal(visibleCardText('Not confirmed'),'Not confirmed');
  assert.deepEqual(releaseViewSpec('brake','v3','155.0.0').stages,['Published','Assigned','Running']);
  assert.equal(releaseViewSpec('tire','v1','76.0.0').card,'Tire service details');
  for(const args of [['unknown','v1','171.0.0'],['platform','v4','171.0.0'],['tire','v2','76.0.0'],['brake','v1','latest']])
    assert.throws(()=>releaseViewSpec(...args),/RELEASE_VIEW_INPUT_INVALID/);
});
test('release verification selects the published profile after team navigation suggests the next one',async()=>{
  for(const [team,profile] of [['platform','v1'],['platform','v2'],['brake','v1'],['brake','v3'],['tire','v1']]) {
    const spec=releaseViewSpec(team,profile,'172.0.0'),clicks=[];
    let selected=null;
    const profileButton={click:async()=>{clicks.push(spec.profileButton);selected=profile;}};
    const page={getByRole:(role,options)=>{
      assert.equal(options.exact,true);
      if(role==='button') {
        assert.equal(options.name,spec.teamTab);
        return {click:async()=>{clicks.push(spec.teamTab);selected='next-profile';}};
      }
      assert.equal(role,'group');assert.equal(options.name,'Capability profile');
      return {getByRole:(child,options)=>{
        assert.equal(child,'button');assert.deepEqual(options,{name:spec.profileButton,exact:true});
        return profileButton;
      }};
    }};
    const expect=element=>({toHaveAttribute:async(name,value)=>{
      assert.equal(element,profileButton);assert.equal(name,'aria-pressed');assert.equal(value,'true');
      assert.equal(selected,profile);
    }});
    await selectReleaseView(page,expect,spec);
    assert.deepEqual(clicks,[spec.teamTab,spec.profileButton]);
  }
});
test('browser failure diagnostics expose fixed categories rather than raw error text',()=>{
  assert.equal(browserFailure(new Error('apiRequestContext.get: read ECONNRESET private details')),'UI_READ_CONNECTION_RESET');
  assert.equal(browserFailure(new Error('strict mode violation: private HTML')),'UI_LOCATOR_AMBIGUOUS');
  assert.equal(browserFailure(new Error('Timed out 5000ms waiting for expect(locator).toBeVisible() private HTML')),'UI_WAIT_TIMED_OUT');
  assert.equal(browserFailure(new Error('private details')),'UI_JOURNEY_CHECK_FAILED');
});
test('status trace retains fixed source timestamps and real Offline, never raw credentials',()=>{
  const data={bindingKey:id+':unit',state:'CURRENT',observedAt:'2026-10-14T09:20:00.123Z',
    value:{online:'OFFLINE',installedVersion:'171.0.0',secret:'DO_NOT_COPY',
      inventory:{unit:{state:'CURRENT',readCompletedAt:'2026-10-14T09:19:59Z',value:{updated_at:'2026-10-14T09:19:58Z',last_online_changed_at:'2026-10-14T09:19:57Z',certificate:'DO_NOT_COPY'}}},
      installedProfile:{profile:'v1',state:'CURRENT',reason:null}}};
  const value=statusObservation(data,id);
  assert.equal(value.online,'OFFLINE');assert.equal(value.bindingMatches,true);
  assert.equal(value.onlineChangedAt,'2026-10-14T09:19:57Z');assert.equal(value.profile,'v1');
  assert(!JSON.stringify(value).includes('DO_NOT_COPY'));
  assert.equal(statusObservation({...data,bindingKey:'other:unit'},id).bindingMatches,false);
  const unsafe=statusObservation({state:'raw',reason:'private key',value:{online:'raw',installedVersion:'secret',installedProfile:{profile:'secret',reason:'private key'}}},id);
  assert.equal(unsafe.reason,null);assert.equal(unsafe.online,null);assert.equal(unsafe.profileReason,null);
});
test('continuous campaign keeps the accepted section order',()=>{
  assert.deepEqual(continuousSections,['release-story','installed-views','moving-sota','stop-start']);
});
test('continuous actions prove serial publication and no extra healthy startup between sections',()=>{
  const startup=['start-demo','start-simulation','connect-test'];
  const publications=['publish','service-publish','publish','service-publish','publish','service-publish','service-publish','service-publish','service-publish'];
  const valid=[...startup,...publications,'backend-reset','backend-reset','stop-demo',...startup,'stop-demo'].map(action=>({action}));
  assert.equal(continuousActions(valid),true);
  for(const value of [valid.slice(1),[...valid,{action:'retire'}],valid.filter(a=>a.action!=='backend-reset'),
    valid.toSpliced(5,0,{action:'stop-demo'},{action:'start-demo'},{action:'start-simulation'},{action:'connect-test'})])
    assert.throws(()=>continuousActions(value));
});
test('same-Test Stop/Start requires a new boot, stationary Manual, preserved models/history and healthy services',()=>{
  const before={local:{bootId:id,identity:{unitId:id},teams:{brake:{model:['a']},tire:{model:['b']}}},
    brake:{productIds:['a']},tire:{productIds:['b']}};
  const after=structuredClone(before);
  after.local.bootId='11234567-89ab-cdef-0123-456789abcdef';
  after.local.controller={fresh:true,held:false,mode:'MANUAL',speed:0,brake:1};
  after.local.services=Object.fromEntries(['iam','cm','sm','vdp'].map(s=>[s,{ActiveState:'active',Result:'success',NRestarts:'0'}]));
  assert.equal(lifecyclePreserved(before,after),true);
  assert(Object.values(lifecycleChecks(before,after)).every(v=>v===true));
  for(const change of [v=>v.local.bootId=id,v=>v.local.identity.unitId='other',v=>v.local.controller.fresh=false,
    v=>v.local.controller.mode='AUTOPILOT',v=>v.local.controller.speed=1,v=>v.local.teams.brake.model=['changed'],
    v=>v.tire.productIds=[],v=>v.local.services.cm.NRestarts='1',v=>delete v.local.services.vdp]) {
    const value=structuredClone(after);change(value);assert.equal(Boolean(lifecyclePreserved(before,value)),false);
    assert(Object.values(lifecycleChecks(before,value)).some(v=>v===false));
  }
  const changed=structuredClone(after);changed.local.teams.brake.model=['changed'];
  assert.deepEqual(Object.entries(lifecycleChecks(before,changed)).filter(([,v])=>v===false),[['brakeModelPreserved',false]]);
  assert(Object.values(lifecycleChecks(null,null)).every(v=>v===false));
});
test('restart-only tail cannot publish, reset, assign, retire or replay a lifecycle action',()=>{
  const actions=['start-demo','start-simulation','connect-test','cloud-inspect','workspace-restore','stop-demo',
    'start-demo','start-simulation','connect-test','cloud-inspect','workspace-restore','stop-demo'].map(action=>({action}));
  assert.equal(restartActions(actions),true);
  for(const action of ['prepare','publish','service-publish','backend-reset','retire','service-assign','create','start-demo'])
    assert.throws(()=>restartActions([...actions,{action}]));
  assert.throws(()=>restartActions(actions.slice(1)));
});
test('new durably delivered invalid Brake window explains failure without being accepted as a product',()=>{
  const row={id,version:'153.0.0',terminalState:'INCOMPLETE_SOURCE_GAP',deliveryState:'DURABLY_RECEIVED',receivedChunkCount:7,expectedChunkCount:7};
  assert.equal(failedWindow({windows:[]},{windows:[row]},'153.0.0'),'INCOMPLETE_SOURCE_GAP');
  assert.equal(failedWindow({windows:[row]},{windows:[row]},'153.0.0'),null);
  for(const change of [{version:'152.0.0'},{terminalState:'COMPLETE'},{terminalState:'UNKNOWN'},
    {deliveryState:'PENDING'},{receivedChunkCount:6},{expectedChunkCount:0}])
    assert.equal(failedWindow({windows:[]},{windows:[{...row,...change}]},'153.0.0'),null);
});
test('campaign baseline pins exact versions before native input', () => {
  const expected={vdp:'158.0.0',brake:'137.0.0',tire:'69.0.0'};
  assert.deepEqual(nativeVersions(expected,expected),expected);
  for (const value of [{...expected,vdp:'latest'},{...expected,tire:true},{vdp:'158.0.0'},
                      {...expected,extra:'1.0.0'},null,[]])
    assert.throws(()=>nativeVersions(value),/NATIVE_VERSIONS_INVALID/);
  assert.throws(()=>nativeVersions({...expected,brake:'138.0.0'},expected),/NATIVE_BASELINE_CHANGED/);
});
test('live maneuver requires a new completed owner receipt, not background products alone', () => {
  const value={id,kind:'brake',runMatches:true,operationMatches:true,phase:'RELEASED',
    state:'COMPLETED',physicalStop:'CONFIRMED',noOp:false};
  assert.equal(completedExercise(value,{},'brake'),true);
  assert.equal(completedExercise(value,{id},'brake'),false);
  for(const change of [{id:'bad'},{kind:'tire'},{runMatches:false},{operationMatches:false},
    {phase:'RUNNING'},{state:'ABORTED'},{physicalStop:null},{noOp:true}])
    assert.equal(Boolean(completedExercise({...value,...change},{},'brake')),false);
  assert.equal(completedExercise({...value,kind:'return_to_road'},{},'return_to_road'),false);
  assert.equal(completedExercise({...value,kind:'return_to_road',autopilotStarted:false},{},'return_to_road'),true);
});
test('moving SOTA requires actual fresh unheld Autopilot motion, not a mode label alone', () => {
  const value={controller:{fresh:true,held:false,mode:'AUTOPILOT',speed:20}};
  assert.equal(autopilot(value,true),true);
  assert.equal(autopilot({...value,controller:{...value.controller,speed:0}}),true);
  assert.equal(autopilot({...value,controller:{...value.controller,speed:0}},true),false);
  for(const change of [{fresh:false},{held:true},{mode:'SAFE_STOP'},{mode:'MANUAL'},{speed:null},{speed:NaN},{speed:-1}])
    assert.equal(autopilot({...value,controller:{...value.controller,...change}},true),false);
});
test('native witness wait leaves browser routing and polling responsive', async () => {
  const url = new URL('./ui_journey.mjs', import.meta.url).href;
  const child = spawn(process.execPath, ['--input-type=module', '-e',
    `import {nativeBrokerReply} from ${JSON.stringify(url)};
     setTimeout(()=>process.stdout.write('POLLING_ALIVE\\n'),10);
     try { const value=await nativeBrokerReply(1);process.stdout.write(value.state+'\\n'); }
     catch { process.stdout.write('FAIL_CLOSED\\n'); }`], {stdio:['pipe','pipe','pipe']});
  let output=''; child.stdout.on('data', data => {
    output+=data;
    if (output === 'POLLING_ALIVE\n') child.stdin.end(JSON.stringify({id:1,ok:true,value:{state:'CLICKED_THROUGH_CUA'}})+'\n');
  });
  const timer=setTimeout(()=>child.kill(),3000);
  const code=await new Promise(resolve=>child.on('exit',resolve));clearTimeout(timer);
  assert.equal(code,0);assert.equal(output,'POLLING_ALIVE\nCLICKED_THROUGH_CUA\n');
});
test('native witness wait rejects a failed or mismatched broker reply', async () => {
  const url = new URL('./ui_journey.mjs', import.meta.url).href;
  for (const reply of [{id:2,ok:true,value:{}},{id:1,ok:false}]) {
    const child=spawn(process.execPath,['--input-type=module','-e',
      `import {nativeBrokerReply} from ${JSON.stringify(url)};
       try {await nativeBrokerReply(1);process.exitCode=1;} catch {process.stdout.write('FAIL_CLOSED\\n');}`],
      {stdio:['pipe','pipe','pipe']});
    let output='';child.stdout.on('data',data=>output+=data);
    child.stdin.end(JSON.stringify(reply)+'\n');
    const code=await new Promise(resolve=>child.on('exit',resolve));
    assert.equal(code,0);assert.equal(output,'FAIL_CLOSED\n');
  }
});
test('transition diagnosis requires current same-Test V1 installation, not a historical card', () => {
  const v = { state: 'CURRENT', bindingKey: id + ':unit', value: { target: 'test', installedVersion: '150.0.0', pendingVersion: null,
    installedProfile: { state: 'CURRENT', profile: 'v1', releaseVersion: '150.0.0' } } };
  assert.equal(transitionBaseline(v, id), true);
  for (const other of [null, { ...v, state: 'UNAVAILABLE' }, { ...v, bindingKey: 'other:unit' },
    { ...v, value: { ...v.value, pendingVersion: '151.0.0' } },
    { ...v, value: { ...v.value, installedProfile: { ...v.value.installedProfile, profile: 'v2' } } },
    { ...v, value: { ...v.value, installedProfile: { ...v.value.installedProfile, releaseVersion: '149.0.0' } } }])
    assert.equal(Boolean(transitionBaseline(other, id)), false);
});
test('visible M1 business checks require settled native window composition',()=>{
  const value={sessionId:id,uncertain:false,active:null,workspaceBusy:false,
    workspace:{state:'PLACED_AWAITING_VISUAL_REVIEW',retryPending:false,zOrder:{state:'VERIFIED'}}};
  assert.doesNotThrow(()=>visibleWorkspace(value,id));
  for(const state of ['WAITING_FOR_UNLOCK','INCOMPLETE','CLOSED','NOT_PREPARED'])
    assert.throws(()=>visibleWorkspace({...value,workspace:{...value.workspace,state}},id));
  assert.throws(()=>visibleWorkspace({...value,workspaceBusy:true},id));
  assert.throws(()=>visibleWorkspace({...value,workspace:{...value.workspace,zOrder:{state:'UNAVAILABLE'}}},id));
  assert.throws(()=>visibleWorkspace(value,'other'));
});
test('partial layout waits only for existing recovery and requires exact settled ordering',()=>{
  const expected={action:'workspace-restore'}, job={state:'PARTIAL'};
  const base={sessionId:id,uncertain:false,active:null,workspaceBusy:false,sourceRecoveryBusy:false};
  const pending={...base,workspace:{state:'WAITING_FOR_WINDOWS',retryPending:true}};
  assert.equal(layoutSettlement(expected,job,pending,id),'PENDING');
  const settled={...base,workspace:{state:'PLACED_AWAITING_VISUAL_REVIEW',retryPending:false,zOrder:{state:'VERIFIED'}}};
  assert.equal(layoutSettlement(expected,job,settled,id),'CONFIRMED');
  assert.equal(layoutSettlement(expected,job,{...settled,workspaceBusy:true},id),'PENDING');
  assert.equal(job.state,'PARTIAL');
  assert.equal(layoutSettlement({action:'service-publish'},job,pending,id),null);
  assert.equal(layoutSettlement(expected,{state:'FAILED'},settled,id),null);
  for(const v of [{...pending,sessionId:'other'},{...pending,uncertain:true},
    {...pending,workspace:{state:'WAITING_FOR_WINDOWS',retryPending:false}},
    {...pending,workspace:{state:'WAITING_FOR_UNLOCK',retryPending:true}},
    {...settled,workspace:{...settled.workspace,zOrder:{state:'UNAVAILABLE'}}},
    {...settled,workspace:{state:'INCOMPLETE',retryPending:false}}])
    assert.throws(()=>layoutSettlement(expected,job,v,id));
});
test('mutation must match the exact currently armed UI command',()=>{
  const expected={action:'service-prepare',team:'brake',profile:'v1'};
  const body={...expected,requestId:id,sessionId:id};
  assert.deepEqual(command(body,expected,id,[]),body);
  for(const wrong of [null,{...expected,profile:'v2'},{...expected,team:'tire'}])
    assert.throws(()=>command(body,wrong,id,[]));
  for(const key of ['force','target','certificate']) assert.throws(()=>command({...body,[key]:true},expected,id,[]));
  assert.throws(()=>command(body,expected,id,[id]));
  assert.throws(()=>command({...body,sessionId:'other'},expected,id,[]));
});
test('layout restoration permits only one exactly armed ordinary UI command',()=>{
  const expected={action:'workspace-restore'};
  const body={...expected,requestId:id,sessionId:id};
  assert.deepEqual(command(body,expected,id,[]),body);
  for(const extra of [{force:true},{target:'production'},{profile:'v1'}])
    assert.throws(()=>command({...body,...extra},expected,id,[]));
  assert.throws(()=>command(body,null,id,[]));
  assert.throws(()=>command(body,expected,id,[id]));
  assert.throws(()=>command({...body,sessionId:'other'},expected,id,[]));
});
test('Advanced settings inspection is exact and does not authorize credential selection',()=>{
  const expected={action:'cloud-inspect'};
  const body={...expected,requestId:id,sessionId:id};
  assert.deepEqual(command(body,expected,id,[]),body);
  for(const change of [{action:'cloud-choose'},{action:'cloud-select'},{certificate:'other'},{pin:'unexpected'}])
    assert.throws(()=>command({...body,...change},expected,id,[]));
  assert.throws(()=>command(body,null,id,[]));
  assert.throws(()=>command(body,expected,id,[id]));
});
test('release values come only from validated product receipts',()=>{
  assert.deepEqual(facts({version:null,release:null,serviceId:null,results:[{facts:{}}]}),{});
  assert.deepEqual(facts({results:[{facts:{version:'150.0.0',releaseHandle:'brake/150.0.0',serviceId:ref}}]}),
    {version:'150.0.0',releaseHandle:'brake/150.0.0',serviceId:ref});
  assert.equal(facts({results:[{facts:{command:{commandId:ref}}}]}).commandId,ref);
  assert.throws(()=>facts({results:[{facts:{serviceId:id}}]}),/SERVICE_RECEIPT_INVALID/);
  assert.throws(()=>facts({results:[{facts:{command:{commandId:id}}}]}),/RESET_RECEIPT_INVALID/);
  for(const v of ['latest','../value','']) assert.throws(()=>facts({results:[{facts:{version:v}}]}));
});
test('VDP readiness keeps its full process and current release contract',()=>{
  const v={activeVersion:'150.0.0',vdpData:'REPORTED_READY',vdpRestarts:'0',processSlotMatches:true};
  assert.equal(installed(v,'platform','150.0.0'),true);
  for(const key of Object.keys(v)) assert.equal(installed({...v,[key]:null},'platform','150.0.0'),false);
  assert.equal(installed(v,'platform','151.0.0'),false);
});
test('service install checks real active instance and error status',()=>{
  const v={observationState:'CURRENT',instances:[{version:'64.0.0',run_state:'active',error_message:false,error_exit_code:0}]};
  assert.equal(installed(v,'tire','64.0.0'),true);
  for(const [key,val] of [['version','63.0.0'],['run_state','failed'],['error_message',true],['error_exit_code',1]])
    assert.equal(installed({...v,instances:[{...v.instances[0],[key]:val}]},'tire','64.0.0'),false);
  for(const observationState of ['STALE','UNAVAILABLE','INCOMPLETE',undefined])
    assert.equal(installed({...v,observationState},'tire','64.0.0'),false);
});
test('reset confirmation binds command, peer model and retained history',()=>{
  const old={local:{teams:{brake:{model:'a'},tire:{model:'b'}}},brake:{productIds:['a']},tire:{productIds:['b']}};
  const after=structuredClone(old);after.brake={...after.brake,resetState:'CLEARED',resetId:id};
  assert.equal(resetPreserved(old,after,'brake',id),true);
  assert.equal(resetPreserved(old,after,'brake','other'),false);
  after.local.teams.tire.model='changed';assert.equal(resetPreserved(old,after,'brake',id),false);
  after.local.teams.tire.model='b';after.tire.productIds=[];assert.equal(resetPreserved(old,after,'brake',id),false);
});

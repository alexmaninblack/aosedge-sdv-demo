// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Isolated mockup state-machine regression tests. No Cloud, VM or browser-profile access.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const mockupPath = path.join(__dirname, '../../docs/demo/mockups');
const source = fs.readFileSync(path.join(mockupPath, 'aosedge-demo-interaction-mockup-2-10.source.html'), 'utf8');
const logic = 'const copy=structuredClone;' + source.slice(source.indexOf('  const names ='), source.indexOf('  // Only mock state')) + source.slice(source.indexOf('  const fixture='), source.indexOf('  function renderNative()'));
// ResizeObserver is a real browser task; the virtual clock alone does not flush it.
// Wait for its actual scale before advancing the queued connector-drawing frame.
async function settleLayout(page){await page.waitForFunction(()=>{const root=document.querySelector('#demo-studio-flow');return Math.abs(Number(getComputedStyle(root).getPropertyValue('--desktop-fit'))-root.clientWidth/1028)<0.0001;});}
test('Standalone contains the same reviewed state machine',()=>{const html=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-10.html'),'utf8');const section=s=>s.slice(s.indexOf('  const names ='),s.lastIndexOf('})();')+5);assert.equal(section(html),section(source));assert.match(html,/CPU · DMIPS/);assert.doesNotMatch(section(html),/data-cpu-bar/);});
function env(saved, epoch = 1800000000000) {
  let now = epoch, seq = 0, queue = [], disk = saved || null;
  class Clock extends Date { constructor(...args) { super(...(args.length ? args : [now])); } static now() { return now; } }
  const context = vm.createContext({structuredClone, Date:Clock, console, root:{dataset:{}}, localStorage:{getItem:()=>disk, setItem:(_,v)=>{disk=v;}}, setTimeout:(fn,ms)=>{queue.push({id:++seq,at:now+ms,fn});return seq;}, clearTimeout:id=>{queue=queue.filter(x=>x.id!==id);}});
  vm.runInContext(logic+';render=()=>{};renderNative=()=>{};renderLogs=()=>{};close=()=>{};dialog=(title,body)=>{globalThis.lastDialog={title,body}};', context);
  const api = {run:x=>vm.runInContext(x,context), value:x=>JSON.parse(vm.runInContext('JSON.stringify('+x+')',context)), saved:()=>disk, now:()=>now,
    advance(ms) {const end=now+ms;for(let n=0;n<1000;n++){queue.sort((a,b)=>a.at-b.at);if(!queue.length||queue[0].at>end){now=end;return;}const x=queue.shift();now=x.at;x.fn();}throw Error('Unbounded timer loop');},
    reload() {api.run('save()');return env(disk,now);}};
  api.run('advancePublications();expireAdvisories();if(!state.uncertain){pump();flushResults();finishLogs();}');
  return api;
}
function setup(e) {e.run("Object.assign(state,{created:true,running:true,provisioned:true,member:true,attached:true,simulator:true,unitId:'T',systemUid:'UID',backendContext:'UID',cloudOnline:true});state.backend={brake:true,tire:true};state.unit.vdp={kind:'vdp',profile:0,version:'0.0.0'};state.runtime.vdp='Running';observe();sampleLocalSignals(true);");return e;}
function release(e,k,n,v,installed=false){e.run(`(()=>{const c={kind:'${k}',profile:${n},version:'${v}',purpose:'test fixture',state:'Published'};state.candidates.${k}[${n}]=c;published[key(c)]={...c};${installed?`state.unit.${k}=fixture(c);state.runtime.${k}='Running';observe();sampleLocalSignals(true);`:''}})()`);}
function signed(e,k='vdp',n=1){e.run(`state.focus='${k}';state.picked.${k}=${n};allocate('${k}',${n});candidate('${k}',${n}).state='Signed';`);}
function publish(e,k='vdp',n=1){e.run(`operation('Publish '+names.${k},publishSteps('${k}',${n}));`);}
test('Manual at zero does not install; stationary Safe Stop does',()=>{const e=setup(env());release(e,'vdp',1,'16.0.0');e.run('pump()');e.advance(3000);assert.equal(e.value('state.unit.vdp.version'),'0.0.0');assert.equal(e.value('state.pending.vdp.phase'),'Ready');e.run("driveMode('safe_stop')");e.advance(1600);assert.equal(e.value('state.unit.vdp.version'),'16.0.0');assert.equal(e.value('state.pending.vdp'),null);assert.equal(e.value('state.cloud.runtime.vdp'),'Not reported');});
test('Safe Stop request while moving still waits for zero',()=>{const e=setup(env());release(e,'vdp',1,'16.0.0');e.run("state.speed=20;pump();driveMode('safe_stop')");e.advance(3000);assert.equal(e.value('state.unit.vdp.version'),'0.0.0');e.run('state.speed=0;pump()');e.advance(1600);assert.equal(e.value('state.unit.vdp.version'),'16.0.0');});
test('Publish before Provision may select a newer warehouse profile',()=>{const e=env();e.run("operation('Create vehicle',createSteps())");e.advance(1500);e.run('state.simulator=true');release(e,'vdp',2,'17.0.0');assert.equal(e.value('lifecycleAction().kind'),'provision');e.run('doLifecycle()');e.advance(3000);assert.equal(e.value('state.pending.vdp.c.profile'),2);e.run("driveMode('safe_stop')");e.advance(1600);assert.equal(e.value('state.unit.vdp.profile'),2);assert.equal(e.value("Object.values(state.completed).some(c=>c.kind==='vdp'&&c.profile===1)"),false);});
test('First service Publish is unassigned; Deploy starts without FOTA gate',()=>{const e=setup(env());release(e,'brake',1,'4.0.0');e.run('pump()');e.advance(3000);assert.equal(e.value('state.unit.brake'),null);e.run("state.mode='autopilot';state.speed=20;operation('Deploy '+names.brake+' to Test',deploySteps('brake'))");e.advance(4000);assert.equal(e.value('state.runtime.brake'),'Running');release(e,'tire',1,'2.0.0');e.run("operation('Deploy '+names.tire+' to Test',deploySteps('tire'))");e.advance(4000);release(e,'brake',2,'5.0.0');e.run('pump()');e.advance(3000);assert.equal(e.value('state.unit.brake.version'),'5.0.0');assert.equal(e.value('state.unit.tire.version'),'2.0.0');assert.deepEqual(e.value('state.assigned'),{brake:true,tire:true});});
test('Full profile story terminates; older observed chapters do not re-open',()=>{const e=setup(env());for(const [k,n,v] of [['vdp',1,'16.0.0'],['brake',1,'4.0.0'],['vdp',2,'17.0.0'],['brake',2,'5.0.0'],['vdp',3,'18.0.0'],['brake',3,'6.0.0'],['tire',1,'2.0.0']]){release(e,k,n,v,true);if(k!=='vdp')e.run(`state.records.${k}.push({systemUid:'UID',serviceVersion:'${v}',messageType:'${k==='brake'&&n===1?'WINDOW_COMPLETION':k==='brake'?'BRAKE_HEALTH_ASSESSMENT':'TIRE_HEALTH_ASSESSMENT'}',dataMode:'VEHICLE_DATA',deliveryState:'DURABLY_RECEIVED',terminalState:'COMPLETE',serviceProfile:${n}})`);}assert.equal(e.value('nextStory()'),null);});
test('Terminal observation completes a chapter without seeing Pending',()=>{const e=setup(env());release(e,'vdp',1,'16.0.0',true);assert.equal(e.value('nextStory().k'),'brake');});
test('Reload during partial Park finishes Park and preserves installed VDP on Resume',()=>{let e=setup(env());release(e,'vdp',3,'18.0.0',true);e.run('park()');e.advance(450);e=e.reload();e.run('reconcile()');e.advance(600);assert.equal(e.value('state.parked'),true);e.run('resume()');e.advance(1200);assert.equal(e.value('state.unit.vdp.version'),'18.0.0');assert.equal(e.value('state.attached'),true);assert.equal(e.value('state.mode'),'manual');});
test('Repeated interruption resumes only remaining steps',()=>{let e=setup(env());release(e,'vdp',3,'18.0.0',true);e.run('park()');e.advance(450);e=e.reload();e.run('reconcile()');e=e.reload();e.run('reconcile()');e.advance(600);assert.equal(e.value('state.parked'),true);assert.equal(e.value('state.wasAttached'),true);});
test('Reconcile does not convert Processing into Published',()=>{let e=env();signed(e);publish(e);e.advance(450);const id=e.value('state.operation.deploymentId');e=e.reload();e.run('reconcile()');assert.equal(e.value('Object.values(published)[0].state'),'Processing');assert.equal(e.value('state.uncertain'),true);e.advance(900);e.run('reconcile()');assert.equal(e.value('candidate("vdp",1).state'),'Published');assert.equal(e.value('Object.values(published)[0].deploymentId'),id);assert.equal(e.value('Object.keys(published).length'),1);});
test('Lost upload response reconciles same server result',()=>{const e=env();signed(e);e.run('state.loseNext=true');publish(e);e.advance(500);e.run('reconcile()');assert.equal(e.value('state.uncertain'),true);e.advance(900);e.run('reconcile()');assert.equal(e.value('candidate("vdp",1).state'),'Published');assert.equal(e.value('Object.keys(published).length'),1);});
test('Failed Quick publication stops; recovery does not continue Provision',()=>{let e=env();e.run('state.failNext=true;state.loseNext=true;quick()');e.advance(4500);assert.equal(e.value('state.uncertain'),true);e=e.reload();e.advance(1000);e.run('reconcile()');assert.equal(e.value('state.provisioned'),false);assert.equal(e.value('candidate("vdp",1).state'),'Error');assert.equal(e.value('state.uncertain'),false);});
test('Rejected publication prepares a new monotonic correction',()=>{const e=env();signed(e);e.run('state.failNext=true');publish(e);e.advance(1400);assert.equal(e.value('candidate("vdp",1).state'),'Error');const v=e.value('ledger.vdp');e.run('allocate("vdp",1)');assert.equal(e.value('ledger.vdp'),v+1);});
test('Unavailable Cloud does not resolve uncertain publication',()=>{const e=env();signed(e);e.run('state.loseNext=true');publish(e);e.advance(1500);e.run('state.cloudReadable=false;reconcile()');assert.equal(e.value('state.uncertain'),true);});
test('Reload during Starting observes remaining startup, not timerless success',()=>{let e=setup(env());release(e,'brake',1,'4.0.0');e.run('state.assigned.brake=true;pump()');e.advance(1700);assert.equal(e.value('state.pending.brake.phase'),'Starting');e=e.reload();e.run('reconcile()');assert.equal(e.value('state.runtime.brake'),'Starting');e.advance(700);assert.equal(e.value('state.runtime.brake'),'Running');assert.equal(e.value('state.pending.brake'),null);});
test('Pending update refuses Park promptly',()=>{const e=setup(env());release(e,'vdp',1,'16.0.0');e.run('pump();park()');assert.equal(e.value('state.running'),true);assert.match(e.value('lastDialog.body'),/unfinished/);});
test('Provision while disconnected cannot claim Online; membership can resume',()=>{const e=setup(env());e.run("state.provisioned=false;state.unitId=null;state.member=false;state.external=false;operation('Provision Test',provisionSteps())");e.advance(1500);assert.equal(e.value('state.cloudOnline'),false);assert.equal(e.value('state.member'),false);e.run('state.external=true;doLifecycle()');e.advance(2000);assert.equal(e.value('state.cloudOnline'),true);assert.equal(e.value('state.member'),true);});
function product(e){release(e,'vdp',3,'18.0.0',true);release(e,'brake',3,'6.0.0',true);e.run('state.assigned.brake=true');}
function completeRetirement(e){e.advance(7000);e.run('observe()');if(e.value('state.finishPending')){e.run('retire()');e.advance(6500);}}
test('Parity: installed warehouse VDP V3 selects Brake V3, not obsolete chapters',()=>{
 const e=setup(env());release(e,'vdp',3,'18.0.0',true);
 assert.deepEqual(e.value('nextStory()'),{k:'brake',n:3,result:false,label:'Open Brake v3'});
});
test('Parity: prior releases remain history, never the current product result',()=>{
 const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);
 assert.equal(e.value('backendProof("brake")'),true);
 release(e,'brake',3,'7.0.0',true);
 assert.equal(e.value('backendProof("brake")'),false);
 assert.equal(e.value('backendSummary("brake").title'),'No result for current release');
 assert.equal(e.value('backendSummary("brake").records.length'),1);
});
test('Parity: completed product predicate matches the working Presenter',()=>{
 const actual=fs.readFileSync(path.join(__dirname,'../../apps/presenter-ui/src/features/service-team/backendProduct.ts'),'utf8');
 const body=actual.slice(actual.indexOf('export function completedProduct')).replace('export ','').replace('row: ProductRow, version: string','row, version').replace('): boolean',')');
 const reference=vm.runInNewContext('const object=v=>v&&typeof v==="object"&&!Array.isArray(v)?v:{};'+body+';completedProduct');
 const e=setup(env());release(e,'brake',1,'4.0.0',true);
 for(const messageType of ['WINDOW_COMPLETION','BRAKE_HEALTH_ASSESSMENT','TIRE_HEALTH_ASSESSMENT','BRAKE_EVENT','FUNCTION_STATUS'])
 for(const terminalState of ['COMPLETE','INCOMPLETE'])
 for(const deliveryState of ['DURABLY_RECEIVED','DURABLE_ACCEPTED','PENDING'])
 for(const serviceVersion of ['4.0.0','3.0.0']){
  const record={messageType,terminalState,deliveryState,serviceVersion};
  const wanted=reference({deliveryState,message:{messageType,serviceVersion,content:{status:terminalState}}},'4.0.0');
  assert.equal(e.value('completedProduct('+JSON.stringify(record)+',"4.0.0")'),wanted,JSON.stringify(record));
 }
 e.run("state.records.brake=[{systemUid:'UID',serviceVersion:'4.0.0',messageType:'WINDOW_COMPLETION',terminalState:'INCOMPLETE',deliveryState:'DURABLY_RECEIVED'}]");
 assert.equal(e.value('backendProof("brake")'),false);
 e.run("state.records.brake[0].terminalState='COMPLETE';state.records.brake[0].dataMode='DEMO_MOCK'");
 assert.equal(e.value('backendProof("brake")'),false);
});
test('Parity: native readiness uses its lease, not a package or Cloud read',()=>{
 const e=setup(env());product(e);e.run('state.review.heartbeat=false;state.cloudReadable=false;state.unit.brake=null');
 assert.equal(e.value('nativeAdvisory("brake")'),'Monitoring');
 e.advance(16000);e.run('sampleLocalSignals()');
 assert.equal(e.value('nativeAdvisory("brake")'),'Not available');
 e.run("state.advisory.brake={text:'Inspection recommended',expiresAt:Date.now()+10000,serviceVersion:null,generation:state.sourceGeneration}");
 // A valid warning is tested with its bound local producer; no readiness lease is needed.
 release(e,'brake',3,'6.0.0',true);e.run("state.review.heartbeat=false;state.readiness.brake=null;emitResult('brake')");e.advance(500);
 assert.equal(e.value('nativeAdvisory("brake")'),'Inspection recommended');
 e.advance(6000);
 assert.equal(e.value('nativeAdvisory("brake")'),'Unavailable');
});
test('Parity: reset rejects a restarted producer even at the same release',()=>{
 const e=setup(env());product(e);e.run("resetScenario('brake');state.producers.brake.epoch='new-process'");e.advance(700);
 assert.equal(e.value('state.resets.brake.status'),'REJECTED');
 assert.equal(e.value('state.resetEpoch.brake'),0);
});
test('Parity: delayed matching CLEAR can confirm timely execution after expiry',()=>{
 const e=setup(env());product(e);e.run("state.review.resetAck=false;resetScenario('brake')");e.advance(1200);
 assert.equal(e.value('state.resets.brake.status'),'WAITING_CLEAR');
 e.advance(61000);e.run('advanceResets()');
 assert.equal(e.value('state.resets.brake.status'),'EXPIRED');
 e.run('state.review.resetAck=true;advanceResets()');
 assert.equal(e.value('state.resets.brake.status'),'CLEARED');
 assert.equal(e.value('state.resetEpoch.brake'),1);
});
test('Parity: uncorrelated CLEAR never confirms reset',()=>{
 const e=setup(env());product(e);e.run("state.review.resetAck=false;resetScenario('brake')");e.advance(1200);
 e.run("confirmReset('brake',{...state.resets.brake.proof,requestId:'OTHER'})");
 assert.equal(e.value('state.resets.brake.status'),'FAILED');
});
test('Parity: current backend results are filtered at reset request, not completion',()=>{
 const e=setup(env());product(e);e.run("resetScenario('brake')");e.advance(1200);
 e.run("state.records.brake=[{id:'during-reset',systemUid:'UID',serviceVersion:'6.0.0',serviceProfile:3,result:'New assessment',capturedAt:new Date(Date.parse(state.resets.brake.issuedAt)+700).toISOString(),receivedAt:time()}]");
 assert.equal(e.value('backendSummary("brake").r.id'),'during-reset');
});
test('Parity: local network state does not instantly change Cloud status',()=>{
 const e=setup(env());e.run('toggleNetwork()');e.advance(1000);
 assert.equal(e.value('state.cloud.status'),'Online');
 e.run('state.review.cloudReports=false');e.advance(40000);e.run('observe()');
 assert.equal(e.value('state.cloud.status'),'Online');
 e.run("state.review.cloudReports=true;scheduleCloudReport('Offline')");e.advance(6500);
 assert.equal(e.value('state.cloud.status'),'Offline');
});
test('Parity: Finish retains identity until Cloud confirms Offline',()=>{
 let e=setup(env());e.run('state.review.cloudReports=false;retire()');e.advance(3000);
 assert.equal(e.value('state.running'),false);assert.equal(e.value('state.simulator'),false);
 assert.equal(e.value('state.provisioned'),true);assert.equal(e.value('state.unitId'),'T');
 assert.equal(e.value('state.finishPending'),true);assert.equal(e.value('lifecycleAction().kind'),'refresh');
 e=e.reload();e.run("state.review.cloudReports=true;scheduleCloudReport('Offline')");e.advance(6500);e.run('retire()');e.advance(6500);
 assert.equal(e.value('state.created'),false);
});
test('Parity: failed service inventory retains last known rather than fabricating absence',()=>{
 const e=setup(env());product(e);e.run('state.observations.services="PARTIAL";state.unit.brake=null;observe()');
 assert.equal(e.value('state.cloud.unit.brake.version'),'6.0.0');
 assert.equal(e.value('lifecycleAction().kind'),'refresh');
 e.run('state.observations.services="CURRENT";observe()');
 assert.equal(e.value('state.cloud.unit.brake'),null);
});
test('Parity: resource samples retain time and value on failure; absent service is not zero',()=>{
 const e=setup(env());const before=e.value('resourceRows()');
 assert.equal(e.value('resourceRows("Tire instance").value'),null);
 e.advance(2000);e.run('state.observations.resources="UNAVAILABLE"');
 const after=e.value('resourceRows()');
 assert.equal(after.available,false);assert.deepEqual(after.sample,before.sample);assert.equal(after.value,before.value);
});
test('Parity: explicit control recovery stops; the driving request is not replayed',()=>{
 const e=setup(env());e.run("state.controlConnected=false;driveMode('autopilot')");
 assert.equal(e.value('state.mode'),'manual');assert.equal(e.value('state.speed'),0);assert.equal(e.value('state.brake'),1);
 e.run("driveMode('autopilot')");assert.equal(e.value('state.mode'),'autopilot');
});
test('Parity: unsigned packages survive Cloud switch and require fresh signing',()=>{
 const e=env();e.run("session=()=>{};allocate('vdp',1);candidate('vdp',1).state='Signed';candidate('vdp',1).sha256='old';state.config.preview='aoscloud.io';cloudAction('select')");
 assert.equal(e.value('candidate("vdp",1).state'),'Prepared');
 assert.equal(e.value('"sha256" in candidate("vdp",1)'),false);
 assert.equal(e.value('state.config.sp'),false);assert.equal(e.value('state.config.setup'),'MISSING');
 assert.equal(e.value('releaseAction().disabled'),true);
 e.run('state.created=true');assert.equal(e.value('releaseAction().kind'),'sign-publish');
 const previous=e.value('candidate("vdp",1).version');e.run("allocate('vdp',1)");assert.notEqual(e.value('candidate("vdp",1).version'),previous);
});
test('Parity: native password prompt can pause Create and Quick without mutating the run',()=>{
 for(const action of ['requestCreate()','quick()']){
  const e=env();e.run('state.vmAccess=false;'+action);e.advance(10000);
  assert.equal(e.value('state.created'),false);assert.equal(e.value('lastDialog.title'),'Demo Control — VM access');
 }
});
test('Parity: synthetic test records remain separate history',()=>{
 const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);
 e.run("state.records.brake[0].dataMode='DEMO_MOCK'");
 assert.equal(e.value('backendSummary("brake").records.length'),0);
 assert.equal(e.value('backendSummary("brake").mockRecords.length'),1);
 assert.equal(e.value('backendProof("brake")'),false);
});
test('Parity: invalid proof timestamps cannot confirm reset',()=>{
 const e=setup(env());product(e);e.run("state.review.resetAck=false;resetScenario('brake')");e.advance(1200);
 e.run("confirmReset('brake',{...state.resets.brake.proof,issuedAt:'not-a-time'})");
 assert.equal(e.value('state.resets.brake.status'),'FAILED');
});
test('Offline result, reconnect and reload retain exactly one delayed receipt',()=>{let e=setup(env());product(e);e.run("state.external=false;emitResult('brake')");e.advance(400);assert.ok(e.value('state.advisory.brake'));assert.equal(e.value('state.records.brake.length'),0);e=e.reload();e.run('toggleNetwork()');e.advance(1500);assert.equal(e.value('state.records.brake.length'),1);assert.equal(e.value('state.records.brake[0].delayed'),true);e=e.reload();e.advance(1500);assert.equal(e.value('state.records.brake.length'),1);});
test('Online outbox resumes after reload before backend receipt',()=>{let e=setup(env());product(e);e.run("emitResult('brake')");e.advance(300);e=e.reload();e.advance(1000);assert.equal(e.value('state.outbox.length'),0);assert.equal(e.value('state.records.brake.length'),1);});
test('Advisory lease expires without deleting backend history',()=>{const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);assert.ok(e.value('state.advisory.brake'));e.advance(31000);e.run('expireAdvisories()');assert.equal(e.value('state.advisory.brake'),null);assert.equal(e.value('state.records.brake.length'),1);});
test('Changed service profile, generation and restart clear live advisory',()=>{const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);release(e,'brake',1,'7.0.0',true);e.run('expireAdvisories()');assert.equal(e.value('state.advisory.brake'),null);product(e);e.run("emitResult('brake')");e.advance(1000);e.run('state.sourceGeneration++;expireAdvisories()');assert.equal(e.value('state.advisory.brake'),null);e.run("emitResult('brake')");e.advance(1000);e.run('park()');e.advance(1000);e.run('resume()');e.advance(1200);assert.equal(e.value('state.advisory.brake'),null);});
test('Retire clears owned run, preserving release catalog and numbering',()=>{const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);e.run('ledger.vdp=18;retire()');e.advance(8000);completeRetirement(e);assert.equal(e.value('state.created'),false);assert.equal(e.value('state.unitId'),null);assert.deepEqual(e.value('state.records'),{brake:[],tire:[]});assert.equal(e.value('ledger.vdp'),18);assert.equal(e.value('Object.keys(published).length'),2);e.run('allocate("vdp",1)');assert.equal(e.value('candidate("vdp",1).version'),'19.0.0');});
test('Interrupted Retire resumes without losing next-cycle identity',()=>{let e=setup(env());e.run('retire()');e.advance(3150);e=e.reload();e.run('reconcile()');e.advance(8000);completeRetirement(e);assert.equal(e.value('state.created'),false);assert.equal(e.value('state.cycle'),2);});
test('Separate deprovision/delete and fresh Create leave no old identity',()=>{const e=setup(env());e.run("operation('Deprovision Test',deprovisionSteps())");e.advance(3000);assert.equal(e.value('state.provisioned'),false);e.run("operation('Delete Unit',deleteSteps())");e.advance(1500);assert.equal(e.value('state.unitId'),null);assert.equal(e.value('state.running'),false);e.run('retire(true)');e.advance(8000);assert.equal(e.value('state.created'),true);assert.equal(e.value('state.unit.vdp.version'),'0.0.0');assert.equal(e.value('state.unitId'),null);});
test('Quick preparation ends in Manual with downloaded VDP, not auto Safe Stop',()=>{const e=env();e.run('quick()');e.advance(9000);assert.equal(e.value('state.member'),true);assert.equal(e.value('state.attached'),true);assert.equal(e.value('state.mode'),'manual');assert.equal(e.value('state.unit.vdp.version'),'0.0.0');assert.equal(e.value('state.pending.vdp.phase'),'Ready');});
test('Fresh Full story does not skip its publication because old Cloud releases remain',()=>{const e=setup(env());release(e,'vdp',3,'18.0.0',true);e.run('retire(true)');e.advance(9000);completeRetirement(e);e.run('doLifecycle()');e.advance(1500);assert.equal(e.value('state.simulator'),true);assert.equal(e.value('state.attached'),false);assert.equal(e.value('Object.keys(published).length'),1);assert.equal(e.value('lifecycleAction().kind'),'baseline');});

function readyReplacement(){const e=setup(env());release(e,'vdp',1,'16.0.0',true);release(e,'vdp',2,'17.0.0');e.run('pump()');e.advance(1000);return e;}
test('Parity: a Cloud-pending component keeps the guide on Platform, not another release',()=>{
 const e=readyReplacement();
 assert.equal(e.value('lifecycleAction().kind'),'vdp-pending');
 e.run("state.cloud.pending.vdp.error='FAILED'");
 assert.equal(e.value('lifecycleAction().kind'),'inspect');
});
test('Offline local VDP apply leaves Cloud on its last report until reconnect',()=>{
 let e=readyReplacement();e.run('toggleNetwork()');e.advance(1000);e.run("driveMode('safe_stop')");e.advance(1600);
 assert.equal(e.value('state.unit.vdp.version'),'17.0.0');assert.equal(e.value('state.runtime.vdp'),'Running');
 assert.equal(e.value('state.cloud.unit.vdp.version'),'16.0.0');assert.equal(e.value('state.cloud.pending.vdp.c.version'),'17.0.0');
 e.advance(4000); assert.equal(e.value('state.cloud.online'),false);assert.equal(e.value("Boolean(state.completed['vdp:17.0.0'])"),false);
 e=e.reload();e.run('observe()');assert.equal(e.value('state.cloud.unit.vdp.version'),'16.0.0');
 e.run('toggleNetwork()');e.advance(2000);assert.equal(e.value('state.cloud.unit.vdp.version'),'17.0.0');assert.equal(e.value('state.cloud.pending.vdp'),null);
 assert.equal(e.value("state.completed['vdp:17.0.0'].version"),'17.0.0');
});
test('Disconnect grace period cannot leak local inventory or service runtime to Cloud',()=>{
 const e=setup(env());release(e,'brake',1,'4.0.0',true);e.run('toggleNetwork();state.runtime.brake="Stopped";state.unit.brake.version="5.0.0";observe()');
 assert.equal(e.value('state.cloud.online'),true);assert.equal(e.value('state.cloud.unit.brake.version'),'4.0.0');assert.equal(e.value('state.cloud.runtime.brake'),'Running');
 e.advance(6500);assert.equal(e.value('state.cloud.online'),false);assert.equal(e.value('state.cloud.runtime.brake'),'Running');
});
test('Cloud can know a desired service while its offline inventory is unchanged',()=>{
 const e=setup(env());e.run('state.external=false;state.cloudOnline=false;state.assigned.brake=true');release(e,'brake',1,'4.0.0');e.run('pump();observe()');
 assert.equal(e.value('state.cloud.unit.brake'),null);assert.equal(e.value('state.cloud.pending.brake.c.version'),'4.0.0');
 assert.equal(e.value('state.pending.brake.downloaded'),false);
});
test('Device reports reach simulated Cloud while operator read access is unavailable',()=>{
 const e=readyReplacement();e.run("state.cloudReadable=false;driveMode('safe_stop')");e.advance(1600);
 assert.equal(e.value('state.cloud.unit.vdp.version'),'16.0.0');assert.equal(e.value('state.deviceReport.unit.vdp.version'),'17.0.0');
 e.run('state.external=false;state.cloudOnline=false;state.cloudReadable=true;observe()');
 assert.equal(e.value('state.cloud.unit.vdp.version'),'17.0.0');assert.equal(e.value('state.cloud.online'),false);
});
test('A new offline identity never inherits the previous Unit inventory',()=>{
 const e=setup(env());release(e,'vdp',3,'18.0.0',true);e.run('state.unitId="NEW";state.external=false;state.cloudOnline=false;observe()');
 assert.equal(e.value('state.cloud.unit.vdp'),null);assert.equal(e.value('state.deviceReport'),null);assert.equal(e.value('state.cloud.runtime.brake'),'Not reported');
});
test('Existing 2.8 storage migrates the last Cloud report without reading an offline guest',()=>{
 const e=setup(env());release(e,'vdp',1,'16.0.0',true);e.run('delete state.deviceReport;state.unit.vdp.version="17.0.0";state.external=false;state.cloudOnline=false;observe()');
 assert.equal(e.value('state.cloud.unit.vdp.version'),'16.0.0');
});
for(const delay of [300,1000])test('Loss of Safe Stop at '+delay+'ms preserves VDP and requires a fresh gated attempt',()=>{
 const e=readyReplacement();e.run("driveMode('safe_stop')");e.advance(delay);assert.equal(e.value('state.unit.vdp.version'),'16.0.0');
 e.run("driveMode('autopilot');state.speed=10;pump()");e.advance(1600);
 assert.equal(e.value('state.unit.vdp.version'),'16.0.0');assert.equal(e.value('state.runtime.vdp'),'Running');assert.equal(e.value('state.pending.vdp.phase'),'Ready');
 assert.equal(e.value('state.cloud.unit.vdp.version'),'16.0.0');assert.equal(e.value('applications.size'),0);
 e.run("state.speed=0;driveMode('safe_stop')");e.advance(1600);assert.equal(e.value('state.unit.vdp.version'),'17.0.0');assert.equal(e.value('state.pending.vdp'),null);
});
test('Safe Stop loss and return before the old timer fires cannot reuse that timer',()=>{
 const e=readyReplacement();e.run("driveMode('safe_stop')");e.advance(300);e.run("driveMode('manual');driveMode('safe_stop')");
 e.advance(1150);assert.equal(e.value('state.unit.vdp.version'),'16.0.0');e.advance(300);assert.equal(e.value('state.unit.vdp.version'),'17.0.0');
});
for(const change of ['state.speed=1','state.attached=false','state.running=false'])test('Invalid vehicle evidence blocks activation: '+change,()=>{
 const e=readyReplacement();e.run("driveMode('safe_stop')");e.advance(1000);e.run(change+';pump()');e.advance(1000);
 assert.equal(e.value('state.unit.vdp.version'),'16.0.0');assert.equal(e.value('state.pending.vdp.phase'),'Ready');
});
for(const delay of [300,1000])test('Reload at '+delay+'ms does not restore a persisted Safe Stop authorization',()=>{
 let e=readyReplacement();e.run("driveMode('safe_stop')");e.advance(delay);e=e.reload();e.run('reconcile()');e.advance(2000);
 assert.equal(e.value('state.mode'),'manual');assert.equal(e.value('state.unit.vdp.version'),'16.0.0');assert.equal(e.value('state.pending.vdp.phase'),'Ready');
 e.run("driveMode('safe_stop')");e.advance(1600);assert.equal(e.value('state.unit.vdp.version'),'17.0.0');
});

test('Browser: actual buttons, full VDP/Brake/Tire story, offline, Park and Retire', {skip:!process.env.MOCKUP_PLAYWRIGHT,timeout:90000}, async()=>{
  const {chromium}=require(process.env.MOCKUP_PLAYWRIGHT);
  const browser=await chromium.launch({executablePath:process.env.MOCKUP_CHROME,headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1512,height:982}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    const html=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-10.html'),'utf8');
    await page.route('**/*',route=>route.request().url().startsWith('http://studio-mock.invalid/')?route.fulfill({contentType:'text/html',body:html}):route.abort());
    await page.clock.install();await page.goto('http://studio-mock.invalid/');
    const tick=ms=>page.clock.runFor(ms),click=sel=>page.locator(sel).filter({visible:true}).first().click();
    const read=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('aosedge-studio-mockup-2.10')).state);
    for(const size of [{width:1728,height:1117},{width:1280,height:720}]){
      await page.setViewportSize(size);await settleLayout(page);await tick(100);
      const fit=await page.evaluate(()=>({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,bottom:document.querySelector('.dw-shell').getBoundingClientRect().bottom}));
      assert.ok(fit.width<=size.width&&fit.height<=size.height&&fit.bottom<=size.height,'The fixed desktop composition fits without page scrolling');
      for(const tab of ['dashboard','vehicle','data']){
        await click('[data-telemetry-tab="'+tab+'"]');
        const inside=await page.evaluate(()=>{
          const edge=document.querySelector('.accepted-native-content').getBoundingClientRect().bottom;
          return [...document.querySelectorAll('.accepted-modes button,[data-telemetry-page]:not([hidden])>*')].every(e=>e.getBoundingClientRect().bottom<=edge+1);
        });
        assert.ok(inside,'Telemetry '+tab+' and driving buttons stay inside the fixed panel');
      }
    }
    await click('[data-telemetry-tab="dashboard"]');
    await page.setViewportSize({width:1512,height:982});await settleLayout(page);await tick(100);
    await click('[data-workspace="tire"]');await page.getByRole('button',{name:'Details',exact:true}).click();
    assert.ok(await page.locator('.v27-detail-row').count()>=7);
    assert.match(await page.locator('.dw-dialog-copy').innerText(),/No real artifact is generated/);
    await page.getByRole('button',{name:'Close',exact:true}).click();await click('[data-workspace="lifecycle"]');
    async function releaseUI(k,n){await click('[data-workspace="'+k+'"]');await click('[data-choose="'+n+'"]');for(const ms of [1000,2200]){await click('[data-action="primary"]');await click('[data-action="confirm"]');await tick(ms);}let s=await read();if(k!=='vdp'&&!s.assigned[k]){await click('[data-action="primary"]');await click('[data-action="confirm"]');await tick(4000);}}
    async function drive(){await click('[data-action="drive"]');await tick(3500);await click('[data-action="stop"]');await tick(2500);}
    await click('[data-guide]');await tick(1700);await click('[data-guide]');await tick(1500);
    await releaseUI('vdp',1);await click('[data-workspace="lifecycle"]');await click('[data-guide]');await tick(3000);await drive();
    for(const [k,n] of [['brake',1],['vdp',2],['brake',2],['vdp',3],['brake',3],['tire',1]]){await releaseUI(k,n);await drive();}
    let s=await read();assert.equal(s.unit.vdp.profile,3);assert.equal(s.unit.brake.profile,3);assert.equal(s.unit.tire.profile,1);assert.equal(s.runtime.brake,'Running');assert.equal(s.runtime.tire,'Running');assert.ok(s.records.brake.length>=3);assert.ok(s.records.tire.length>=1);
    await click('[data-workspace="lifecycle"]');
    for(const size of [{width:1728,height:1117},{width:1512,height:982},{width:1280,height:720}]){
      await page.setViewportSize(size);await settleLayout(page);await tick(100);
      const fit=await page.evaluate(()=>{
        const panel=document.querySelector('.dw-panel'),footer=document.querySelector('.dw-footer'),guide=document.querySelector('.concept-guide'),map=document.querySelector('.dw-map');
        return {panel:panel.getBoundingClientRect().bottom,footer:footer.getBoundingClientRect().bottom,guide:guide.getBoundingClientRect().bottom,footerTop:footer.getBoundingClientRect().top,map:map.getBoundingClientRect().bottom,guideTop:guide.getBoundingClientRect().top,overflow:panel.scrollHeight-panel.clientHeight,width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight};
      });
      assert.ok(fit.footer<=fit.panel+1&&fit.footer<=size.height&&fit.overflow<=1,'Populated architecture/footer fit at '+JSON.stringify({size,fit}));
      assert.ok(fit.guide<=fit.footerTop&&fit.map<=fit.guideTop,'Architecture, guide and footer do not overlap');
      assert.ok(fit.width<=size.width&&fit.height<=size.height,'No page scrolling '+JSON.stringify({size,fit}));
      assert.equal(await page.locator('.dw-slot button:not([hidden]) .b2-icon').count(),3);
    }
    await page.setViewportSize({width:1728,height:1117});await settleLayout(page);await tick(100);
    if(process.env.MOCKUP_SCREENSHOT)await page.screenshot({path:process.env.MOCKUP_SCREENSHOT});
    assert.equal(await page.locator('[data-guide]').innerText(),'Finish demo');
    await click('[data-guide]');assert.equal(await page.locator('#dw-dialog-title').innerText(),'Finish this demo?');await page.keyboard.press('Escape');assert.equal((await read()).created,true);
    await click('[data-page="cloud"]');await click('[data-popup-tab="resources"]');assert.match(await page.locator('.dw-dialog-copy').innerText(),/DMIPS/);await click('[data-action="close"]');
    await click('[data-action="network"]');await tick(6500);await drive();s=await read();assert.equal(s.cloudOnline,false);assert.ok(s.outbox.length);await click('[data-action="network"]');await tick(2200);assert.equal((await read()).outbox.length,0);
    await click('[data-action="operator"]');await click('[data-op="park"]');await tick(1300);assert.equal((await read()).parked,true);
    await click('[data-action="operator"]');await click('[data-op="resume"]');await tick(1300);assert.equal((await read()).unit.vdp.profile,3);
    await click('[data-action="operator"]');await click('[data-op="retire"]');await click('[data-action="confirm"]');await tick(8000);await page.keyboard.press('Escape');await click('[data-guide]');await tick(6500);s=await read();assert.equal(s.created,false);assert.equal(s.unitId,null);assert.deepEqual(s.records,{brake:[],tire:[]});assert.deepEqual(errors,[]);
  } finally {await browser.close();}
});

test('Browser: offline Cloud display and Safe Stop loss during activation', {skip:!process.env.MOCKUP_PLAYWRIGHT,timeout:60000}, async()=>{
 const {chromium}=require(process.env.MOCKUP_PLAYWRIGHT),browser=await chromium.launch({executablePath:process.env.MOCKUP_CHROME,headless:true});
 const html=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-10.html'),'utf8');
 try{for(const scenario of ['offline','gate']){
   const page=await browser.newPage({viewport:{width:1280,height:720}}),e=readyReplacement(),errors=[];
   e.run('state.view="studio";state.focus="vdp";state.picked.vdp=2;save()');
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',r=>r.request().url().startsWith('http://studio-mock.invalid/')?r.fulfill({contentType:'text/html',body:html}):r.abort());
   await page.addInitScript(saved=>localStorage.setItem('aosedge-studio-mockup-2.10',saved),e.saved());
   await page.clock.install();await page.goto('http://studio-mock.invalid/');
   const click=s=>page.locator(s).filter({visible:true}).first().click(),tick=ms=>page.clock.runFor(ms);
   const read=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('aosedge-studio-mockup-2.10')).state);
   await click('[data-action="primary"]');await tick(100);
   if(scenario==='offline'){await click('[data-action="network"]');await tick(1100);}
   await click('[data-action="stop"]');await tick(1000);
   if(scenario==='gate'){await click('[data-action="drive"]');}
   await tick(1600);
   assert.equal((await read()).unit.vdp.version,scenario==='offline'?'17.0.0':'16.0.0');
   assert.equal(await page.locator('[data-path-unit]').innerText(),'16.0.0');
   assert.match(await page.locator('[data-path-unit-note]').innerText(),/Pending 17.0.0/);
   assert.equal(await page.locator('[data-action="primary"]').innerText(),'Observe update');
   await click('[data-workspace="lifecycle"]');
   assert.match(await page.locator('[data-map-vdp]').innerText(),/16.0.0/);
   assert.match(await page.locator('[data-map-pending]').innerText(),/17.0.0/);
   const fit=await page.evaluate(()=>{const p=document.querySelector('.dw-panel'),f=document.querySelector('.dw-footer');return {overflow:p.scrollHeight-p.clientHeight,bottom:f.getBoundingClientRect().bottom,panel:p.getBoundingClientRect().bottom};});
   assert.ok(fit.overflow<=1&&fit.bottom<=fit.panel+1&&fit.bottom<=720,'Pending state fits '+JSON.stringify(fit));
   await click(scenario==='offline'?'[data-action="network"]':'[data-action="stop"]');await tick(3000);
   assert.equal((await read()).cloud.unit.vdp.version,'17.0.0');assert.equal((await read()).pending.vdp,null);
   assert.deepEqual(errors,[]);await page.close();
 }}finally{await browser.close();}
});

test('The retained 2.7 source and standalone are unchanged',()=>{
 const {createHash}=require('node:crypto');
 for(const [suffix,expected] of [['source.html','0b8e8e861740cb02a0a1fe39c6627b03303d05b31b64b4cf22436e501792d5db'],['html','9bce32fcecc46d0bcb061e181b4dc0cbe0cc7bb81e5c504327689a794ca648cd']])
  assert.equal(createHash('sha256').update(fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-7.'+suffix))).digest('hex'),expected);
});
test('2.8 retains the CARLA reference and the official logo unchanged',()=>{
 const old=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-6.source.html'),'utf8');
 const images=s=>[...s.matchAll(/<img\b[^>]*>/g)].map(m=>m[0]);
 assert.deepEqual(images(source),images(old));
});
test('2.8 visual adapter cannot issue actions, access Cloud or persist simulation state',()=>{
 const adapter=source.match(/<script data-visual-edition="2.7">([\s\S]*?)<\/script>/)[1];
 assert.doesNotMatch(adapter,/localStorage|sessionStorage|fetch\(|XMLHttpRequest|WebSocket|dispatchEvent|\.click\(|\.focus\(|\bstate\.[A-Za-z_$]/);
 assert.match(source,/<style data-visual-edition="2.7">/);
});

test('2.10 starts local controls before Provision and attaches without a source restart',()=>{
 const e=env();e.run("operation('Create vehicle',createSteps())");e.advance(1500);e.run('doLifecycle()');e.advance(1100);
 assert.equal(e.value('state.simulator'),true);assert.equal(e.value('state.attached'),false);
 const gen=e.value('state.sourceGeneration');release(e,'vdp',1,'16.0.0');e.run('doLifecycle()');e.advance(3000);
 assert.equal(e.value('state.attached'),true);assert.equal(e.value('state.sourceGeneration'),gen);
 assert.equal(e.value('state.mode'),'manual');assert.equal(e.value('state.unit.vdp.profile'),0);
 assert.equal(e.value('state.image'),'35');
});
test('2.10 independently distinguishes absent support, waiting producer and monitoring',()=>{
 const e=setup(env());assert.equal(e.value('nativeAdvisory("brake")'),'Not available');
 release(e,'vdp',3,'18.0.0',true);assert.equal(e.value('nativeAdvisory("brake")'),'Waiting for service');
 release(e,'brake',2,'5.0.0',true);assert.equal(e.value('nativeAdvisory("brake")'),'Waiting for service');
 release(e,'brake',3,'6.0.0',true);release(e,'tire',1,'2.0.0',true);
 assert.equal(e.value('nativeAdvisory("brake")'),'Monitoring');assert.equal(e.value('nativeAdvisory("tire")'),'Monitoring');
 e.run('state.external=false');assert.equal(e.value('nativeAdvisory("brake")'),'Monitoring');
 e.run('state.runtime.brake="Stopped";sampleLocalSignals(true)');assert.equal(e.value('nativeAdvisory("brake")'),'Unavailable');
 assert.equal(e.value('nativeAdvisory("tire")'),'Monitoring');
});
for(const k of ['brake','tire'])test('2.10 '+k+' reset requires correlated CLEAR, preserves peer and history, then allows a new warning',()=>{
 const e=setup(env());product(e);release(e,'tire',1,'2.0.0',true);e.run("emitResult('brake');emitResult('tire')");e.advance(1000);
 const peer=k==='brake'?'tire':'brake',peerWarning=e.value('state.advisory.'+peer),versions=e.value('state.unit');
 e.run(`resetScenario('${k}')`);assert.equal(e.value(`state.resets.${k}.status`),'PENDING');
 e.advance(700);assert.equal(e.value(`state.resets.${k}.status`),'WAITING_CLEAR');assert.ok(e.value(`state.advisory.${k}`));
 e.advance(400);assert.equal(e.value(`state.resets.${k}.status`),'CLEARED');assert.equal(e.value(`state.advisory.${k}`),null);
 assert.equal(e.value(`state.records.${k}.length`),1);assert.deepEqual(e.value('state.unit'),versions);
 assert.deepEqual(e.value('state.advisory.'+peer),peerWarning);assert.equal(e.value(`backendSummary('${k}').title`),'Waiting for a new drive');
 e.run(`emitResult('${k}')`);e.advance(1000);assert.ok(e.value(`state.advisory.${k}`));assert.equal(e.value(`state.records.${k}.length`),2);
 assert.equal(e.value(`backendSummary('${k}').title`),'Inspection recommended');
});
test('2.10 reset eligibility includes Brake V3 and Tire V1 only with live support',()=>{
 const e=setup(env());release(e,'vdp',3,'18.0.0',true);release(e,'brake',2,'5.0.0',true);release(e,'tire',1,'2.0.0',true);
 assert.equal(e.value('resetEligible("brake")'),false);assert.equal(e.value('resetEligible("tire")'),true);
 release(e,'brake',3,'6.0.0',true);assert.equal(e.value('resetEligible("brake")'),true);
 e.run('state.external=false;resetScenario("brake")');assert.equal(e.value('state.resets.brake'),null);
});
test('2.10 reset cannot execute against a new service version',()=>{
 const e=setup(env());product(e);e.run('resetScenario("brake")');release(e,'brake',3,'7.0.0',true);e.advance(700);
 assert.equal(e.value('state.resets.brake.status'),'REJECTED');
});
test('2.10 offline reset expires rather than running after a later reconnect',()=>{
 const e=setup(env());product(e);e.run('resetScenario("brake");state.external=false');e.advance(61000);e.run('state.external=true;advanceResets()');
 assert.equal(e.value('state.resets.brake.status'),'EXPIRED');assert.equal(e.value('state.resetEpoch.brake'),0);
});
test('2.10 reset interrupted after service acknowledgement resumes CLEAR without resetting twice',()=>{
 let e=setup(env());product(e);e.run('resetScenario("brake")');e.advance(700);e=e.reload();e.run('advanceResets()');e.advance(500);
 assert.equal(e.value('state.resets.brake.status'),'CLEARED');assert.equal(e.value('state.resetEpoch.brake'),1);
});
test('2.10 Finish exits pending VDP without Safe Stop and cannot resurrect the discarded operation',()=>{
 const e=readyReplacement();e.run('retire()');e.advance(15000);completeRetirement(e);
 assert.equal(e.value('state.created'),false);assert.equal(e.value('state.unitId'),null);assert.equal(e.value('state.unit.vdp'),null);
});
test('2.10 Finish stops locally on Cloud read failure, preserves identity and continues retirement',()=>{
 const e=readyReplacement();e.run('state.cloudReadable=false;retire()');
 assert.equal(e.value('state.running'),false);assert.equal(e.value('state.simulator'),false);assert.equal(e.value('state.unitId'),'T');
 assert.equal(e.value('lifecycleAction().kind'),'finish');e.run('state.cloudReadable=true;doLifecycle()');e.advance(8000);completeRetirement(e);
 assert.equal(e.value('state.created'),false);assert.equal(e.value('state.unitId'),null);
});
test('2.10 summaries use backend receipts, not local queued results',()=>{
 const e=setup(env());product(e);e.run('state.external=false;emitResult("brake")');e.advance(700);
 assert.equal(e.value('backendSummary("brake").records.length'),0);assert.equal(e.value('backendSummary("brake").title'),'No results yet');
 assert.ok(e.value('state.advisory.brake'));e.run('state.external=true;flushResults()');e.advance(800);
 assert.equal(e.value('backendSummary("brake").records.length'),1);
});
test('2.10 never calls a real backend or native bridge',()=>{
 assert.doesNotMatch(source,/\b(fetch|XMLHttpRequest|WebSocket)\s*\(|window\.openai|localhost|127\.0\.0\.1/);
 assert.match(source,/aosedge-studio-mockup-2\.10/);
});
test('2.10 preserves both complete 2.8 and partial 2.9 byte-for-byte',()=>{
 const {createHash}=require('node:crypto');
 for(const [file,digest] of [
  ['2-8.source.html','84dcd3d7c174054fc7b89ffe6d3a91ebdd56670d4d2e4ff2b23033a4324a0c0d'],
  ['2-8.html','6564ae45b718cd3e4ac52bcf587d9f863422f1682d3836370c8828c978561f04'],
  ['2-9.source.html','b5f0b5b64f9abc20929dc4434701575774c69ee1c259c0307dd1991d054072b4'],
  ['2-9.html','19cc53cdf8cf7f8557efa5563f5b467858c8316aa9bde57739f27055386726b9']])
  assert.equal(createHash('sha256').update(fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-'+file))).digest('hex'),digest);
});

test('Browser: Session Cloud/setup, native-access cancellation and review controls are isolated', {skip:!process.env.MOCKUP_PLAYWRIGHT,timeout:90000}, async()=>{
 const {chromium}=require(process.env.MOCKUP_PLAYWRIGHT),browser=await chromium.launch({executablePath:process.env.MOCKUP_CHROME,headless:true});
 const html=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-10.html'),'utf8');
 const page=await browser.newPage({viewport:{width:1728,height:1117}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.route('**/*',r=>r.request().url().startsWith('http://studio-mock.invalid/')?r.fulfill({contentType:'text/html',body:html}):r.abort());
  await page.clock.install();await page.goto('http://studio-mock.invalid/');
  const click=s=>page.locator(s).filter({visible:true}).first().click(),body=()=>page.locator('.dw-dialog-copy').innerText();
  const read=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('aosedge-studio-mockup-2.10')).state);
  const fit=async()=>{const r=await page.evaluate(()=>{const d=document.querySelector('.dw-dialog'),p=document.querySelector('.dw-panel'),c=document.querySelector('.dw-dialog-copy');return {dialog:d.getBoundingClientRect().toJSON(),panel:p.getBoundingClientRect().toJSON(),overflow:c.scrollHeight-c.clientHeight}});assert.ok(r.dialog.top>=r.panel.top&&r.dialog.bottom<=r.panel.bottom+1&&r.overflow<=1,JSON.stringify(r));};
  for(const size of [{width:1728,height:1117},{width:1512,height:982},{width:1280,height:720}]){
   await page.setViewportSize(size);await settleLayout(page);await click('[data-action=operator]');
   for(const tab of ['lifecycle','cloud','setup','review']){await click('[data-session-tab='+tab+']');await fit();}
   await page.keyboard.press('Escape');
  }
  await click('[data-action=operator]');await click('[data-session-tab=cloud]');await click('[data-cloud-action=choose]');
  await click('[data-certificate="aoscloud.io"]');await click('[data-cloud-action=select]');
  assert.equal((await read()).config.domain,'aoscloud.io');
  await click('[data-session-tab=setup]');await click('[data-cloud-action=check]');assert.match(await body(),/Certificate mismatch/);
  await click('[data-cloud-action=prepare]');assert.equal((await read()).config.setup,'MISSING');
  await click('[data-session-tab=review]');await click('[data-review=sp]');
  await click('[data-action=operator]');await click('[data-session-tab=setup]');await click('[data-cloud-action=prepare]');
  assert.equal((await read()).config.setup,'READY');
  await click('[data-session-tab=review]');await click('[data-review=vm-access]');
  await click('[data-guide]');assert.match(await body(),/No password|No secret/);
  await page.keyboard.press('Escape');assert.equal((await read()).created,false);
  await click('[data-guide]');await click('[data-action=confirm]');await page.clock.runFor(1600);
  assert.equal((await read()).created,true);
  await click('[data-workspace=vdp]');await click('[data-action=primary]');await click('[data-action=confirm]');await page.clock.runFor(1200);
  assert.equal(await page.locator('[data-action=primary]').innerText(),'Sign & publish');
  const version=(await read()).candidates.vdp[1].version;
  await click('[data-prepare-again]');await click('[data-action=confirm]');await page.clock.runFor(1200);
  assert.notEqual((await read()).candidates.vdp[1].version,version);
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
});

test('Browser: inline receipts, all dialogs, keyboard return, independent Brake V3 / Tire V1 resets and renewed warnings', {skip:!process.env.MOCKUP_PLAYWRIGHT,timeout:90000}, async()=>{
 const {chromium}=require(process.env.MOCKUP_PLAYWRIGHT),browser=await chromium.launch({executablePath:process.env.MOCKUP_CHROME,headless:true});
 const html=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-10.html'),'utf8');
 const e=setup(env(undefined,Date.now()));product(e);release(e,'tire',1,'2.0.0',true);
 for(let i=0;i<6;i++){e.run("emitResult('brake');emitResult('tire')");e.advance(1000);}e.run('save()');
 const page=await browser.newPage({viewport:{width:1728,height:1117}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.route('**/*',r=>r.request().url().startsWith('http://studio-mock.invalid/')?r.fulfill({contentType:'text/html',body:html}):r.abort());
  await page.addInitScript(saved=>localStorage.setItem('aosedge-studio-mockup-2.10',saved),e.saved());
  await page.clock.install({time:new Date(e.now())});await page.goto('http://studio-mock.invalid/');
  const click=s=>page.locator(s).filter({visible:true}).first().click(),tick=ms=>page.clock.runFor(ms);
  const read=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('aosedge-studio-mockup-2.10')).state);
  const body=()=>page.locator('.dw-dialog-copy').innerText();
  const fit=async()=>{const r=await page.evaluate(()=>{const d=document.querySelector('.dw-dialog'),p=document.querySelector('.dw-panel'),c=document.querySelector('.dw-dialog-copy');return {dialog:d.getBoundingClientRect().toJSON(),panel:p.getBoundingClientRect().toJSON(),overflow:c.scrollHeight-c.clientHeight}});assert.ok(r.dialog.top>=r.panel.top&&r.dialog.bottom<=r.panel.bottom+1&&r.overflow<=1,JSON.stringify(r));};
  assert.equal(await page.locator('[data-count=brake]').innerText(),'6');assert.equal(await page.locator('[data-count=tire]').innerText(),'6');
  for(const size of [{width:1728,height:1117},{width:1512,height:982},{width:1280,height:720}]){
   await page.setViewportSize(size);await settleLayout(page);await tick(100);
   for(const kind of ['brake','tire','cloud']){
    await click('[data-page="'+kind+'"]');await fit();
    assert.equal((await read()).view,'map');assert.equal(await page.locator('.dw-map').evaluate(el=>el.inert),true);
    const tabs=kind==='cloud'?['software','resources']:['records'];
    for(const tab of tabs){await click('[data-popup-tab="'+tab+'"]');await fit();}
    await page.keyboard.press('Escape');assert.equal(await page.locator('.dw-overlay').evaluate(el=>el.hidden),true);
    assert.equal(await page.evaluate(()=>document.activeElement.dataset.page),kind);
   }
  }
  await page.setViewportSize({width:1728,height:1117});await settleLayout(page);
  await click('[data-page=cloud]');await click('[data-popup-tab=software]');await click('.dw-dialog-copy [data-detail=brake]');
  assert.match(await body(),/6\.0\.0/);await click('[data-popup-return]');assert.equal(await page.locator('[data-popup-tab=software]').getAttribute('aria-pressed'),'true');
  await click('[data-action=close]');
  for(const k of ['brake','tire']){
   const peer=k==='brake'?'tire':'brake',before=await read();await click('[data-page="'+k+'"]');await click('[data-popup-tab=records]');
   assert.equal(await page.locator('[data-popup-record]').count(),4);await click('[data-popup-next]');assert.equal(await page.locator('[data-popup-record]').count(),2);
   const id=await page.locator('[data-popup-record]').first().getAttribute('data-popup-record');await click('[data-popup-record]');assert.match(await body(),new RegExp(id));await fit();
   await click('[data-popup-back]');assert.equal(await page.locator('[data-popup-record]').first().getAttribute('data-popup-record'),id);
   await click('[data-popup-tab=overview]');await click('[data-popup-reset]');await click('[data-popup-reset-cancel]');assert.equal((await read()).resets[k],null);
   await click('[data-popup-reset]');await click('[data-popup-reset-confirm]');await tick(700);assert.match(await body(),/waiting for Gateway CLEAR/);
   await tick(500);assert.match(await body(),/Reset confirmed/);assert.equal(await page.locator('[data-summary="'+k+'"]').innerText(),'Waiting for a new drive');
   const after=await read();assert.equal(after.resets[k].status,'CLEARED');assert.equal(after.records[k].length,6);assert.deepEqual(after.advisory[peer],before.advisory[peer]);
   assert.equal(await page.locator('[data-'+k+'-advisory]').innerText(),'Monitoring');await fit();
   if(process.env.MOCKUP_SCREENSHOT)await page.screenshot({path:process.env.MOCKUP_SCREENSHOT.replace('.png','-'+k+'-popup.png')});
   await page.keyboard.press('Escape');
  }
  await click('[data-action=drive]');await tick(3500);await click('[data-action=stop]');await tick(2500);
  for(const k of ['brake','tire']){assert.equal(await page.locator('[data-summary="'+k+'"]').innerText(),'Inspection recommended');assert.equal(await page.locator('[data-'+k+'-advisory]').innerText(),'Inspection recommended');}
  await click('[data-action=network]');await tick(6500);await click('[data-page=cloud]');assert.match(await body(),/Offline/);await click('[data-popup-tab=resources]');assert.match(await body(),/Last known/);await page.keyboard.press('Escape');
  await click('[data-page=brake]');assert.equal(await page.locator('[data-popup-reset]').isDisabled(),true);assert.match(await body(),/Reset confirmed/);await page.keyboard.press('Escape');
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
});

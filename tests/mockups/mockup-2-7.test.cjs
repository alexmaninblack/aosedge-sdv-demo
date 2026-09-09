// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Isolated mockup state-machine regression tests. No Cloud, VM or browser-profile access.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const mockupPath = path.join(__dirname, '../../docs/demo/mockups');
const source = fs.readFileSync(path.join(mockupPath, 'aosedge-demo-interaction-mockup-2-7.source.html'), 'utf8');
const logic = 'const copy=structuredClone;' + source.slice(source.indexOf('  const names ='), source.indexOf('  // Only mock state')) + source.slice(source.indexOf('  const fixture='), source.indexOf('  function renderNative()'));
test('Standalone contains the same reviewed state machine',()=>{const html=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-7.html'),'utf8');const section=s=>s.slice(s.indexOf('  const names ='),s.lastIndexOf('})();')+5);assert.equal(section(html),section(source));assert.match(html,/CPU · DMIPS/);assert.doesNotMatch(section(html),/data-cpu-bar/);});
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
function setup(e) {e.run("Object.assign(state,{created:true,running:true,provisioned:true,member:true,attached:true,unitId:'T',systemUid:'UID',backendContext:'UID',cloudOnline:true});state.backend={brake:true,tire:true};state.unit.vdp={kind:'vdp',profile:0,version:'0.0.0'};state.runtime.vdp='Running';observe();");return e;}
function release(e,k,n,v,installed=false){e.run(`(()=>{const c={kind:'${k}',profile:${n},version:'${v}',purpose:'test fixture',state:'Published'};state.candidates.${k}[${n}]=c;published[key(c)]={...c};${installed?`state.unit.${k}=fixture(c);state.runtime.${k}='Running';observe();`:''}})()`);}
function signed(e,k='vdp',n=1){e.run(`state.focus='${k}';state.picked.${k}=${n};allocate('${k}',${n});candidate('${k}',${n}).state='Signed';`);}
function publish(e,k='vdp',n=1){e.run(`operation('Publish '+names.${k},publishSteps('${k}',${n}));`);}
test('Manual at zero does not install; stationary Safe Stop does',()=>{const e=setup(env());release(e,'vdp',1,'16.0.0');e.run('pump()');e.advance(3000);assert.equal(e.value('state.unit.vdp.version'),'0.0.0');assert.equal(e.value('state.pending.vdp.phase'),'Ready');e.run("driveMode('safe_stop')");e.advance(1600);assert.equal(e.value('state.unit.vdp.version'),'16.0.0');assert.equal(e.value('state.pending.vdp'),null);assert.equal(e.value('state.cloud.runtime.vdp'),'Not reported');});
test('Safe Stop request while moving still waits for zero',()=>{const e=setup(env());release(e,'vdp',1,'16.0.0');e.run("state.speed=20;pump();driveMode('safe_stop')");e.advance(3000);assert.equal(e.value('state.unit.vdp.version'),'0.0.0');e.run('state.speed=0;pump()');e.advance(1600);assert.equal(e.value('state.unit.vdp.version'),'16.0.0');});
test('Publish before Provision may select a newer warehouse profile',()=>{const e=env();e.run("operation('Create vehicle',createSteps())");e.advance(1500);e.run('state.attached=true');release(e,'vdp',2,'17.0.0');assert.equal(e.value('lifecycleAction().kind'),'provision');e.run('doLifecycle()');e.advance(2500);assert.equal(e.value('state.pending.vdp.c.profile'),2);e.run("driveMode('safe_stop')");e.advance(1600);assert.equal(e.value('state.unit.vdp.profile'),2);assert.equal(e.value("Object.values(state.completed).some(c=>c.kind==='vdp'&&c.profile===1)"),false);});
test('First service Publish is unassigned; Deploy starts without FOTA gate',()=>{const e=setup(env());release(e,'brake',1,'4.0.0');e.run('pump()');e.advance(3000);assert.equal(e.value('state.unit.brake'),null);e.run("state.mode='autopilot';state.speed=20;operation('Deploy '+names.brake+' to Test',deploySteps('brake'))");e.advance(4000);assert.equal(e.value('state.runtime.brake'),'Running');release(e,'tire',1,'2.0.0');e.run("operation('Deploy '+names.tire+' to Test',deploySteps('tire'))");e.advance(4000);release(e,'brake',2,'5.0.0');e.run('pump()');e.advance(3000);assert.equal(e.value('state.unit.brake.version'),'5.0.0');assert.equal(e.value('state.unit.tire.version'),'2.0.0');assert.deepEqual(e.value('state.assigned'),{brake:true,tire:true});});
test('Full profile story terminates; older observed chapters do not re-open',()=>{const e=setup(env());for(const [k,n,v] of [['vdp',1,'16.0.0'],['brake',1,'4.0.0'],['vdp',2,'17.0.0'],['brake',2,'5.0.0'],['vdp',3,'18.0.0'],['brake',3,'6.0.0'],['tire',1,'2.0.0']]){release(e,k,n,v,true);if(k!=='vdp')e.run(`state.records.${k}.push({systemUid:'UID',serviceVersion:'${v}'})`);}assert.equal(e.value('nextStory()'),null);});
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
test('Provision while disconnected cannot claim Online; membership can resume',()=>{const e=setup(env());e.run("state.provisioned=false;state.unitId=null;state.member=false;state.external=false;operation('Provision Test',provisionSteps())");e.advance(1500);assert.equal(e.value('state.cloudOnline'),false);assert.equal(e.value('state.member'),false);e.run('state.external=true;doLifecycle()');e.advance(1500);assert.equal(e.value('state.cloudOnline'),true);assert.equal(e.value('state.member'),true);});
function product(e){release(e,'vdp',3,'18.0.0',true);release(e,'brake',3,'6.0.0',true);e.run('state.assigned.brake=true');}
test('Offline result, reconnect and reload retain exactly one delayed receipt',()=>{let e=setup(env());product(e);e.run("state.external=false;emitResult('brake')");e.advance(400);assert.ok(e.value('state.advisory.brake'));assert.equal(e.value('state.records.brake.length'),0);e=e.reload();e.run('toggleNetwork()');e.advance(1500);assert.equal(e.value('state.records.brake.length'),1);assert.equal(e.value('state.records.brake[0].delayed'),true);e=e.reload();e.advance(1500);assert.equal(e.value('state.records.brake.length'),1);});
test('Online outbox resumes after reload before backend receipt',()=>{let e=setup(env());product(e);e.run("emitResult('brake')");e.advance(300);e=e.reload();e.advance(1000);assert.equal(e.value('state.outbox.length'),0);assert.equal(e.value('state.records.brake.length'),1);});
test('Advisory lease expires without deleting backend history',()=>{const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);assert.ok(e.value('state.advisory.brake'));e.advance(31000);e.run('expireAdvisories()');assert.equal(e.value('state.advisory.brake'),null);assert.equal(e.value('state.records.brake.length'),1);});
test('Changed service profile, generation and restart clear live advisory',()=>{const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);release(e,'brake',1,'7.0.0',true);e.run('expireAdvisories()');assert.equal(e.value('state.advisory.brake'),null);product(e);e.run("emitResult('brake')");e.advance(1000);e.run('state.sourceGeneration++;expireAdvisories()');assert.equal(e.value('state.advisory.brake'),null);e.run("emitResult('brake')");e.advance(1000);e.run('park()');e.advance(1000);e.run('resume()');e.advance(1200);assert.equal(e.value('state.advisory.brake'),null);});
test('Retire clears owned run, preserving release catalog and numbering',()=>{const e=setup(env());product(e);e.run("emitResult('brake')");e.advance(1000);e.run('ledger.vdp=18;retire()');e.advance(8000);assert.equal(e.value('state.created'),false);assert.equal(e.value('state.unitId'),null);assert.deepEqual(e.value('state.records'),{brake:[],tire:[]});assert.equal(e.value('ledger.vdp'),18);assert.equal(e.value('Object.keys(published).length'),2);e.run('allocate("vdp",1)');assert.equal(e.value('candidate("vdp",1).version'),'19.0.0');});
test('Interrupted Retire resumes without losing next-cycle identity',()=>{let e=setup(env());e.run('retire()');e.advance(3150);e=e.reload();e.run('reconcile()');e.advance(8000);assert.equal(e.value('state.created'),false);assert.equal(e.value('state.cycle'),2);});
test('Separate deprovision/delete and fresh Create leave no old identity',()=>{const e=setup(env());e.run("operation('Deprovision Test',deprovisionSteps())");e.advance(3000);assert.equal(e.value('state.provisioned'),false);e.run("operation('Delete Unit',deleteSteps())");e.advance(1500);assert.equal(e.value('state.unitId'),null);assert.equal(e.value('state.running'),false);e.run('retire(true)');e.advance(8000);assert.equal(e.value('state.created'),true);assert.equal(e.value('state.unit.vdp.version'),'0.0.0');assert.equal(e.value('state.unitId'),null);});
test('Quick preparation ends in Manual with downloaded VDP, not auto Safe Stop',()=>{const e=env();e.run('quick()');e.advance(9000);assert.equal(e.value('state.member'),true);assert.equal(e.value('state.attached'),true);assert.equal(e.value('state.mode'),'manual');assert.equal(e.value('state.unit.vdp.version'),'0.0.0');assert.equal(e.value('state.pending.vdp.phase'),'Ready');});
test('Fresh Full story does not skip its publication because old Cloud releases remain',()=>{const e=setup(env());release(e,'vdp',3,'18.0.0',true);e.run('retire(true)');e.advance(9000);e.run('doLifecycle()');e.advance(1500);assert.equal(e.value('state.attached'),true);assert.equal(e.value('Object.keys(published).length'),1);assert.equal(e.value('lifecycleAction().kind'),'baseline');});

test('Browser: actual buttons, full VDP/Brake/Tire story, offline, Park and Retire', {skip:!process.env.MOCKUP_PLAYWRIGHT,timeout:90000}, async()=>{
  const {chromium}=require(process.env.MOCKUP_PLAYWRIGHT);
  const browser=await chromium.launch({executablePath:process.env.MOCKUP_CHROME,headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1512,height:982}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    const html=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-7.html'),'utf8');
    await page.route('**/*',route=>route.request().url().startsWith('http://studio-mock.invalid/')?route.fulfill({contentType:'text/html',body:html}):route.abort());
    await page.clock.install();await page.goto('http://studio-mock.invalid/');
    const tick=ms=>page.clock.runFor(ms),click=sel=>page.locator(sel).filter({visible:true}).first().click();
    const read=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('aosedge-studio-mockup-2.7')).state);
    for(const size of [{width:1728,height:1117},{width:1280,height:720}]){
      await page.setViewportSize(size);await tick(100);
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
    await page.setViewportSize({width:1512,height:982});await tick(100);
    await click('[data-workspace="tire"]');await page.getByRole('button',{name:'Details',exact:true}).click();
    assert.equal(await page.locator('.v27-detail-row').count(),7);
    assert.match(await page.locator('.dw-dialog-copy').innerText(),/No real artifact is generated/);
    await page.getByRole('button',{name:'Close',exact:true}).click();await click('[data-workspace="lifecycle"]');
    async function releaseUI(k,n){await click('[data-workspace="'+k+'"]');await click('[data-choose="'+n+'"]');for(const ms of [1000,600,1500]){await click('[data-action="primary"]');await tick(ms);}let s=await read();if(k!=='vdp'&&!s.assigned[k]){await click('[data-action="primary"]');await tick(4000);}}
    async function drive(){await click('[data-action="drive"]');await tick(3500);await click('[data-action="stop"]');await tick(2500);}
    await click('[data-guide]');await tick(1700);await click('[data-guide]');await tick(1500);
    await releaseUI('vdp',1);await click('[data-workspace="lifecycle"]');await click('[data-guide]');await tick(3000);await drive();
    for(const [k,n] of [['brake',1],['vdp',2],['brake',2],['vdp',3],['brake',3],['tire',1]]){await releaseUI(k,n);await drive();}
    let s=await read();assert.equal(s.unit.vdp.profile,3);assert.equal(s.unit.brake.profile,3);assert.equal(s.unit.tire.profile,1);assert.equal(s.runtime.brake,'Running');assert.equal(s.runtime.tire,'Running');assert.ok(s.records.brake.length>=3);assert.ok(s.records.tire.length>=1);
    await click('[data-workspace="lifecycle"]');await click('[data-page="cloud"]');assert.match(await page.locator('[data-cpu]').innerText(),/DMIPS/);
    await click('[data-action="network"]');await tick(1300);await drive();s=await read();assert.equal(s.cloudOnline,false);assert.ok(s.outbox.length);await click('[data-action="network"]');await tick(1500);assert.equal((await read()).outbox.length,0);
    await click('[data-action="operator"]');await click('[data-op="park"]');await tick(1300);assert.equal((await read()).parked,true);
    await click('[data-action="operator"]');await click('[data-op="resume"]');await tick(1300);assert.equal((await read()).unit.vdp.profile,3);
    await click('[data-action="operator"]');await click('[data-op="retire"]');await click('[data-action="confirm"]');await tick(8000);s=await read();assert.equal(s.created,false);assert.equal(s.unitId,null);assert.deepEqual(s.records,{brake:[],tire:[]});assert.deepEqual(errors,[]);
  } finally {await browser.close();}
});

test('2.7 retains every 2.6 flow script, with only isolated storage and the visible version label changed',()=>{
 const old=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-6.source.html'),'utf8');
 const scripts=s=>[...s.matchAll(/<script(?![^>]*data-visual-edition)[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
 const normalize=s=>s.replaceAll('aosedge-studio-mockup-2.7','aosedge-studio-mockup-2.6').replaceAll('MOCKUP 2.7','MOCKUP 2.6');
 assert.deepEqual(scripts(source).map(normalize),scripts(old));
});
test('2.7 retains the CARLA reference and the official logo unchanged',()=>{
 const old=fs.readFileSync(path.join(mockupPath,'aosedge-demo-interaction-mockup-2-6.source.html'),'utf8');
 const images=s=>[...s.matchAll(/<img\b[^>]*>/g)].map(m=>m[0]);
 assert.deepEqual(images(source),images(old));
});
test('2.7 visual adapter cannot issue actions, access Cloud or persist simulation state',()=>{
 const adapter=source.match(/<script data-visual-edition="2.7">([\s\S]*?)<\/script>/)[1];
 assert.doesNotMatch(adapter,/localStorage|sessionStorage|fetch\(|XMLHttpRequest|WebSocket|dispatchEvent|\.click\(|\.focus\(|\bstate\.[A-Za-z_$]/);
 assert.match(source,/<style data-visual-edition="2.7">/);
});

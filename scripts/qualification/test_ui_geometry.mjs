// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import test from 'node:test';
import {geometryChanges,presentationSnapshot,watchPresentation} from './ui_geometry.mjs';

const snapshot=()=>({view:'Vehicle',viewport:{width:876,height:908},visibility:'visible',dialogOpen:false,
 primary:'View progress',regions:{primary:{x:600,y:727,width:160,height:38},controller:{x:235,y:403,width:613,height:317}}});

test('same-label movement is measured; deliberate context, viewport and dialog changes are separate',()=>{
 const before=snapshot(),after=structuredClone(before);after.regions.primary.y-=100;
 assert.deepEqual(geometryChanges(before,after),[{region:'primary',x:0,y:-100,width:0,height:0}]);
 after.primary='Start controller';assert.deepEqual(geometryChanges(before,after),[]);
 for(const change of [{view:'Brake Team'},{visibility:'hidden'},{dialogOpen:true},{viewport:{width:640,height:850}}])
  assert.deepEqual(geometryChanges(before,{...after,...change}),[]);
});

test('DOM sample retains fixed freshness/visibility/reason fields, never arbitrary text or private identities',async()=>{
 const prior={document:globalThis.document,innerWidth:globalThis.innerWidth,innerHeight:globalThis.innerHeight};
 globalThis.innerWidth=876;globalThis.innerHeight=908;
 const raw='01234567-89ab-cdef-0123-456789abcdef';
 globalThis.document={visibilityState:'hidden',querySelector:selector=>selector==='[data-cloud-report]'
  ?{getAttribute:name=>name==='data-freshness'?'last-known':raw}
  :selector.includes('aria-pressed')?{getAttribute:()=> 'Vehicle'}
  :{textContent:raw,getBoundingClientRect:()=>({x:1.23,y:2,width:100,height:20})}};
 try {
  const value=await presentationSnapshot({evaluate:async(fn,args)=>fn(args)});
  assert.equal(value.reason,'OTHER_REASON');assert.equal(value.primary,null);assert.equal(value.visibility,'hidden');
  assert.equal(value.freshness,'last-known');assert(!JSON.stringify(value).includes(raw));
  assert.equal(value.regions.nav.x,1.2);
 } finally {Object.assign(globalThis,prior);}
});

test('watcher coalesces reads, bounds samples and awaits the owned read before closing',async()=>{
 let tick,resolve,cancelled=false,reads=0;const events=[];
 const page={evaluate:()=>{reads++;return new Promise(done=>{resolve=done;});}};
 const watcher=watchPresentation(page,event=>events.push(event),{limit:1,schedule:fn=>{tick=fn;return 1;},cancel:()=>{cancelled=true;}});
 tick();tick();assert.equal(reads,1);
 let finished=false;const closing=watcher.close().then(value=>{finished=true;return value;});
 await Promise.resolve();assert.equal(finished,false);assert.equal(cancelled,true);
 resolve(snapshot());const result=await closing;
 assert.equal(result.samples,1);assert.equal(result.errors,0);assert.equal(result.sampleLimitReached,true);
 tick();assert.equal(reads,1);assert.equal(events.length,1);
});

test('failed diagnostic write is counted without leaking exception text or stranding cleanup',async()=>{
 let tick;const watcher=watchPresentation({evaluate:async()=>snapshot()},()=>{throw new Error('PRIVATE_DETAIL');},
  {schedule:fn=>{tick=fn;return 1;},cancel:()=>{}});
 tick();const result=await watcher.close();assert.equal(result.errors,1);assert.equal(result.readOnly,true);
});

// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import test from 'node:test';
import { command, facts, installed, resetPreserved, visibleWorkspace } from './ui_journey.mjs';
const id='01234567-89ab-cdef-0123-456789abcdef';
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
test('release values come only from validated product receipts',()=>{
  assert.deepEqual(facts({version:null,release:null,serviceId:null,results:[{facts:{}}]}),{});
  assert.deepEqual(facts({results:[{facts:{version:'150.0.0',releaseHandle:'brake/150.0.0',serviceId:id}}]}),
    {version:'150.0.0',releaseHandle:'brake/150.0.0',serviceId:id});
  assert.equal(facts({results:[{facts:{command:{commandId:id}}}]}).commandId,id);
  for(const v of ['latest','../value','']) assert.throws(()=>facts({results:[{facts:{version:v}}]}));
});
test('VDP readiness keeps its full process and current release contract',()=>{
  const v={activeVersion:'150.0.0',vdpData:'REPORTED_READY',vdpRestarts:'0',processSlotMatches:true};
  assert.equal(installed(v,'platform','150.0.0'),true);
  for(const key of Object.keys(v)) assert.equal(installed({...v,[key]:null},'platform','150.0.0'),false);
  assert.equal(installed(v,'platform','151.0.0'),false);
});
test('service install checks real active instance and error status',()=>{
  const v={instances:[{version:'64.0.0',run_state:'active',error_message:false,error_exit_code:0}]};
  assert.equal(installed(v,'tire','64.0.0'),true);
  for(const [key,val] of [['version','63.0.0'],['run_state','failed'],['error_message',true],['error_exit_code',1]])
    assert.equal(installed({instances:[{...v.instances[0],[key]:val}]},'tire','64.0.0'),false);
});
test('reset confirmation binds command, peer model and retained history',()=>{
  const old={local:{teams:{brake:{model:'a'},tire:{model:'b'}}},brake:{productIds:['a']},tire:{productIds:['b']}};
  const after=structuredClone(old);after.brake={...after.brake,resetState:'CLEARED',resetId:id};
  assert.equal(resetPreserved(old,after,'brake',id),true);
  assert.equal(resetPreserved(old,after,'brake','other'),false);
  after.local.teams.tire.model='changed';assert.equal(resetPreserved(old,after,'brake',id),false);
  after.local.teams.tire.model='b';after.tire.productIds=[];assert.equal(resetPreserved(old,after,'brake',id),false);
});

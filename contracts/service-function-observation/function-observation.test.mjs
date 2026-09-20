// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: Apache-2.0
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {DatabaseSync} from 'node:sqlite';
import {FunctionObservationStore, functionObservationSchema, validateFunctionObservation, observationCanonical, observationDigest} from './function-observation.ts';

export function fixture(team = 'brake', sequence = 1, generation = 1) {
  const value = {schemaVersion:3,contractVersion:'3.0.0',messageType:team.toUpperCase()+'_FUNCTION_OBSERVATION',
    unitSystemUid:'test-unit',unitRole:'VALIDATION',serviceVersion:'60.0.0',serviceProfile:team === 'brake' ? 'v3' : 'v1',
    serviceInstance:{serviceId:team,subjectId:'subject',instanceIndex:0,instanceId:'instance'},generation,sequence,
    observedAt:'2026-09-18T20:00:00.000Z',content:{connection:'CONNECTED',input:{state:'RECEIVING',reason:'NONE'},
      activity:{state:'WAITING',reason:'NOT_QUALIFIED',episodeId:null},delivery:{state:'IDLE',queuedMessages:0,lastReceiptAt:null},
      advisory:{state:'WAITING',requestId:null},lastResult:null},contentSha256:''};
  return signed(value);
}
function signed(value) {value.contentSha256=observationDigest(observationCanonical(value.content));return value;}
function database() {const db=new DatabaseSync(':memory:');for(const sql of functionObservationSchema)db.exec(sql);return db;}
for (const team of ['brake','tire']) {
  test(team+': valid axes and waiting are independent of installed profile',()=>{
    const value=fixture(team);assert.doesNotThrow(()=>validateFunctionObservation(value,team));
    value.content.connection='REAUTHENTICATING';value.content.input={state:'WAITING',reason:'REAUTHENTICATING'};
    assert.doesNotThrow(()=>validateFunctionObservation(signed(value),team));
    assert.throws(()=>validateFunctionObservation(value,team==='brake'?'tire':'brake'));
  });
  for(const kind of ['extra','zero','fraction','overflow','date','profile','input','advisory','digest','legacy','instance'])test(team+': rejects '+kind,()=>{
    const value=fixture(team);
    if(kind==='extra')value.content.activeVdpProfile='v3';
    if(kind==='zero')value.generation=0;
    if(kind==='fraction')value.sequence=1.5;
    if(kind==='overflow')value.sequence=Number.MAX_SAFE_INTEGER+1;
    if(kind==='date')value.observedAt='2026-02-30T20:00:00.000Z';
    if(kind==='profile')value.serviceProfile=team==='brake'?'v4':'v3';
    if(kind==='input')value.content.input.state='DISCONNECTED';
    if(kind==='advisory')value.content.advisory.state='CONFIRMED';
    if(kind==='legacy')value.schemaVersion=2;
    if(kind==='instance')value.serviceInstance.instanceId='instance\n';
    signed(value);if(kind==='digest')value.contentSha256='0'.repeat(64);
    assert.throws(()=>validateFunctionObservation(value,team));
  });
  test(team+': late reports, generations, clock skew, duplicates and conflict',()=>{
    const db=database();try{
      const store=new FunctionObservationStore(db,team,()=> '2026-09-18T20:00:10.000Z');
      const recent=fixture(team,4,2), old=fixture(team,99,1);
      assert.equal(store.ingest(recent,'VALIDATION').status,201);
      const receipt=store.ingest(recent,'VALIDATION');assert.equal(receipt.status,200);
      store.ingest(old,'VALIDATION');store.ingest(fixture(team,3,2),'VALIDATION');
      assert.equal(store.query('test-unit').items[0].message.sequence,4);
      assert.equal(store.query('test-unit').items[0].stale,false);
      const reopened=new FunctionObservationStore(db,team,()=> '2026-09-18T20:02:00.000Z');
      assert.deepEqual(reopened.ingest(recent,'VALIDATION'),receipt);
      assert.equal(reopened.query('test-unit').items[0].stale,true);
      recent.observedAt='2026-09-18T20:00:01.000Z';
      assert.equal(store.ingest(recent,'VALIDATION').status,409);
      assert.equal(store.query('test-unit').items[0].deliveryState,'CONFLICT');
      const future=fixture(team,5,2);future.observedAt='2026-09-18T20:01:00.000Z';store.ingest(future,'VALIDATION');
      assert.equal(store.query('test-unit').items[0].clockSkew,true);
      assert.equal(store.query('test-unit').items[0].stale,true);
      assert.throws(()=>store.ingest(fixture(team),'PRODUCTION'));
    }finally{db.close();}
  });
}
test('profile limits: Brake V1/V2 have no advisory; V3 and Tire do',()=>{
  for(const profile of ['v1','v2']){const value=fixture();value.serviceProfile=profile;
    assert.throws(()=>validateFunctionObservation(value,'brake'));
    value.content.advisory.state='NOT_SUPPORTED';assert.doesNotThrow(()=>validateFunctionObservation(signed(value),'brake'));}
});
test('payload retention does not erase receipt/deduplication ledger',()=>{
  const db=database();try{
    const store=new FunctionObservationStore(db,'brake');const first=store.ingest(fixture(),'VALIDATION');
    for(let n=2;n<=1026;n++)store.ingest(fixture('brake',n),'VALIDATION');
    assert.equal(db.prepare('SELECT count(*) AS n FROM function_observations WHERE canonical IS NOT NULL').get().n,1024);
    const replay=store.ingest(fixture(),'VALIDATION');assert.equal(replay.status,200);assert.equal(replay.body.receiptId,first.body.receiptId);
    assert.equal(store.query('test-unit').items[0].message.sequence,1026);
  }finally{db.close();}
});
test('different native instances remain separate, no receipt-time winner',()=>{
  const db=database();try{
    const store=new FunctionObservationStore(db,'brake');store.ingest(fixture(),'VALIDATION');
    const peer=fixture();peer.serviceInstance.instanceId='peer';store.ingest(peer,'VALIDATION');
    assert.equal(store.query('test-unit').items.length,2);assert.equal(store.query('test-unit',1).truncated,true);
    assert.throws(()=>store.query('test-unit',101));
  }finally{db.close();}
});
test('transaction failure preserves an empty store',()=>{
  const db=database();try{
    db.exec("CREATE TRIGGER fail_insert BEFORE INSERT ON function_observations BEGIN SELECT RAISE(ABORT,'fixture'); END");
    const store=new FunctionObservationStore(db,'brake');assert.throws(()=>store.ingest(fixture(),'VALIDATION'));
    assert.equal(store.query('test-unit').items.length,0);
  }finally{db.close();}
});

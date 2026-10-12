// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import test from 'node:test';
import { PassThrough } from 'node:stream';
import fs from 'node:fs';
import { readBroker } from './ui_read_broker.mjs';

function fixture(t,timing=()=>{}) {
  const input=new PassThrough(),output=new PassThrough();
  const broker=readBroker(input,output,timing);t.after(()=>broker.close());
  let sent=[];output.on('data',b=>sent.push(JSON.parse(b.toString())));
  return {broker,input,output,sent};
}
test('all scenario owner reads are awaited and no synchronous child process is retained',()=>{
  const source=fs.readFileSync(new URL('./ui_journey.mjs',import.meta.url),'utf8');
  assert(!/(?<!await )\b(?:query|observed)\(/.test(source),'UNAWAITED_OWNER_READ');
  assert(!source.includes('execFileSync'),'SYNCHRONOUS_OWNER_PROCESS');
});
test('query waiting is asynchronous and each repeated query receives a fresh reply',async t=>{
  const {broker,input,sent}=fixture(t);let tick=false;
  const first=broker.request('query',{name:'local'});
  await new Promise(r=>setTimeout(()=>{tick=true;r();},10));assert(tick);
  const reply=Buffer.from(JSON.stringify({id:1,ok:true,value:{boot:'first'}})+'\n');
  input.write(reply.subarray(0,7));input.write(reply.subarray(7));
  assert.deepEqual(await first,{boot:'first'});
  const second=broker.request('query',{name:'local'});
  input.write(JSON.stringify({id:2,ok:true,value:{boot:'second'}})+'\n');
  assert.deepEqual(await second,{boot:'second'});assert.equal(sent.length,2);
});
test('concurrent queries are refused rather than sharing an old observation',async t=>{
  const {broker,input,sent}=fixture(t);const first=broker.request('query',{name:'local'});
  assert.throws(()=>broker.request('query',{name:'local'}),/NOT_IDLE/);assert.equal(sent.length,1);
  input.write('{"id":1,"ok":true,"value":{}}\n');await first;
});
test('wrong IDs, failed or malformed replies fail closed without another dispatch',async t=>{
  for(const reply of ['{"id":2,"ok":true,"value":{}}\n','{"id":1,"ok":false}\n','invalid\n']) {
    const {broker,input,sent}=fixture(t);const p=broker.request('observe',{label:'before'});
    input.write(reply);await assert.rejects(p,/BROKER/);
    assert.throws(()=>broker.request('query',{name:'local'}),/NOT_IDLE/);assert.equal(sent.length,1);
  }
});
test('oversized output and EOF cancel the sole outstanding read',async t=>{
  for(const kind of ['size','eof']) {
    const {broker,input,sent}=fixture(t);const p=broker.request('query',{name:'local'});
    if(kind==='size')input.write(Buffer.alloc(524289,65));else input.end();
    await assert.rejects(p,/TOO_LARGE|CLOSED/);assert.equal(sent.length,1);
  }
});
test('deadline and cancellation reject without replay and remove stream listeners',async t=>{
  const {broker,input,sent}=fixture(t);await assert.rejects(broker.request('query',{name:'local'},10),/TIMEOUT_NO_REPLAY/);
  assert.equal(sent.length,1);broker.close();assert.equal(input.listenerCount('data'),0);
  const other=fixture(t);const p=other.broker.request('query',{name:'local'});other.broker.close();
  await assert.rejects(p,/CANCELLED/);assert.equal(other.input.listenerCount('data'),0);
});
test('timing write failure rejects rather than stranding an unobserved result',async t=>{
  const {broker,input}=fixture(t,()=>{throw new Error('TIMING_WRITE_FAILED');});
  const p=broker.request('query',{name:'local'});input.write('{"id":1,"ok":true,"value":{}}\n');
  await assert.rejects(p,/TIMING_WRITE_FAILED/);
});

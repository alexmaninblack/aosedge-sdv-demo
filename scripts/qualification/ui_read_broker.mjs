// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';

export function readBroker(input=process.stdin,output=process.stdout,onTiming=()=>{}) {
  let sequence=0,pending=null,buffer=Buffer.alloc(0),closed=false;
  const fail=code=>{
    closed=true;buffer=Buffer.alloc(0);
    if(pending) {clearTimeout(pending.timer);pending.reject(new Error(code));pending=null;}
  };
  const data=chunk=>{
    if(closed)return;
    buffer=Buffer.concat([buffer,Buffer.from(chunk)]);
    const newline=buffer.indexOf(10);
    if(buffer.length>524288) {fail('UI_READ_BROKER_TOO_LARGE');return;}
    if(newline<0)return;
    const line=buffer.subarray(0,newline);buffer=buffer.subarray(newline+1);
    try {
      assert(pending && buffer.length===0,'UI_READ_BROKER_UNEXPECTED_REPLY');
      const reply=JSON.parse(line.toString('utf8'));
      assert(reply.id===pending.id && reply.ok===true,'UI_READ_BROKER_UNAVAILABLE');
      const current=pending;
      onTiming({kind:current.kind,seconds:+((performance.now()-current.started)/1000).toFixed(3)});
      pending=null;clearTimeout(current.timer);
      current.resolve(reply.value);
    } catch(error) {fail(/^[A-Z][A-Z0-9_]+$/.test(error.message)?error.message:'UI_READ_BROKER_INVALID_REPLY');}
  };
  const ended=()=>fail('UI_READ_BROKER_CLOSED');
  input.on('data',data);input.on('end',ended);input.on('error',ended);
  return {
    request(kind,args,budget=70000) {
      assert(!closed && !pending,'UI_READ_BROKER_NOT_IDLE');
      assert(['observe','query','native'].includes(kind) && args && typeof args==='object'
        && Number.isInteger(budget) && budget>0 && budget<=150000,'UI_READ_BROKER_REQUEST_INVALID');
      const id=++sequence;
      return new Promise((resolve,reject)=>{
        pending={id,kind,resolve,reject,started:performance.now(),timer:setTimeout(()=>fail('UI_READ_BROKER_TIMEOUT_NO_REPLAY'),budget)};
        output.write(JSON.stringify({uiRead:true,id,kind,args})+'\n');
      });
    },
    close() {
      fail('UI_READ_BROKER_CANCELLED');
      input.off('data',data);input.off('end',ended);input.off('error',ended);
      input.pause();
    }
  };
}

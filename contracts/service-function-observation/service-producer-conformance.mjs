// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Consume only synthetic --emit-conformance output from the real C++ producer tests.
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {DatabaseSync} from "node:sqlite";
import {validateFunctionObservation,observationCanonical,FunctionObservationStore,functionObservationSchema} from "./function-observation.ts";
const team=process.argv[2];
assert.ok(team==="brake"||team==="tire");
const lines=readFileSync(0,"utf8").trim().split("\n");assert.ok(lines.length>0);
const db=new DatabaseSync(":memory:");
try {
 for(const sql of functionObservationSchema)db.exec(sql);
 const store=new FunctionObservationStore(db,team,()=>"2026-09-18T12:00:10.000Z");
 const profiles=new Set();
 for(const line of lines){
  const input=JSON.parse(line),parsed=validateFunctionObservation(input,team);
  assert.equal(parsed.canonical,line);assert.equal(observationCanonical(input),line);
  profiles.add(input.serviceProfile);
  const first=store.ingest(input,"VALIDATION"),retry=store.ingest(input,"VALIDATION");
  assert.equal(first.status,201);assert.equal(retry.status,200);
  assert.equal(first.body.receiptId,retry.body.receiptId);assert.equal(first.body.messageKeySha256,parsed.key);
  const head=store.query(input.unitSystemUid).items.find(item=>item.message.serviceInstance.instanceId===input.serviceInstance.instanceId);
  assert.equal(head.message.sequence,input.sequence);
 }
 assert.deepEqual([...profiles].sort(),team==="brake"?["v1","v2","v3"]:["v1"]);
 console.log("PASS "+team+" real C++ canonical payloads, all profiles, reference decoding, SQLite receipts, exact retry and source ordering");
}finally{db.close();}

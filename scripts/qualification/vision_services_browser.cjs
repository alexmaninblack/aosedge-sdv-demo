// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
"use strict";
const fs=require("node:fs"),path=require("node:path"),readline=require("node:readline"),assert=require("node:assert/strict");
const c=JSON.parse(process.argv[2]);
const {chromium}=require(path.join(c.runtime,"playwright-core"));
const profile=path.join(c.records,"browser-profile");
let context,page,latest,baseline,beforeReference,errors=[];
const emit=(phase,data)=>process.stdout.write(JSON.stringify({phase,data})+"\n");
const uuid=/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}/i;
async function close(){if(context){const owned=context;context=null;await owned.close();}}
process.on("SIGTERM",()=>close().finally(()=>process.exit(1)));
async function waitState(state){await page.waitForFunction(wanted=>document.getElementById("state").textContent===wanted,state,{timeout:15000});}
async function rectangles(){return page.evaluate(()=>Object.fromEntries(["tab-overview","state","age","path-plot","lead","plan"].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return[id,[r.x,r.y,r.width,r.height].map(n=>Math.round(n*10)/10)];})));}
async function screenshot(name){
 assert(!uuid.test(await page.content()),"FULL_IDENTIFIER_IN_BROWSER");
 assert.equal(errors.length,0,"BROWSER_SCRIPT_ERROR");
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),"HORIZONTAL_OVERFLOW");
 await page.screenshot({path:path.join(c.records,name+".png"),fullPage:true});
}
async function command(op){
 if(op==="BASELINE"){
  await waitState("AVAILABLE");beforeReference=latest.vision.reference;
  assert.equal(latest.vision.perceptionVersion,"0.1.1");assert.equal(latest.vision.assessmentVersion,"0.1.1");
  baseline=await rectangles();await screenshot("01-overview-available");
  await page.getByRole("tab",{name:"Perception",exact:true}).click();
  for(const name of ["AutoSteer","AutoSpeed","AutoDrive"])assert(await page.getByRole("heading",{name,exact:true}).isVisible());
  await screenshot("02-perception");
  await page.getByRole("tab",{name:"Assessment",exact:true}).click();await screenshot("03-assessment");
  await page.getByRole("tab",{name:"Overview",exact:true}).click();
  const first=latest.vision.reference;const deadline=Date.now()+10000;
  while(latest.vision.reference===first&&Date.now()<deadline)await page.waitForTimeout(100);
  assert.notEqual(latest.vision.reference,first,"NO_ADVANCING_NATIVE_RESULT");
  assert.deepEqual(await rectangles(),baseline,"LAYOUT_CHANGED_DURING_LIVE_RESULTS");
  return {tabs:3,headed:true,versionsVerified:true,opaqueReferenceOnly:true,layoutStableAcrossResults:true,screenshotCount:3};
 }
 if(op==="UNAVAILABLE"){
  await waitState("UNAVAILABLE");
  assert.equal(await page.locator("#lead").textContent(),"Unavailable");
  assert.equal(await page.locator("#plan").textContent(),"Unavailable");
  assert.equal(await page.locator("#path-line").getAttribute("points"),"");
  assert.deepEqual(await rectangles(),baseline,"LAYOUT_CHANGED_ON_INPUT_LOSS");
  await screenshot("04-input-unavailable");return {previousValidResultsCleared:true,layoutStable:true};
 }
 if(op==="RECOVERED"){
  await waitState("AVAILABLE");assert.notEqual(latest.vision.reference,beforeReference,"OLD_RESULT_REUSED_AFTER_RECOVERY");
  assert.deepEqual(await rectangles(),baseline,"LAYOUT_CHANGED_AFTER_RECOVERY");
  await screenshot("05-input-recovered");return {freshNativeReference:true,layoutStable:true,shadowOnly:latest.vision.shadowOnly,imageMatched:latest.vision.imageMatched};
 }
 throw Error("UNKNOWN_UI_COMMAND");
}
(async()=>{
 try{
  fs.mkdirSync(profile,{mode:0o700});
  context=await chromium.launchPersistentContext(profile,{headless:false,chromiumSandbox:true,executablePath:c.executable,
   viewport:{width:1440,height:900},locale:"en-US",colorScheme:"light",reducedMotion:"reduce",permissions:[],
   args:["--window-size=1460,980","--window-position=540,70"]});
  await context.route("**/*",route=>new URL(route.request().url()).origin==="http://127.0.0.1:18080"?route.continue():route.abort());
  page=context.pages()[0]||await context.newPage();page.on("pageerror",e=>errors.push(e.name));
  page.on("response",async response=>{if(response.url()==="http://127.0.0.1:18080/api/presenter/snapshot"&&response.ok()){
   const raw=await response.body();assert(raw.length<=4096);assert(!uuid.test(raw.toString()));const value=JSON.parse(raw);assert.equal(value.profile,"vision");latest=value;
  }});
  await page.goto("http://127.0.0.1:18080/",{waitUntil:"domcontentloaded",timeout:15000});emit("READY",{headed:true,sandboxEnabled:true});
  const input=readline.createInterface({input:process.stdin});
  for await(const line of input){
   if(line==="STOP"){await close();input.close();process.stdin.destroy();emit("CLOSED",{browserClosed:true});return;}
   emit(line,await command(line));
  }
 }catch(error){emit("ERROR",{code:error.code||error.name,message:String(error.message).slice(0,200)});process.exitCode=1;}
 finally{await close();}
})();

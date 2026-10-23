// SPDX-FileCopyrightText: 2026 maninblack
// SPDX-License-Identifier: MIT
// Bounded, read-only DOM observation. No product callbacks, inputs or state authority.
const selectors={nav:'.studio-nav',guide:'.studio-guide',primary:'.studio-guide>button',
  footer:'.studio-footer',backends:'.studio-backends',controller:'.studio-controller'};

export async function presentationSnapshot(page) {
  return page.evaluate(selectors=>{
    const regions={};
    for(const [key,selector] of Object.entries(selectors)) {
      const element=document.querySelector(selector),r=element?.getBoundingClientRect();
      if(r?.width && r?.height) regions[key]={x:+r.x.toFixed(1),y:+r.y.toFixed(1),width:+r.width.toFixed(1),height:+r.height.toFixed(1)};
    }
    const connection=document.querySelector('.studio-connection');
    const reason=connection?.getAttribute('data-observation-reason');
    const knownReasons=['OBSERVER_HIDDEN','ACTION_COMPLETED_REFRESH_REQUIRED','CLOUD_READ_SLOW','AOS_CLOUD_STATE_UNAVAILABLE'];
    const text=document.querySelector(selectors.primary)?.textContent?.trim()??'';
    const primary=/^(View progress|Refresh (Cloud state|state)|Start (controller|simulator)|Connect in Manual|Open (Platform|Brake|Tire)( v[123]| backend|)|Select v[123]|Stop demo and keep data|Create controller|Continue preparation|Provision to Test|Continue registration|Open update details|Delete Test & start over|Continue Test deletion)$/.test(text)?text:null;
    const view=document.querySelector('.studio-nav button[aria-pressed=true]')?.getAttribute('aria-label');
    const freshness=connection?.getAttribute('data-freshness');
    return {view:['Vehicle','Platform Team','Brake Team','Tire Team'].includes(view)?view:null,
      viewport:{width:innerWidth,height:innerHeight},visibility:document.visibilityState==='visible'?'visible':'hidden',
      freshness:['current','last-known','unconfirmed'].includes(freshness)?freshness:null,
      reason:knownReasons.includes(reason)?reason:reason?'OTHER_REASON':null,
      dialogOpen:Boolean(document.querySelector('[role=dialog]')),primary,regions};
  },selectors);
}

export function geometryChanges(before,after) {
  if(!before || before.view!==after.view || before.dialogOpen || after.dialogOpen
      || before.visibility!=='visible' || after.visibility!=='visible'
      || JSON.stringify(before.viewport)!==JSON.stringify(after.viewport))return [];
  return Object.entries(after.regions).flatMap(([region,rect])=>{
    const old=before.regions[region];
    if(!old || region==='primary' && before.primary!==after.primary)return [];
    const delta=Object.fromEntries(['x','y','width','height'].map(key=>[key,+(rect[key]-old[key]).toFixed(1)]));
    return Math.max(...Object.values(delta).map(Math.abs))>1?[{region,...delta}]:[];
  });
}

export function watchPresentation(page,emit,{interval=500,limit=7200,schedule=setInterval,cancel=clearInterval}={}) {
  let closed=false,busy=false,flight=null,last=null,samples=0,errors=0,movements=0;
  async function sample() {
    if(closed || busy || samples>=limit)return;
    busy=true;
    try {
      const value=await presentationSnapshot(page),changes=geometryChanges(last,value);
      samples++;movements+=changes.length;
      emit({state:'UI_PRESENTATION_SAMPLE',...value,changes});last=value;
    } catch {errors++;try {emit({state:'UI_PRESENTATION_SAMPLE_UNAVAILABLE'});} catch { /* Count evidence I/O failure too; never leak the exception. */ }}
    finally {busy=false;}
  }
  const timer=schedule(()=>{if(!busy && !closed)flight=sample();},interval);
  return {close:async()=>{closed=true;cancel(timer);await flight;
    return {samples,errors,movements,sampleLimitReached:samples>=limit,readOnly:true};}};
}

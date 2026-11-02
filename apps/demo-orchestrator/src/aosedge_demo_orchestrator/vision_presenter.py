# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only Vision view of the existing bounded Source observation.

No inference owner, camera stream, lifecycle operation or additional API. The
ordinary Presenter snapshot route and loopback protections remain in force.
"""
from pathlib import Path
from . import vision_observation
from .environment import JOURNAL
from .status import read_json,now


class VisionReader:
    def __init__(self,source):
        from .vision_bootstrap import INSTANCE_NAME,VM_PROFILE
        self.source=source;self.root=source.root
        state=read_json(self.root/JOURNAL)
        if self.root.name!=INSTANCE_NAME or state.get('vmProfile')!=VM_PROFILE:
            raise ValueError('VISION_PRESENTER_TARGET_REQUIRED')

    def __call__(self):
        state=read_json(self.root/JOURNAL);view=vision_observation.unavailable()
        source=state.get('source') or {};runtime=state['vehicles']['test'].get('runtime') or {}
        if source.get('state')=='RUNNING' and runtime.get('state')=='RUNNING':
            try:view=vision_observation.observation(self.source.observe(guest=False,timeout=5).get('vision'))
            except (OSError,ValueError):pass
        return dict(profile='vision',observedAt=now(),vision=view,
            controller=dict(state='RUNNING' if runtime.get('state')=='RUNNING' else 'STOPPED'),
            source=dict(state='RUNNING' if source.get('state')=='RUNNING' else 'STOPPED'))


def assets(root):
    """Materialize signed constant assets into a new scenario-owned directory."""
    root=Path(root);root.mkdir(mode=0o700)
    (root/'assets').mkdir(mode=0o700)
    for name,text in (('index.html',HTML),('assets/vision.css',CSS),('assets/vision.js',JS)):
        with (root/name).open('x') as stream:stream.write(text)
    return root


HTML='''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SDV Lab — Vision</title>
<link rel="stylesheet" href="/assets/vision.css"><script defer src="/assets/vision.js"></script></head>
<body><header><div><p class="eyebrow">AosEdge SDV Lab</p><h1>Vision Pilot</h1></div>
<div class="badge">SHADOW ONLY · NO VEHICLE CONTROL</div></header>
<nav role="tablist" aria-label="Vision views"><button role="tab" aria-selected="true" aria-controls="overview" id="tab-overview">Overview</button>
<button role="tab" aria-selected="false" aria-controls="perception" id="tab-perception">Perception</button>
<button role="tab" aria-selected="false" aria-controls="assessment" id="tab-assessment">Assessment</button></nav>
<main><section class="status-row" aria-label="Live status"><article><span>Vision controller</span><strong id="controller">Waiting</strong></article>
<article><span>Camera source</span><strong id="source">Waiting</strong></article><article><span>Analysis</span><strong id="state" role="status">Waiting</strong></article>
<article><span>Capture → observation</span><strong id="age">—</strong></article></section>
<p class="notice" id="reason">Waiting for a live Source observation.</p>
<section id="overview" role="tabpanel" aria-labelledby="tab-overview"><div class="grid">
<article class="card plot-card"><h2>Interpreted road path</h2><p>Ground-plane result, not an overlay on the live camera.</p>
<svg id="path-plot" viewBox="0 0 560 320" role="img" aria-label="Interpreted path in vehicle coordinates">
<path class="axis" d="M280 285V25 M40 285H520"/><text x="288" y="28">forward (m)</text><text x="40" y="308">left ← lateral (m) → right</text>
<polyline id="path-line" points=""/><text id="path-empty" x="155" y="155">No valid path to display</text></svg>
<div class="metrics"><span>Analyzed frame <b id="frame">—</b></span><span>Live camera frame <b id="camera-frame">—</b></span></div>
<p id="association">No image association.</p></article>
<div class="stack"><article class="card"><h2>Lead vehicle</h2><strong class="result" id="lead">Unavailable</strong><p id="lead-detail">No valid observation.</p></article>
<article class="card"><h2>Shadow plan</h2><strong class="result" id="plan">Unavailable</strong><p id="plan-detail">Requires valid perception, dynamics and a trusted vehicle profile.</p></article></div></div></section>
<section id="perception" role="tabpanel" aria-labelledby="tab-perception" hidden><article class="card wide"><h2>Perception service <span id="perception-version">—</span></h2>
<p>Three FP32 models run in one native Aos container, using only its assigned Camera Access resource.</p>
<div class="model-grid"><article><h3>AutoSteer</h3><p>Lane / road-path evidence</p></article><article><h3>AutoSpeed</h3><p>Object detections</p></article><article><h3>AutoDrive</h3><p>Temporal lead / path evidence</p></article></div>
<p>These are model roles, not three separately deployable services. Raw model tensors and full capture identifiers stay server-side. See Overview for the actual interpreted result.</p></article></section>
<section id="assessment" role="tabpanel" aria-labelledby="tab-assessment" hidden><article class="card wide"><h2>Assessment service <span id="assessment-version">—</span></h2>
<p>Fuses Perception with frame-bound context. Results are display-only: no steering, throttle, brake or advisory writer.</p>
<dl><dt>Result validity</dt><dd id="assessment-state">Unavailable</dd><dt>Path convention</dt><dd>Forward metres; left-positive lateral metres</dd><dt>Missing inputs</dt><dd>Withhold the affected output; never reuse an old valid plan</dd><dt>Image matching</dt><dd>Only the original analyzed frame can carry its result overlay</dd></dl></article></section>
</main><footer>Engineering Vision profile · Read-only · Performance, accuracy and safety qualification are separate gates.</footer></body></html>'''

CSS='''*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#172c45;font:16px system-ui,sans-serif}header,nav,main,footer{max-width:1240px;margin:auto}header{height:122px;display:flex;align-items:center;justify-content:space-between;padding:22px 24px}h1{font-size:30px;margin:0}.eyebrow{font-size:13px;letter-spacing:.12em;margin:0 0 5px;color:#53708c}.badge{border:1px solid #c1d2df;border-radius:20px;padding:10px 16px;font-size:12px;font-weight:700}nav{display:flex;gap:8px;padding:0 24px;height:54px;border-bottom:1px solid #ced9e4}button{font:inherit;border:0;background:transparent;color:#425e78;padding:0 22px;cursor:pointer;border-bottom:3px solid transparent}button[aria-selected=true]{border-color:#1476b8;color:#075789;font-weight:700}button:focus-visible{outline:3px solid #f1b13d}main{padding:24px;min-height:660px}.status-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.status-row article{background:white;border:1px solid #d9e1ea;border-radius:10px;padding:16px;min-height:87px}.status-row span{display:block;color:#5a7186;font-size:13px}.status-row strong{display:block;padding-top:8px;font-size:18px;font-variant-numeric:tabular-nums}.notice{min-height:44px;padding:12px 0;color:#4c6174;font-size:14px;margin:0}.grid{display:grid;grid-template-columns:1.7fr 1fr;gap:18px}.card{border:1px solid #d9e1ea;border-radius:12px;background:#fff;padding:22px}.card h2{font-size:20px;margin:0 0 8px}.card p{color:#566c80;font-size:14px;line-height:1.5;margin:6px 0 12px}.plot-card{height:445px}.stack{display:grid;grid-template-rows:1fr 1fr;gap:18px}.result{display:block;font-size:23px;margin:14px 0;min-height:31px}.wide{height:445px}.model-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:32px 0}.model-grid article{background:#f2f6fb;padding:22px;border-radius:8px;min-height:130px}.model-grid h3{margin:0 0 10px}svg{display:block;height:260px;width:100%;background:#f8fafc;border-radius:8px}svg text{font-size:13px;fill:#5d7386}.axis{stroke:#c9d6e3;stroke-width:1;fill:none}#path-line{stroke:#138b9a;stroke-width:4;fill:none}.metrics{display:flex;justify-content:space-between;margin-top:10px;font-size:13px;gap:20px}.metrics b{display:inline-block;min-width:65px;font-variant-numeric:tabular-nums}#association{height:22px}dl{display:grid;grid-template-columns:180px 1fr;gap:20px;margin-top:30px}dt{font-weight:700}dd{margin:0}footer{font-size:12px;color:#667c91;padding:16px 24px 24px}[hidden]{display:none!important}@media(max-width:800px){.badge{max-width:190px}.status-row{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.wide{height:auto;min-height:445px}.model-grid{grid-template-columns:1fr}.plot-card{height:auto}header{height:140px}}'''

JS='''"use strict";
const byId=id=>document.getElementById(id), text=(id,value)=>{byId(id).textContent=value;};
const empty=()=>({state:"UNAVAILABLE",reason:"WAITING_FOR_ANALYSIS",frame:null,cameraFrame:null,captureAgeMs:null,perceptionVersion:null,assessmentVersion:null,lead:null,path:null,plan:null,imageMatched:false});
let lastSuccess=0;
function render(snapshot){
 const v=snapshot.vision||empty();
 text("controller",snapshot.controller?.state||"Unavailable");text("source",snapshot.source?.state||"Unavailable");
 text("state",v.state);text("age",v.captureAgeMs===null?"—":`${Math.round(v.captureAgeMs)} ms`);
 text("reason",v.reason.split("_").join(" "));
 text("frame",v.frame??"—");text("camera-frame",v.cameraFrame??"—");
 text("perception-version",v.perceptionVersion?`v${v.perceptionVersion}`:"—");text("assessment-version",v.assessmentVersion?`v${v.assessmentVersion}`:"—");text("assessment-state",v.state);
 const valid=v.state==="AVAILABLE";
 text("lead",!valid||!v.lead?.valid?"Unavailable":v.lead.present?`${v.lead.distanceMetres.toFixed(1)} m`:"No lead vehicle detected");
 text("lead-detail",valid&&v.lead?.valid?(v.lead.present?"Valid interpreted observation.":"Valid absence; no fabricated distance."):"No valid observation.");
 text("plan",valid&&v.plan?.valid?"Valid shadow prediction":"Unavailable");
 text("plan-detail",valid&&v.plan?.valid?`Acceleration ${v.plan.accelerationMps2.toFixed(2)} m/s² · Steering ${v.plan.firstSteeringRadians.toFixed(3)} rad · Display only.`:"Required planning inputs are not valid. No control command is sent.");
 const path=valid&&v.path?.valid?v.path.points:[];
 byId("path-line").setAttribute("points",path.map(p=>`${Math.max(40,Math.min(520,280-p[1]*8))},${Math.max(25,Math.min(285,285-p[0]*2))}`).join(" "));
 byId("path-empty").hidden=path.length>0;byId("path-empty").style.display=path.length?"none":"";
 text("association",v.frame===null?"No image association.":v.imageMatched?"Frame identities match. This view remains a separate ground plot.":"Newer live image — result belongs to its original analyzed frame.");
}
document.querySelectorAll('[role="tab"]').forEach(button=>button.addEventListener("click",()=>{
 document.querySelectorAll('[role="tab"]').forEach(tab=>{const selected=tab===button;tab.setAttribute("aria-selected",String(selected));byId(tab.getAttribute("aria-controls")).hidden=!selected;});
}));
async function poll(){try{const response=await fetch("/api/presenter/snapshot",{cache:"no-store"});if(!response.ok)throw Error("Observation unavailable");const snapshot=await response.json();if(snapshot.profile!=="vision")throw Error("Wrong profile");lastSuccess=performance.now();render(snapshot);}catch{render({vision:empty()});text("reason","Live observation unavailable — previous valid results cleared.");}finally{setTimeout(poll,200);}}
setInterval(()=>{if(lastSuccess&&performance.now()-lastSuccess>1200){render({vision:empty()});text("reason","Observation connection lost — previous valid results cleared.");}},200);
poll();
'''

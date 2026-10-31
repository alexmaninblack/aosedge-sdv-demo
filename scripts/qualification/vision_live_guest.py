# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Engineering-only live CPU inference. No CARLA client or actuation interface.

Pre/postprocessing parity references pinned upstream inference.cpp,
auto_drive.cpp, auto_speed.cpp and visualization/debug_display.cpp.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from vision_live_contract import read_packet,require,jpeg_dimensions
from vision_model_probe import valid_input_shapes
STAGE='preflight'
FACTS={}


def main():
    global STAGE
    p=argparse.ArgumentParser();p.add_argument('--payload',type=Path,required=True)
    p.add_argument('--session',required=True);p.add_argument('--source',required=True)
    p.add_argument('--calibration',type=Path,required=True);a=p.parse_args()
    require(os.uname().machine=='aarch64' and sys.platform=='linux' and len(os.sched_getaffinity(0))==4,'VISION_GUEST_REQUIRED')
    root=a.payload;lock=json.loads((root/'input-lock.json').read_bytes())
    require(lock['upstream']=='e7e5c614832f175f1f9f10a0d0c0df2559ff2c38','MODEL_PIN_CHANGED')
    for row in lock['files']:
        relative=Path(row['path']);require(not relative.is_absolute() and '..' not in relative.parts,'PAYLOAD_PATH_INVALID')
        f=root/relative;require(not f.is_symlink() and f.stat().st_size==row['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256'],'PAYLOAD_CHANGED')
    sys.path.insert(0,str(root/'libraries'))
    import numpy as np
    import cv2
    import onnxruntime as ort
    require((np.__version__,cv2.__version__,ort.__version__)==('2.4.4','4.13.0','1.26.0'),'LIBRARY_PIN_CHANGED')
    cv2.setNumThreads(1);cal=json.loads(a.calibration.read_bytes())
    require(cal['profile']=='carla-forward-720p-fov50-v1','CALIBRATION_PROFILE_INVALID')
    warp=np.asarray(cal['rawToModel'],dtype=np.float64)
    require(warp.shape==(3,3) and np.isfinite(warp).all(),'CALIBRATION_INVALID')
    sessions={};names={}
    for name in ('autodrive','autosteer','autospeed'):
        options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
        options.graph_optimization_level=ort.GraphOptimizationLevel.ORT_DISABLE_ALL;options.log_severity_level=3
        options.add_session_config_entry('session.intra_op.allow_spinning','0')
        session=ort.InferenceSession(str(root/'models'/f'{name}_fp32.onnx'),options,providers=['CPUExecutionProvider'])
        require(session.get_providers()==['CPUExecutionProvider'] and len(session.get_inputs())==(2 if name=='autodrive' else 1)
                and valid_input_shapes(session.get_inputs()),'MODEL_CONTRACT_CHANGED')
        sessions[name]=session;names[name]=[v.name for v in session.get_inputs()]
    def emit(value):
        text=json.dumps(value,separators=(',',':'),allow_nan=False)
        require(len(text.encode())<=65536,'RESULT_LIMIT');print(text,flush=True)
    emit(dict(state='READY',session=a.session,source=a.source,calibration=cal['id'],provider='CPUExecutionProvider'))
    mean=np.asarray([.485,.456,.406],np.float32).reshape(1,3,1,1)
    std=np.asarray([.229,.224,.225],np.float32).reshape(1,3,1,1)
    def chw(image,normalize=False):
        value=np.ascontiguousarray((image[:,:,::-1].astype(np.float32)/np.float32(255)).transpose(2,0,1)[None])
        return np.ascontiguousarray((value-mean)/std) if normalize else value
    def infer(name,data):
        started=time.perf_counter();options=ort.RunOptions();options.add_run_config_entry('memory.enable_memory_arena_shrinkage','cpu:0')
        out=sessions[name].run(None,dict(zip(names[name],data)),options)
        require(all(np.isfinite(v).all() for v in out),'NONFINITE_OUTPUT')
        return out,(time.perf_counter()-started)*1000
    last=-1;count=0
    with ThreadPoolExecutor(max_workers=3) as pool:
        while True:
            STAGE='frame-input'
            packet=read_packet(sys.stdin.buffer,a.session,a.source,cal['id'],last)
            if packet is None:break
            meta,images,pair_valid=packet;started=time.perf_counter()
            STAGE='jpeg-header'
            for v in images:jpeg_dimensions(v)
            STAGE='jpeg-decode'
            decoded=[cv2.imdecode(np.frombuffer(v,np.uint8),cv2.IMREAD_COLOR) for v in images]
            require(all(v is not None and v.shape==(720,1280,3) for v in decoded),'CAMERA_DIMENSIONS_INVALID')
            resized=cv2.resize(decoded[1][80:],(1024,512),interpolation=cv2.INTER_LINEAR);plain=chw(resized)
            futures={n:pool.submit(infer,n,[plain]) for n in ('autosteer','autospeed')}
            if pair_valid:
                tensors=[chw(cv2.warpPerspective(v,warp,(1024,512),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101),True) for v in decoded]
                futures['autodrive']=pool.submit(infer,'autodrive',tensors)
            values={n:f.result() for n,f in futures.items()}
            STAGE='output-decode'
            FACTS['shapes']={n:[list(v.shape) for v in row[0]] for n,row in values.items()}
            path,confidence=values['autosteer'][0]
            require(path.shape==confidence.shape==(1,1,64,1),'AUTOSTEER_SHAPE_CHANGED')
            waypoints=[[float(x)*1024,i*511/63] for i,(x,h) in enumerate(zip(path.ravel(),confidence.ravel())) if h>=.5 and 0<=x<=1]
            raw=values['autospeed'][0][0];require(raw.shape==(1,8,10752),'AUTOSPEED_SHAPE_CHANGED')
            data=raw[0];scores=1/(1+np.exp(-np.clip(data[4:],-80,80)))
            classes=scores.argmax(axis=0);score=scores.max(axis=0);indices=np.flatnonzero(score>=.6)
            # Upstream class-agnostic NMS, fixed confidence/IoU; bound retained DTO.
            indices=indices[np.argsort(score[indices])[::-1]];boxes=[]
            while len(indices) and len(boxes)<128:
                i=int(indices[0]);cx,cy,w,h=map(float,data[:4,i]);box=[cx-w/2,cy-h/2,cx+w/2,cy+h/2]
                if w>0 and h>0:boxes.append(dict(box=box,score=float(score[i]),level=int(classes[i])))
                rest=indices[1:]
                if not len(rest):break
                x1=data[0,rest]-data[2,rest]/2;y1=data[1,rest]-data[3,rest]/2
                x2=data[0,rest]+data[2,rest]/2;y2=data[1,rest]+data[3,rest]/2
                intersection=np.maximum(0,np.minimum(box[2],x2)-np.maximum(box[0],x1))*np.maximum(0,np.minimum(box[3],y2)-np.maximum(box[1],y1))
                union=max(w*h,0)+np.maximum(0,data[2,rest])*np.maximum(0,data[3,rest])-intersection+1e-6
                indices=rest[intersection/union<=.45]
            lead=dict(valid=False,reason='PAIR_CADENCE_INVALID',probability=None,distanceEstimateMetres=None,curvatureRaw=None)
            if pair_valid:
                outputs=values['autodrive'][0];require([v.shape for v in outputs]==[(1,1)]*3,'AUTODRIVE_SHAPE_CHANGED')
                distance,curve,logit=(float(v.ravel()[0]) for v in outputs)
                probability=float(1/(1+np.exp(-np.clip(logit,-80,80))))
                lead=dict(valid=True,probability=probability,distanceNormalized=distance,
                    distanceEstimateMetres=150*(1-distance) if probability>=.4 and 0<=distance<=1 else None,curvatureRaw=curve)
            last=meta['frames'][1]['frame'];count+=1;require(count<=1800,'LIVE_RESULT_COUNT_LIMIT')
            STAGE='result-encode'
            emit(dict(state='RESULT',schemaVersion=1,session=a.session,source=a.source,calibration=cal['id'],
                frames=meta['frames'],autodrive=lead,autosteer=dict(path=waypoints),autospeed=dict(detections=boxes),
                inferenceMs={n:v[1] for n,v in values.items()},guestPipelineMs=(time.perf_counter()-started)*1000,
                accuracy='NOT_QUALIFIED',assessment='NOT_RUN',motionAuthority=False))
    emit(dict(state='STOPPED',results=count,motionAuthority=False))


if __name__=='__main__':
    try:main()
    except Exception as error:
        import traceback
        trace=traceback.extract_tb(error.__traceback__)
        message=str(error);print(json.dumps(dict(state='FAILED',stage=STAGE,facts=FACTS,line=trace[-1].lineno if trace else None,
            code=message if message.isupper() and message.replace('_','').isalnum() else type(error).__name__)),flush=True)
        raise SystemExit(1)

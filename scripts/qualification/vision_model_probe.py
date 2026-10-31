# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Guest-only bounded ONNX execution probe; no actuation or accuracy claim."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time


def require(ok, code):
    if not ok:raise ValueError(code)


def validate_sequence(value, *, tensor_timing_only=False):
    rows=value['frames']
    require(value.get('kind')=='vision-camera-sequence' and 2<=len(rows)<=60,'SEQUENCE_INVALID')
    require(isinstance(value.get('source'),str) and value['source'] and value.get('camera')=='forward-rgb-720p-fov50','SEQUENCE_SOURCE_INVALID')
    for i,row in enumerate(rows):
        require(type(row['frame']) is int and type(row['simulationTime']) in (int,float)
                and math.isfinite(row['simulationTime']),'FRAME_METADATA_INVALID')
        require(row['file']==str(row['frame'])+'.jpg' and len(row['sha256'])==64,'FRAME_FILE_INVALID')
        if i:
            delta=row['simulationTime']-rows[i-1]['simulationTime']
            require(row['frame']>rows[i-1]['frame'] and 0<delta<=.5,'FRAME_PAIR_INTERVAL_INVALID')
            if not tensor_timing_only:require(.08<=delta<=.12,'FRAME_PAIR_INTERVAL_INVALID')
    return rows


def distribution(values):
    ordered=sorted(values)
    return dict(count=len(values),median=statistics.median(values),p95=ordered[min(len(ordered)-1,int(.95*len(ordered)))],
                max=max(values))


def valid_input_shapes(spec):
    # The pinned exports have a named dynamic batch dimension. Runtime tensors
    # still use exactly one image; spatial/channel dimensions remain fixed.
    return bool(spec) and all(row.type=='tensor(float)' and row.shape==['batch_size',3,512,1024] for row in spec)


def replay_manifest(source, frames, retained=None):
    """A later live workload never becomes the source of retained JPEGs."""
    if retained is not None:
        validate_sequence(retained,tensor_timing_only=True)
        require(retained['frames']==frames,'RETAINED_FRAME_METADATA_CHANGED')
        source=retained['source']
    value=dict(kind='vision-camera-sequence',camera='forward-rgb-720p-fov50',source=source,frames=frames)
    validate_sequence(value,tensor_timing_only=True)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',required=True,type=Path)
    parser.add_argument('--sequence',required=True,type=Path)
    parser.add_argument('--steady-seconds',type=int,default=0)
    parser.add_argument('--tensor-timing-only',action='store_true',required=True,
        help='Explicitly uncalibrated tensor-execution timing, never interpreted Vision output')
    args=parser.parse_args();root=args.payload
    require(0<=args.steady_seconds<=60,'STEADY_DURATION_INVALID')
    require(os.uname().machine=='aarch64' and sys.platform=='linux','LINUX_ARM64_GUEST_REQUIRED')
    require(len(os.sched_getaffinity(0))==4,'FOUR_VCPU_REQUIRED')
    lock=json.loads((root/'input-lock.json').read_bytes())
    require(lock['upstream']=='e7e5c614832f175f1f9f10a0d0c0df2559ff2c38','UPSTREAM_PIN_CHANGED')
    for row in lock['files']:
        relative=Path(row['path']);require(not relative.is_absolute() and '..' not in relative.parts,'PAYLOAD_PATH_INVALID')
        path=root/relative
        require(not path.is_symlink() and path.stat().st_size==row['bytes']
                and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'PAYLOAD_CHANGED')
    sys.path.insert(0,str(root/'libraries'))
    import numpy as np
    import cv2
    import onnxruntime as ort
    require((np.__version__,cv2.__version__,ort.__version__)==('2.4.4','4.13.0','1.26.0'),'LIBRARY_VERSIONS_CHANGED')
    cv2.setNumThreads(1)
    sequence=json.loads((args.sequence/'sequence.json').read_bytes())
    rows=validate_sequence(sequence,tensor_timing_only=args.tensor_timing_only)
    intervals=[b['simulationTime']-a['simulationTime'] for a,b in zip(rows,rows[1:])]
    tensors=[]
    mean=np.array([.485,.456,.406],dtype=np.float32).reshape(1,3,1,1)
    std=np.array([.229,.224,.225],dtype=np.float32).reshape(1,3,1,1)
    for row in rows:
        raw=(args.sequence/row['file']).read_bytes()
        require(hashlib.sha256(raw).hexdigest()==row['sha256'],'FRAME_CHANGED')
        bgr=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
        require(bgr is not None and bgr.shape==(720,1280,3),'FRAME_DIMENSIONS_INVALID')
        # Correct upstream top crop, color, CHW and normalization. AutoDrive
        # geometry is deliberately NOT claimed: no foreign H.yaml is adopted.
        image=cv2.resize(bgr[80:,:,:],(1024,512),interpolation=cv2.INTER_LINEAR)
        tensor=np.ascontiguousarray((image[:,:,::-1].astype(np.float32)/np.float32(255)).transpose(2,0,1)[None])
        tensors.append((tensor,np.ascontiguousarray((tensor-mean)/std)))
    sessions={};inputs={};loads={}
    for name in ('autodrive','autosteer','autospeed'):
        options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
        options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
        options.graph_optimization_level=ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        options.add_session_config_entry('session.intra_op.allow_spinning','0')
        options.log_severity_level=3
        begin=time.perf_counter()
        session=ort.InferenceSession(str(root/'models'/f'{name}_fp32.onnx'),options,providers=['CPUExecutionProvider'])
        require(session.get_providers()==['CPUExecutionProvider'],'CPU_PROVIDER_REQUIRED')
        spec=session.get_inputs();require(len(spec)==(2 if name=='autodrive' else 1),'MODEL_INPUT_COUNT_CHANGED')
        require(valid_input_shapes(spec),'MODEL_INPUT_SHAPE_CHANGED')
        sessions[name]=session;inputs[name]=[r.name for r in spec];loads[name]=time.perf_counter()-begin
        print(json.dumps(dict(stage='model-load',model=name,seconds=round(loads[name],3))),flush=True)
    def infer(name,index):
        session=sessions[name];current=tensors[index%len(tensors)];previous=tensors[(index-1)%len(tensors)]
        data=[previous[1],current[1]] if name=='autodrive' else [current[0]]
        options=ort.RunOptions();options.add_run_config_entry('memory.enable_memory_arena_shrinkage','cpu:0')
        begin=time.perf_counter();out=session.run(None,dict(zip(inputs[name],data)),options)
        require(all(np.isfinite(value).all() for value in out),'NONFINITE_MODEL_OUTPUT')
        return (time.perf_counter()-begin)*1000,[list(value.shape) for value in out]
    summaries={}
    for name in sessions:
        infer(name,1);measure=[infer(name,i) for i in range(1,min(len(tensors),7))]
        summaries[name]=dict(inferenceMs=distribution([v[0] for v in measure]),outputShapes=measure[0][1])
        print(json.dumps(dict(stage='model-measure',model=name,metrics=summaries[name])),flush=True)
    timings=[];steady=[];steady_elapsed=0.
    with ThreadPoolExecutor(max_workers=3) as pool:
        for index in range(1,min(len(tensors),13)):
            begin=time.perf_counter();futures=[pool.submit(infer,name,index) for name in sessions]
            for future in futures:future.result()
            timings.append((time.perf_counter()-begin)*1000)
        if args.steady_seconds:
            print(json.dumps(dict(stage='steady-start',seconds=args.steady_seconds)),flush=True)
            steady_begin=time.perf_counter();index=1
            while time.perf_counter()-steady_begin<args.steady_seconds:
                begin=time.perf_counter();futures=[pool.submit(infer,name,index) for name in sessions]
                for future in futures:future.result()
                steady.append((time.perf_counter()-begin)*1000)
                require(len(steady)<=1200,'STEADY_SAMPLE_LIMIT')
                index=index%(len(tensors)-1)+1
            steady_elapsed=time.perf_counter()-steady_begin
            print(json.dumps(dict(stage='steady-end',samples=len(steady),seconds=steady_elapsed)),flush=True)
    import resource
    print(json.dumps(dict(outcome='PASS_TENSOR_EXECUTION_ONLY',models=summaries,combinedMs=distribution(timings),
        combinedHz=1000/statistics.mean(timings),maxRssKiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        inputFrames=len(rows),precision='FP32',threadsPerSession=1,parallelSessions=3,
        sourcePairIntervalsSeconds=distribution(intervals),
        nominalPairCadenceConformant=all(.08<=v<=.12 for v in intervals),
        temporalFusion='NOT_QUALIFIED: actual source timestamps retained; tensor timing does not validate cadence',
        graphOptimization='ORT_DISABLE_ALL',memoryArenaShrink='cpu:0',
        steady=dict(seconds=steady_elapsed,samples=len(steady),hz=len(steady)/steady_elapsed,
                    combinedMs=distribution(steady)) if steady else dict(outcome='NOT_RUN'),
        semanticGeometry='NOT_VALIDATED: AutoDrive uses unwarped image tensors for compute timing only',
        upstreamPreprocessingParity='Color/CHW/normalization/top crop derived from pinned inference.cpp; BEV omitted explicitly',
        assessment='NOT_RUN',accuracy='NOT_QUALIFIED',nativeAosDeployment='NOT_RUN',
        calibratedFrameFusion='NOT_RUN',motionAuthority=False)),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as error:
        message=str(error)
        print(json.dumps(dict(outcome='NOT_COMPLETE',code=message if message.isupper() and message.replace('_','').isalnum() else type(error).__name__)),flush=True)
        raise SystemExit(1)

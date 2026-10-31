# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded engineering SSH camera protocol and calibrated planar geometry.

No simulator, model runtime or native-platform privileges are imported here.
"""
import hashlib
import json
import math
import struct

PROFILE='carla-forward-720p-fov50-v1'
MODEL_V=((.00209514907,-.000941721466,-9.24906396),
         (.00662758637,-.000352940531,-3.33396502),
         (.000120077371,-.00411343505,1.))


def require(ok,code):
    if not ok:raise ValueError(code)


def matmul(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]


def inverse(a):
    augmented=[list(map(float,row))+[float(i==j) for j in range(3)] for i,row in enumerate(a)]
    for i in range(3):
        pivot=max(range(i,3),key=lambda j:abs(augmented[j][i]))
        require(abs(augmented[pivot][i])>1e-12,'CALIBRATION_SINGULAR')
        augmented[i],augmented[pivot]=augmented[pivot],augmented[i]
        v=augmented[i][i];augmented[i]=[x/v for x in augmented[i]]
        for j in range(3):
            if i!=j:
                scale=augmented[j][i];augmented[j]=[x-scale*y for x,y in zip(augmented[j],augmented[i])]
    return [row[3:] for row in augmented]


def project(matrix,point):
    value=[sum(x*y for x,y in zip(row,(*point,1.))) for row in matrix]
    require(all(math.isfinite(v) for v in value) and abs(value[2])>1e-9,'PROJECTION_UNDEFINED')
    return [value[0]/value[2],value[1]/value[2]]


def calibration(world_to_camera,origin,forward,left):
    """CARLA UE (forward,right,up) -> image; ground (forward,left) metres.

    Origin and basis are calibration inputs only, never object labels or model
    predictions. Flat-road validity is separate from learned-model accuracy.
    """
    focal=1280/(2*math.tan(math.radians(50)/2))
    columns=[]
    for vector,translation in ((forward,False),(left,False),(origin,True)):
        columns.append([sum(world_to_camera[i][j]*vector[j] for j in range(3))+
                        (world_to_camera[i][3] if translation else 0) for i in range(3)])
    ground_to_image=[[focal*v[1]+640*v[0] for v in columns],
                     [-focal*v[2]+360*v[0] for v in columns],[v[0] for v in columns]]
    h=inverse(ground_to_image);c=matmul(inverse(MODEL_V),h)
    checks=[]
    for point in ((15,5),(30,-3),(75,2),(150,-5)):
        pixel=project(ground_to_image,point);restored=project(h,pixel)
        checks.append(math.dist(restored,point))
    require(max(checks)<1e-6,'CALIBRATION_ROUNDTRIP_FAILED')
    value=dict(profile=PROFILE,width=1280,height=720,fov=50,rawToGround=h,rawToModel=c,
        modelView=MODEL_V,cropTop=80,modelWidth=1024,modelHeight=512,
        geometry='Ideal pinhole, local planar road; not model-accuracy validation',maxRoundtripMetres=max(checks))
    value['id']=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    return value


def encode_packet(meta,images):
    require(len(images)==2 and all(isinstance(v,bytes) and 0<len(v)<=4*1024**2 for v in images),'FRAME_BYTES_INVALID')
    value=dict(meta,images=[dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for v in images])
    header=json.dumps(value,separators=(',',':'),allow_nan=False).encode()
    require(len(header)<=4096,'FRAME_HEADER_LIMIT')
    return struct.pack('!I',len(header))+header+b''.join(images)


def exact(stream,size):
    data=bytearray()
    while len(data)<size:
        value=stream.read(size-len(data));require(value,'TRUNCATED_STREAM');data.extend(value)
    return bytes(data)


def jpeg_dimensions(raw):
    """Inspect bounded SOF metadata before a native decoder can allocate pixels."""
    require(raw[:2]==b'\xff\xd8' and len(raw)<=4*1024**2,'JPEG_HEADER_INVALID')
    offset=2
    while offset+4<=len(raw):
        require(raw[offset]==255,'JPEG_MARKER_INVALID')
        marker=raw[offset+1];offset+=2
        while marker==255:
            require(offset<len(raw),'JPEG_HEADER_INVALID');marker=raw[offset];offset+=1
        require(marker not in (0,0xDA,0xD9),'JPEG_SOF_MISSING')
        size=struct.unpack('!H',raw[offset:offset+2])[0]
        require(size>=2 and offset+size<=len(raw),'JPEG_SEGMENT_INVALID')
        if marker in (0xC0,0xC1,0xC2):
            require(size>=8 and raw[offset+2]==8,'JPEG_SOF_INVALID')
            height,width=struct.unpack('!HH',raw[offset+3:offset+7])
            require((width,height)==(1280,720) and raw[offset+7]==3,'JPEG_DIMENSIONS_INVALID')
            return width,height
        offset+=size
    raise ValueError('JPEG_SOF_MISSING')


def read_packet(stream,session,source,calibration_id,last_frame):
    prefix=stream.read(4)
    if not prefix:return None
    require(len(prefix)==4,'TRUNCATED_STREAM');size=struct.unpack('!I',prefix)[0]
    require(0<size<=4096,'FRAME_HEADER_LIMIT');meta=json.loads(exact(stream,size))
    require(meta.get('schemaVersion')==1 and meta.get('session')==session and meta.get('source')==source
            and meta.get('calibration')==calibration_id,'FRAME_SCOPE_INVALID')
    refs=meta.get('frames');require(isinstance(refs,list) and len(refs)==2,'FRAME_PAIR_INVALID')
    require(all(type(v.get('frame')) is int and v['frame']>=0 and type(v.get('simulationTime')) in (int,float)
                and math.isfinite(v['simulationTime']) and v['simulationTime']>=0 for v in refs),'FRAME_METADATA_INVALID')
    dt=refs[1]['simulationTime']-refs[0]['simulationTime']
    require(last_frame<refs[1]['frame'] and refs[0]['frame']<refs[1]['frame'] and 0<dt<=.5,'FRAME_ORDER_INVALID')
    descriptors=meta.get('images');require(isinstance(descriptors,list) and len(descriptors)==2,'FRAME_BYTES_INVALID')
    images=[]
    for row in descriptors:
        require(type(row.get('bytes')) is int and 0<row['bytes']<=4*1024**2,'FRAME_BYTES_INVALID')
        image=exact(stream,row['bytes']);require(hashlib.sha256(image).hexdigest()==row.get('sha256'),'FRAME_DIGEST_INVALID')
        images.append(image)
    return meta,images,.08<=dt<=.12


def model_to_raw(x,y):return [x*1.25,y*1.25+80]


def usable_capture_pair(previous,current):
    """Reject startup duplicates/gaps before sending, without changing timestamps."""
    return (current['frame']>previous['frame'] and
            0<current['simulationTime']-previous['simulationTime']<=.5)


def write_all(stream,data):
    remaining=memoryview(data)
    while remaining:
        count=stream.write(remaining)
        require(type(count) is int and 0<count<=len(remaining),'STREAM_WRITE_FAILED')
        remaining=remaining[count:]
    stream.flush()


def validate_result(value,meta):
    require(value.get('state')=='RESULT' and value.get('schemaVersion')==1 and value.get('motionAuthority') is False
            and all(value.get(k)==meta[k] for k in ('session','source','calibration','frames')),'RESULT_BINDING_INVALID')
    points=value['autosteer']['path'];detections=value['autospeed']['detections'];lead=value['autodrive']
    require(isinstance(points,list) and len(points)<=64 and all(len(p)==2 and all(type(v) in (int,float) and math.isfinite(v) for v in p)
            and 0<=p[0]<=1024 and 0<=p[1]<=512 for p in points),'RESULT_PATH_INVALID')
    require(isinstance(detections,list) and len(detections)<=128,'RESULT_DETECTION_LIMIT')
    for d in detections:
        require(type(d['level']) is int and 0<=d['level']<=3 and len(d['box'])==4
                and all(type(v) in (int,float) and math.isfinite(v) for v in d['box'])
                and type(d['score']) in (int,float) and math.isfinite(d['score']) and 0<=d['score']<=1,'RESULT_DETECTION_INVALID')
    require(type(lead['valid']) is bool,'RESULT_LEAD_INVALID')
    if lead['valid']:
        require(type(lead['probability']) in (int,float) and math.isfinite(lead['probability']) and 0<=lead['probability']<=1,'RESULT_LEAD_INVALID')
    distance=lead['distanceEstimateMetres']
    require(distance is None or type(distance) in (int,float) and math.isfinite(distance) and 0<=distance<=150,'RESULT_DISTANCE_INVALID')
    require(type(value['guestPipelineMs']) in (int,float) and math.isfinite(value['guestPipelineMs']) and value['guestPipelineMs']>=0,'RESULT_TIMING_INVALID')
    return value

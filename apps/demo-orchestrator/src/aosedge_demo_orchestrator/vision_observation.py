# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Identity-free read-only Source projection, never an inference/control owner."""
import json
import math
import re

FIELDS={'schemaVersion','shadowOnly','state','reason','reference','frame','cameraFrame','captureAgeMs','sequence',
    'perceptionVersion','assessmentVersion','modelSet','lead','path','plan','imageMatched'}
REASONS={'SOURCE_NOT_SELECTED','WAITING_FOR_ANALYSIS','CALIBRATION_UNAVAILABLE','RESULT_STALE','ANALYSIS_STATUS',
    'CURRENT','WARMING','FIRST_INPUT','CAPTURE_GAP','EPOCH_CHANGED','RECOVERY_AFTER_REGRESSION','INPUT_RECOVERED',
    'CONTEXT_UNAVAILABLE','PERCEPTION_INVALID','ALGORITHM_INVALID','DYNAMICS_UNAVAILABLE','GEOMETRY_UNAVAILABLE',
    'FUSION_INVALID','INPUT_UNAVAILABLE','INCOMPATIBLE','AVAILABLE','SHADOW_PLAN_UNAVAILABLE'}


def require(ok):
    if not ok:raise ValueError('VISION_OBSERVATION_INVALID')


def number(value,low=-math.inf,high=math.inf):return type(value) in (int,float) and math.isfinite(value) and low<=value<=high


def observation(value):
    require(type(value) is dict and set(value)==FIELDS and type(value['schemaVersion']) is int and value['schemaVersion']==1
        and value['shadowOnly'] is True and value['state'] in ('AVAILABLE','WARMING','UNAVAILABLE','INCOMPATIBLE')
        and value['reason'] in REASONS and value['modelSet']=='Three FP32 models' and type(value['imageMatched']) is bool)
    require(value['reference'] is None or type(value['reference']) is str and re.fullmatch('vision-[0-9a-f]{24}',value['reference']))
    for key in ('frame','cameraFrame','sequence'):
        require(value[key] is None or type(value[key]) is int and 0<=value[key]<=2**53-1)
    require(value['captureAgeMs'] is None or number(value['captureAgeMs'],0,1000))
    for key in ('perceptionVersion','assessmentVersion'):
        require(value[key] is None or type(value[key]) is str and re.fullmatch(r'(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})',value[key]))
    if value['reference'] is None:
        require(value['state']=='UNAVAILABLE' and all(value[key] is None for key in ('frame','sequence','captureAgeMs','perceptionVersion','assessmentVersion','lead','path','plan')) and value['imageMatched'] is False)
    else:
        require(all(value[key] is not None for key in ('frame','sequence','captureAgeMs','perceptionVersion','assessmentVersion','lead','path','plan')))
        lead=value['lead'];path=value['path'];plan=value['plan']
        require(type(lead) is dict and set(lead)=={'valid','present','distanceMetres','relativeSpeedMps','distanceStddevMetres'} and type(lead['valid']) is bool)
        if not lead['valid']:require(all(lead[key] is None for key in lead if key!='valid'))
        elif lead['present'] is False:require(all(lead[key] is None for key in ('distanceMetres','relativeSpeedMps','distanceStddevMetres')))
        else:require(lead['present'] is True and number(lead['distanceMetres'],0,150) and number(lead['relativeSpeedMps'],-120,120) and number(lead['distanceStddevMetres'],0,150))
        require(type(path) is dict and set(path)=={'valid','points','crossTrackMetres','yawRadians','curvaturePerMetre'} and type(path['valid']) is bool)
        if not path['valid']:require(all(path[key] is None for key in path if key!='valid'))
        else:
            require(type(path['points']) is list and 1<=len(path['points'])<=16
                and all(type(point) is list and len(point)==2 and all(number(v) for v in point) for point in path['points'])
                and number(path['crossTrackMetres']) and number(path['yawRadians'],-math.pi,math.pi) and number(path['curvaturePerMetre']))
        require(type(plan) is dict and set(plan)=={'valid','accelerationMps2','firstSteeringRadians'} and type(plan['valid']) is bool)
        if not plan['valid']:require(plan['accelerationMps2'] is plan['firstSteeringRadians'] is None)
        else:require(value['state']=='AVAILABLE' and lead['valid'] and path['valid'] and number(plan['accelerationMps2']) and number(plan['firstSteeringRadians'],-math.pi/2,math.pi/2))
        if value['state']!='AVAILABLE':require(not any(row['valid'] for row in (lead,path,plan)))
        require(value['imageMatched']==(value['cameraFrame'] is not None and value['cameraFrame']==value['frame']))
    raw=json.dumps(value,allow_nan=False,separators=(',',':')).encode();require(len(raw)<=3072)
    return json.loads(raw)


def unavailable():
    return dict(schemaVersion=1,shadowOnly=True,state='UNAVAILABLE',reason='WAITING_FOR_ANALYSIS',reference=None,frame=None,
        cameraFrame=None,captureAgeMs=None,sequence=None,perceptionVersion=None,assessmentVersion=None,modelSet='Three FP32 models',
        lead=None,path=None,plan=None,imageMatched=False)

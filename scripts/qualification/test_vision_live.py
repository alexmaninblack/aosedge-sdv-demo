# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline geometry, input framing and scope checks; no live host workload."""
import copy
import io
import math
import struct
import unittest
from vision_live_contract import calibration,encode_packet,inverse,model_to_raw,project,read_packet,jpeg_dimensions,usable_capture_pair,write_all,validate_result,FrameClock,FRAME_CLOCK,WIRE_SCHEMA
from vision_live_worker import response


class GeometryTests(unittest.TestCase):
    def test_flat_camera_projection_and_canonical_model_view(self):
        # Camera: x=1.6, z=1.5; vehicle origin on a flat road.
        w2c=[[1,0,0,-1.6],[0,1,0,0],[0,0,1,-1.5],[0,0,0,1]]
        c=calibration(w2c,[0,0,0],[1,0,0],[0,-1,0])
        f=1280/(2*math.tan(math.radians(25)))
        for x,y in ((15,5),(30,0),(100,-4)):
            uv=[640-f*y/(x-1.6),360+f*1.5/(x-1.6)]
            self.assertLess(math.dist(project(c['rawToGround'],uv),[x,y]),1e-8)
            self.assertLess(math.dist(project(c['modelView'],project(c['rawToModel'],uv)),[x,y]),1e-8)
        self.assertEqual([640,400],model_to_raw(512,256))

    def test_singular_and_horizon_are_not_valid_distances(self):
        with self.assertRaisesRegex(ValueError,'SINGULAR'):inverse([[0]*3]*3)
        with self.assertRaisesRegex(ValueError,'UNDEFINED'):project([[1,0,0],[0,1,0],[0,0,0]],[1,2])


class PacketTests(unittest.TestCase):
    def test_result_identity_shape_and_authority_are_fail_closed(self):
        meta=self.packet()
        value=dict(meta,state='RESULT',motionAuthority=False,autosteer=dict(path=[[512,300]]),
            autospeed=dict(detections=[]),autodrive=dict(valid=True,probability=.02,distanceEstimateMetres=None),guestPipelineMs=200.)
        self.assertEqual(value,validate_result(value,meta))
        for key,wrong in (('session','foreign'),('frames',[]),('motionAuthority',True),('schemaVersion',1),('guestPipelineMs',float('nan'))):
            bad=copy.deepcopy(value);bad[key]=wrong
            with self.assertRaises(ValueError):validate_result(bad,meta)
        bad=copy.deepcopy(value);bad['autosteer']['path']=[[float('nan'),0]]
        with self.assertRaises(ValueError):validate_result(bad,meta)

    def test_partial_pipe_writes_are_completed_not_silently_truncated(self):
        class Partial(io.BytesIO):
            def write(self,value):return super().write(value[:3])
        stream=Partial();write_all(stream,b'0123456789');self.assertEqual(b'0123456789',stream.getvalue())

    def test_startup_duplicates_are_dropped_without_retiming(self):
        first=dict(frame=10,simulationTime=1.)
        self.assertFalse(usable_capture_pair(first,dict(frame=12,simulationTime=1.)))
        self.assertFalse(usable_capture_pair(first,dict(frame=12,simulationTime=2.)))
        self.assertTrue(usable_capture_pair(first,dict(frame=12,simulationTime=1.05)))

    def test_jpeg_dimensions_checked_without_a_native_decoder(self):
        value=b'\xff\xd8\xff\xc0'+struct.pack('!HBHHB',8,8,720,1280,3)
        self.assertEqual((1280,720),jpeg_dimensions(value))
        with self.assertRaisesRegex(ValueError,'DIMENSIONS'):jpeg_dimensions(value[:-3]+struct.pack('!HB',40000,3))
        for bad in (b'not-jpeg',b'\xff\xd8\xff\xda\x00\x08'):
            with self.assertRaises(ValueError):jpeg_dimensions(bad)

    def packet(self):
        return dict(schemaVersion=WIRE_SCHEMA,session='session',source='source',calibration='cal',frames=[
            dict(frame=10,simulationTime=1,sensorSimulationTime=1,clock=FRAME_CLOCK),
            dict(frame=12,simulationTime=1.1,sensorSimulationTime=1.1,clock=FRAME_CLOCK)])

    def read(self,value,last=-1):return read_packet(io.BytesIO(value),'session','source','cal',last)

    def test_real_pair_and_bytes_roundtrip(self):
        data=encode_packet(self.packet(),[b'first-jpeg',b'second-jpeg'])
        meta,images,valid=self.read(data)
        self.assertTrue(valid);self.assertEqual([b'first-jpeg',b'second-jpeg'],images)
        self.assertEqual(self.packet()['frames'],meta['frames'])

    def test_foreign_scope_fails_before_consuming_image_bytes(self):
        for key in ('session','source','calibration','schemaVersion'):
            v=self.packet();v[key]='foreign'
            with self.assertRaisesRegex(ValueError,'SCOPE'):self.read(encode_packet(v,[b'a',b'b']))

    def test_unidentified_or_mismatched_clock_is_rejected(self):
        for field,value in (('clock','ARRIVAL_TIME'),('sensorSimulationTime',2.)):
            v=self.packet();v['frames'][0][field]=value
            with self.assertRaisesRegex(ValueError,'CLOCK'):self.read(encode_packet(v,[b'a',b'b']))
        v=self.packet();del v['frames'][0]['sensorSimulationTime']
        with self.assertRaisesRegex(ValueError,'CLOCK'):self.read(encode_packet(v,[b'a',b'b']))

    def test_irregular_pair_is_explicit_not_retimed(self):
        v=self.packet();v['frames'][1]['simulationTime']=1.15
        v['frames'][1]['sensorSimulationTime']=1.15
        meta,_,valid=self.read(encode_packet(v,[b'a',b'b']))
        self.assertFalse(valid);self.assertEqual(1.15,meta['frames'][1]['simulationTime'])

    def test_regression_replay_nonfinite_and_truncation_fail(self):
        packet=encode_packet(self.packet(),[b'a',b'b'])
        for value,last in ((packet,12),(packet[:-1],-1),(struct.pack('!I',5000),-1)):
            with self.assertRaises(ValueError):self.read(value,last)
        v=self.packet();v['frames'][0]['simulationTime']=float('nan')
        with self.assertRaises(ValueError):encode_packet(v,[b'a',b'b'])

    def test_image_digest_and_bound_are_enforced(self):
        data=encode_packet(self.packet(),[b'a',b'b'])
        with self.assertRaisesRegex(ValueError,'DIGEST'):self.read(data[:-1]+b'c')
        with self.assertRaisesRegex(ValueError,'BYTES'):encode_packet(self.packet(),[b'',b'x'])

    def test_coalesced_result_lines_are_drained_without_waiting_on_a_pipe(self):
        value,pending=response(None,b'{"state":"A"}\n{"state":"B"}\n',.1)
        self.assertEqual(dict(state='A'),value)
        value,pending=response(None,pending,.1)
        self.assertEqual((dict(state='B'),b''),(value,pending))


class FrameClockTests(unittest.TestCase):
    def test_exact_frame_world_time_not_resampled_sensor_time(self):
        clock=FrameClock();clock.note(10,1.);clock.note(12,1.1)
        a=clock.bind(dict(frame=10,simulationTime=1.05));b=clock.bind(dict(frame=12,simulationTime=1.1))
        self.assertAlmostEqual(.1,b['simulationTime']-a['simulationTime'])
        self.assertEqual(1.05,a['sensorSimulationTime']);self.assertEqual(FRAME_CLOCK,a['clock'])
        self.assertEqual({'50.0':1,'0.0':1},clock.facts()['sensorMinusWorldMs'])

    def test_no_timestamp_is_invented_when_snapshot_is_absent(self):
        clock=FrameClock();clock.note(10,1.)
        self.assertIsNone(clock.bind(dict(frame=12,simulationTime=1.1)))
        self.assertEqual(1,clock.facts()['missingFrames'])

    def test_conflicting_epoch_and_large_disagreement_fail_closed(self):
        clock=FrameClock();clock.note(10,1.)
        with self.assertRaisesRegex(ValueError,'MISMATCH'):clock.bind(dict(frame=10,simulationTime=1.2))
        clock.note(10,1.1)
        with self.assertRaisesRegex(ValueError,'CHANGED'):clock.bind(dict(frame=10,simulationTime=1.))

    def test_snapshot_history_is_bounded(self):
        clock=FrameClock(8)
        for frame in range(100):clock.note(frame,frame*.05)
        self.assertEqual(8,clock.facts()['retainedFrames'])
        self.assertIsNone(clock.bind(dict(frame=1,simulationTime=.05)))

    def test_genuine_gap_and_world_epoch_are_not_hidden(self):
        clock=FrameClock();clock.note(10,1.);clock.note(14,1.2)
        a=clock.bind(dict(frame=10,simulationTime=1.));b=clock.bind(dict(frame=14,simulationTime=1.2))
        self.assertAlmostEqual(.2,b['simulationTime']-a['simulationTime'])
        self.assertFalse(.08<=b['simulationTime']-a['simulationTime']<=.12)
        clock.note(1,.05)
        with self.assertRaisesRegex(ValueError,'EPOCH'):clock.bind(dict(frame=14,simulationTime=1.2))


if __name__=='__main__':unittest.main()

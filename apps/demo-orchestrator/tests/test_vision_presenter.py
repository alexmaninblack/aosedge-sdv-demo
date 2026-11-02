# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock,patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from aosedge_demo_orchestrator import vision_presenter as p,vision_observation as v,presenter


class VisionPresenterTests(unittest.TestCase):
    def source(self):
        source=Mock();source.root=Path('/fixture/SDV-Vision-Camera-Image-Lab-Data');return source

    def state(self):return dict(vmProfile='aos-vision-main-qemuarm64-v1',source=dict(state='RUNNING'),vehicles=dict(test=dict(runtime=dict(state='RUNNING'))))

    def test_only_selected_vision_profile_and_closed_dto_cross_boundary(self):
        source=self.source();source.observe.return_value=dict(vision=v.unavailable(),unitId='PRIVATE',credential='PRIVATE')
        with patch.object(p,'read_json',return_value=self.state()):
            value=p.VisionReader(source)()
        self.assertEqual(set(value),{'profile','observedAt','vision','controller','source'})
        self.assertNotIn('PRIVATE',json.dumps(value));self.assertEqual(value['vision'],v.unavailable())
        with patch.object(p,'read_json',return_value=dict(self.state(),vmProfile='main')):
            with self.assertRaisesRegex(ValueError,'TARGET_REQUIRED'):p.VisionReader(source)

    def test_missing_invalid_or_stopped_observation_clears_not_caches(self):
        source=self.source()
        for observed in (dict(),dict(vision=dict(v.unavailable(),unitId='PRIVATE'))):
            source.observe.return_value=observed
            with patch.object(p,'read_json',return_value=self.state()):self.assertEqual(p.VisionReader(source)()['vision'],v.unavailable())
        source.observe.reset_mock();state=self.state();state['source']['state']='STOPPED'
        with patch.object(p,'read_json',return_value=state):self.assertEqual(p.VisionReader(source)()['vision'],v.unavailable())
        source.observe.assert_not_called()

    def test_vision_http_has_no_mutation_or_main_cloud_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            assets=p.assets(Path(directory)/'view')
            with patch.object(presenter,'StudioCloudReader') as cloud:
                cloud.return_value.application.environment_service.root=Path(directory)
                server=presenter.make_server(assets,address=('127.0.0.1',0),reader=lambda:dict(profile='vision',vision=v.unavailable()),vision_only=True)
                thread=threading.Thread(target=server.serve_forever);thread.start()
                try:
                    url='http://127.0.0.1:'+str(server.server_port)
                    with urlopen(url+'/api/presenter/snapshot') as response:self.assertEqual(json.load(response)['vision'],v.unavailable())
                    for path,code in (('/api/presenter/platform',404),('/api/presenter/backend/brake',404),('/api/presenter/monitoring',404)):
                        with self.assertRaises(HTTPError) as error:urlopen(url+path)
                        self.assertEqual(error.exception.code,code)
                    with self.assertRaises(HTTPError) as error:urlopen(Request(url+'/api/presenter/operations',data=b'{}',method='POST'))
                    self.assertEqual(error.exception.code,405)
                    with urlopen(url+'/') as response:self.assertIn(b'NO VEHICLE CONTROL',response.read())
                finally:server.shutdown();thread.join();server.server_close()
            with self.assertRaisesRegex(ValueError,'READ_ONLY_REQUIRED'):presenter.make_server(assets,native=object(),vision_only=True)


if __name__=='__main__':unittest.main()

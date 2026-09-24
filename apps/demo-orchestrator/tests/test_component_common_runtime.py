# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""V1/V2 must use the reviewed common runtime without acquiring V3 capabilities."""
import contextlib
import copy
import importlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator import component_build as build
from aosedge_demo_orchestrator.component_sources import UNSIGNED_SHA, source
from aosedge_demo_orchestrator.components import ComponentService, archive_files, sha
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, FACTORY, MANIFEST
from test_component_replay import inputs


class CommonRuntimeTests(unittest.TestCase):
    def test_prepare_and_inspection_use_common_runtime_for_both_profiles(self):
        modules={build.PACKAGE+n:('REVIEWED_'+n.replace('.','_')+' = True\n').encode()
                 for n in ('runtime.py','bridge.py','manifest.py')}
        pin=dict(build.ADVISORY_RUNTIME_PIN,modules=dict(build.ADVISORY_RUNTIME_PIN['modules']))
        pin['modules'].update({n.removeprefix(build.PACKAGE):sha(raw) for n,raw in modules.items()})
        for profile in ('v1','v2'):
            with self.subTest(profile=profile),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                service=ComponentService(SimpleNamespace(root=root,catalog=SimpleNamespace(project=root/'artifacts'),
                    _writer=contextlib.nullcontext))
                service.root.mkdir(parents=True)
                baseline,digest,contract=inputs(profile)
                fixture=root/'contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json'
                fixture.parent.mkdir(parents=True);fixture.write_bytes(build.encoded(contract))
                journal=root/JOURNAL;journal.parent.mkdir(parents=True,exist_ok=True)
                journal.write_bytes(build.encoded({'factory':dict(version='6.1.1-maninblack.29',sha256='offline',
                    format='raw',path=FACTORY['raw'],manifestPath=MANIFEST)}))
                inspected={'source':{'legacyArchiveSha256':digest,'unsignedSha256':UNSIGNED_SHA[build.PROFILE_BASES[profile][0]]},
                           'sourceIntegrity':'VERIFIED_PINNED_DIGESTS'}
                with patch.object(build,'ADVISORY_RUNTIME_PIN',pin),patch.object(build,'advisory_source',return_value=modules), \
                        patch('aosedge_demo_orchestrator.component_sources.source',return_value=(inspected,baseline)), \
                        patch.object(service,'_worker',side_effect=AssertionError('No Cloud permitted')):
                    receipt=service.prepare('112.0.0',profile)
                    self.assertEqual(build.COMMON_RUNTIME_BUILD_TYPE,receipt['buildType'])
                    self.assertEqual([],service.inspect('112.0.0')['problems'])
                    with self.assertRaisesRegex(EnvironmentError,'DESTINATION_EXISTS'):
                        service.prepare('112.0.0',profile)

    def test_pin_required_before_any_release_reservation_for_v1_and_v2(self):
        for profile in ('v1', 'v2'):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as tmp:
                env = SimpleNamespace(root=Path(tmp), catalog=SimpleNamespace(project=Path(tmp)),
                                      _writer=contextlib.nullcontext)
                service = ComponentService(env)
                with patch.object(build, 'ADVISORY_RUNTIME_PIN', None), patch.object(service, '_worker') as worker:
                    with self.assertRaisesRegex(EnvironmentError, 'SOURCE_CHECKPOINT_REQUIRED'):
                        service.prepare(None, profile)
                worker.assert_not_called()

    def test_compose_is_deterministic_and_preserves_profile_dependencies_and_history(self):
        modules = {build.PACKAGE+n: ('CURRENT_'+n.replace('.', '_')+' = True\n').encode()
                   for n in ('runtime.py', 'bridge.py', 'manifest.py')}
        pin = dict(build.ADVISORY_RUNTIME_PIN, modules=dict(build.ADVISORY_RUNTIME_PIN['modules']))
        pin['modules'].update({n.removeprefix(build.PACKAGE):sha(raw) for n,raw in modules.items()})
        for profile in ('v1', 'v2'):
            baseline, digest, contract = inputs(profile)
            old = copy.deepcopy(baseline)
            with self.subTest(profile=profile), patch.object(build, 'ADVISORY_RUNTIME_PIN', pin), \
                    patch.object(build, 'advisory_source', return_value=modules):
                args = ('112.0.0', profile, baseline, digest, Path('/not-read'), contract,
                        {'version':'offline', 'sha256':'offline'})
                kw = {'unsigned_source_sha':UNSIGNED_SHA[build.PROFILE_BASES[profile][0]]}
                first, record = build.compose_common_runtime(*args, **kw)
                second, repeated = build.compose_common_runtime(*args, **kw)
                self.assertEqual(first, second)
                self.assertEqual(record, repeated)
                self.assertEqual(old, baseline)
                payload=archive_files(first['vehicle-data-platform/vdp-112.0.0-arm64.tar.gz'])
                for name,raw in modules.items():self.assertEqual(raw,payload[name])
                for name in ('lib/native.so','bin/vehicle-data-provider',build.PACKAGE+'vdp_release_profile.py'):
                    self.assertEqual(baseline[name],payload[name])
                self.assertEqual([],json.loads(payload['config/capability-manifest.json'])['advisoryEndpoints'])
                self.assertNotIn(build.PACKAGE+'advisory_transport.py',payload)
                self.assertEqual('NOT_APPLICABLE',record['advisory'])
                provenance=json.loads(payload['provenance/provenance.json'])
                build.validate_common_payload(payload,provenance)
                for mutation in ('runtime','buildType','sourceTree','advisory','inputs'):
                    bad=copy.deepcopy(payload); prov=copy.deepcopy(provenance)
                    if mutation=='runtime':bad[build.PACKAGE+'runtime.py']=baseline[build.PACKAGE+'runtime.py']
                    elif mutation=='buildType':prov['buildType']='democtl-profile-replay-v1'
                    elif mutation=='sourceTree':prov['sourceTree']='f'*40
                    elif mutation=='advisory':bad[build.PACKAGE+'advisory.py']=b'pass'
                    else:prov['buildInputs']=[]
                    with self.assertRaises(EnvironmentError):build.validate_common_payload(bad,prov)

    def test_real_retained_bases_load_current_runtime_without_advisory(self):
        solution=Path(__file__).resolve().parents[3]
        platform=solution.parent/'aos-vehicle-platform'
        project=solution.parent/'demo-artifacts/aosedge-sdv-demo'
        if not (platform/'.git').exists() or not project.exists():
            self.skipTest('optional local immutable payload fixtures unavailable')
        service=ComponentService(SimpleNamespace(catalog=SimpleNamespace(project=project)))
        contract=json.loads((solution/'contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json').read_bytes())
        for profile in ('v1','v2'):
            version,digest,_,count=build.PROFILE_BASES[profile]
            inspected,baseline=source(service,version,materialize=False)
            transport,record=build.compose_common_runtime('112.0.0',profile,baseline,digest,platform,contract,
                {'version':'offline','sha256':'offline'},unsigned_source_sha=inspected['source']['unsignedSha256'])
            payload=archive_files(transport['vehicle-data-platform/vdp-112.0.0-arm64.tar.gz'])
            with self.subTest(profile=profile),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                for name,raw in payload.items():
                    if name.startswith((build.PACKAGE,'config/')):
                        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
                name='common_packaging_proof'
                package=root/build.PACKAGE
                spec=importlib.util.spec_from_file_location(name,package/'__init__.py',submodule_search_locations=[str(package)])
                mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod
                try:
                    spec.loader.exec_module(mod)
                    runtime=importlib.import_module(name+'.runtime')
                    config=runtime.load_payload_configuration(root/'config/provider.json')
                    self.assertFalse(config.advisory_enabled)
                    self.assertEqual(count,len(config.signals))
                    bridge=importlib.import_module(name+'.bridge')
                    self.assertIn('repeated',bridge.Snapshot.__dataclass_fields__)
                    self.assertEqual(build.ADVISORY_RUNTIME_PIN['modules']['runtime.py'],sha(payload[build.PACKAGE+'runtime.py']))
                finally:
                    for key in list(sys.modules):
                        if key==name or key.startswith(name+'.'):del sys.modules[key]

if __name__=='__main__':unittest.main()

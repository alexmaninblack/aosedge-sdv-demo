# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('vehicle_inputs', SCRIPTS / 'vehicle_inputs.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class VehicleInputsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.integration, self.platform, self.artifacts = [self.root / n for n in ('integration', 'platform', 'artifacts')]
        self.output = self.root / 'Candidate with spaces'
        self.firmware = self.root / 'QEMU_EFI.fd'
        self.put(self.firmware, b'firmware')
        self.factory = dict(version='6.1.1-maninblack.39', image='main-qemuarm64.img', format='raw',
                            sizeBytes=7, sha256=digest(b'factory'), sourceRevision='a' * 40)
        self.put(self.integration / 'workspace/checkpoints/demo-v1.1.json', {'factory': self.factory})
        self.factory_dir = self.artifacts / 'factory-images' / self.factory['version']
        self.put(self.factory_dir / 'manifest.json', {'factoryImage': dict(version=self.factory['version'],
            architecture='main-qemuarm64', path=self.factory['image'], byteLength=7, sha256=self.factory['sha256'], format='raw'),
            'source': {'revision': 'a' * 40}})
        self.image = self.factory_dir / self.factory['image']
        self.put(self.image, b'factory')
        self.image.chmod(0o444)
        self.inventory = dict(publicBinaryObservations=[dict(component='QEMU_EFI.fd', bytes=8, sha256=digest(b'firmware'))],
                              unsignedVdpInputs=[], vdpPreparationSource={'commonAndAdvisoryRuntime': 'b' * 40}, serviceExports=[])
        bases = {}
        for profile, version in [('v1', '1.0.16'), ('v2', '2.0.0'), ('v3', '3.0.0')]:
            raw = version.encode()
            self.inventory['unsignedVdpInputs'].append(dict(version=version, bytes=len(raw), sha256=digest(raw)))
            source = dict(schemaVersion=1, version=version, unsignedSha256=digest(raw), legacyArchiveSha256='c' * 64,
                          trust='REVIEWED_SOURCE_DIGESTS')
            folder = self.artifacts / 'components/vehicle-data-provider/.source-profiles' / version
            self.put(folder / 'package.tar.gz', raw)
            self.put(folder / 'source.json', source)
            bases[profile] = version, 'c' * 64
        self.product_raw = b'executable'
        for team, profile in [('brake', 'v1'), ('brake', 'v2'), ('brake', 'v3'), ('tire', 'v1')]:
            pin = dict(team=team, profile=profile, source='d' * 40,
                       bootstrapSha256=digest(self.product_raw), serviceSha256=digest(self.product_raw))
            self.inventory['serviceExports'].append(pin)
            output = self.artifacts / 'services' / team / 'builds' / pin['source'] / profile / 'output'
            product = dict(schemaVersion=1, sourceRevision=pin['source'], functionalProfile=profile, os='linux', architecture='arm64',
                kind=team + '-health-linux-arm64-product', binaries=[dict(path='rootfs/usr/bin/' + team + '-health-' + role,
                size=len(self.product_raw), sha256=digest(self.product_raw)) for role in ('bootstrap', 'service')],
                tests=dict(ctest='passed', count=8, report='evidence/ctest-results.xml', reportSha256=digest(b'ctest')))
            self.put(output / 'product-build.json', product)
            self.put(output / 'evidence/ctest-results.xml', b'ctest')
        self.save_inventory()
        for name in module.CONTRACTS:
            self.put(self.integration / 'contracts' / name, {})
        for root in (self.integration, self.platform):
            self.put(root / 'LICENSE', b'notice')
        inspector = SimpleNamespace(_inspect=lambda version, path: (dict(problems=[], signedEnvelope=False,
                                    sha256=digest(path.read_bytes()), readPathCount=7), {}))
        builder = SimpleNamespace(PROFILE_BASES=bases, advisory_runtime_pin=lambda: {'revision': 'b' * 40},
                                   advisory_source=lambda repo: {'python/provider/runtime.py': b'# reviewed'})
        def products(build, team):
            files = {'usr/bin/' + team + '-health-' + role: (self.product_raw, 0o755) for role in ('bootstrap', 'service')}
            files['usr/share/licenses/' + team + '-health-service/LICENSE'] = b'MIT', 0o444
            return files
        self.api = inspector, builder, products

    def put(self, path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json.dumps(raw).encode() if isinstance(raw, dict) else raw)

    def save_inventory(self):
        self.put(self.integration / 'workspace/distribution-stage0-inventory.json', self.inventory)

    def collect(self):
        return module.collect(self.integration, self.platform, self.artifacts, self.firmware, self.api)

    def test_allowlist_excludes_run_state_and_signed_releases(self):
        self.put(self.artifacts / 'private.pem', b'never read')
        self.put(self.artifacts / 'release/package.sign', b'never read')
        files, image, identities = self.collect()
        self.assertEqual(image, self.image)
        self.assertEqual(len(identities['vdpProfiles']), 3)
        self.assertEqual(len(identities['serviceProfiles']), 4)
        self.assertFalse(any('private' in name or 'package.sign' in name for name in files))
        self.assertIn('vdp/reviewed-runtime/python/provider/runtime.py', files)

    def test_missing_service_profile(self):
        self.inventory['serviceExports'].pop()
        self.save_inventory()
        with self.assertRaisesRegex(module.BundleError, 'Incomplete service'):
            self.collect()

    def service_checkpoint(self, rows=None):
        name = 'workspace/checkpoints/services-candidate.json'
        rows = rows if rows is not None else [dict(r, architecture='linux/arm64') for r in self.inventory['serviceExports']]
        self.put(self.integration / name, dict(schemaVersion=1, kind='reviewed-service-exports', serviceExports=rows))
        return name

    def test_explicit_service_checkpoint_preserves_historical_inventory(self):
        name = self.service_checkpoint()
        self.inventory['serviceExports'] = []
        self.save_inventory()
        old = (self.integration / 'workspace/distribution-stage0-inventory.json').read_bytes()
        _, _, identities = module.collect(self.integration, self.platform, self.artifacts, self.firmware,
            self.api, service_checkpoint=name)
        self.assertEqual(len(identities['serviceProfiles']), 4)
        self.assertEqual((self.integration / 'workspace/distribution-stage0-inventory.json').read_bytes(), old)

    def test_explicit_service_checkpoint_never_falls_back(self):
        for name, error in [('workspace/checkpoints/absent.json', FileNotFoundError),
                            ('../outside.json', module.BundleError)]:
            with self.subTest(name=name), self.assertRaises(error):
                module.collect(self.integration, self.platform, self.artifacts, self.firmware,
                    self.api, service_checkpoint=name)
        name = self.service_checkpoint([])
        with self.assertRaisesRegex(module.BundleError, 'Incomplete service'):
            module.collect(self.integration, self.platform, self.artifacts, self.firmware,
                self.api, service_checkpoint=name)

    def test_invalid_service_checkpoint_identity_is_rejected_before_products(self):
        for key, value in [('source', '../escape'), ('source', 'main'), ('architecture', 'linux/amd64'),
                           ('bootstrapSha256', 'bad'), ('serviceSha256', True), ('unexpected', 'field')]:
            rows = [dict(r, architecture='linux/arm64') for r in self.inventory['serviceExports']]
            rows[0][key] = value
            name = self.service_checkpoint(rows)
            with self.subTest(key=key, value=value), patch.object(module, 'service_inputs') as reader:
                with self.assertRaisesRegex(module.BundleError, 'Service checkpoint identity'):
                    module.collect(self.integration, self.platform, self.artifacts, self.firmware,
                        self.api, service_checkpoint=name)
                reader.assert_not_called()

    def test_service_checkpoint_duplicates_and_mixed_brake_revisions_rejected(self):
        original = [dict(r, architecture='linux/arm64') for r in self.inventory['serviceExports']]
        for rows in ([original[0], original[0], *original[2:]],
                     [dict(original[0], source='e'*40), *original[1:]]):
            name = self.service_checkpoint(rows)
            with self.assertRaises(module.BundleError):
                module.service_pins(self.integration, self.inventory, name)

    def test_service_checkpoint_bad_schema_and_link_rejected(self):
        name = self.service_checkpoint()
        for version in (2, True, '1'):
            self.put(self.integration / name, dict(schemaVersion=version, kind='reviewed-service-exports', serviceExports=[]))
            with self.assertRaisesRegex(module.BundleError, 'schema'):
                module.service_pins(self.integration, self.inventory, name)
        self.put(self.integration / name, b'{"schemaVersion": 1, "schemaVersion": 2}')
        with self.assertRaisesRegex(module.BundleError, 'Duplicate'):
            module.service_pins(self.integration, self.inventory, name)
        (self.integration / name).unlink()
        (self.integration / name).symlink_to(self.integration / 'workspace/distribution-stage0-inventory.json')
        with self.assertRaisesRegex(module.BundleError, 'symlink'):
            module.service_pins(self.integration, self.inventory, name)

    def test_new_service_checkpoint_keeps_binary_pin_guard(self):
        rows = [dict(r, architecture='linux/arm64') for r in self.inventory['serviceExports']]
        rows[0]['bootstrapSha256'] = '0'*64
        name = self.service_checkpoint(rows)
        with self.assertRaisesRegex(module.BundleError, 'binary pins'):
            module.collect(self.integration, self.platform, self.artifacts, self.firmware,
                self.api, service_checkpoint=name)

    def test_reviewed_reproduction_checkpoint_matches_selected_component_sources(self):
        root = SCRIPTS.parents[1]
        pins = module.service_pins(root, {}, 'workspace/checkpoints/reproduction-services-20261008.json')
        release = json.loads((root / 'workspace/releases/kit028-setup042.json').read_text())
        sources = {row['id']: row['revision'] for row in release['sources']}
        for pin in pins:
            owner = 'functional-service' if pin['team'] == 'brake' else 'tire-health-service'
            self.assertEqual(pin['source'], sources[owner])

    def test_explicit_checkpoint_does_not_rewrite_historical_return_point(self):
        original = (self.integration / module.DEFAULT_FACTORY_CHECKPOINT).read_bytes()
        name = 'workspace/checkpoints/factory-candidate.json'
        self.put(self.integration / name, {'factory': self.factory})
        _, image, identities = module.collect(self.integration, self.platform, self.artifacts,
            self.firmware, self.api, factory_checkpoint=name)
        self.assertEqual(image, self.image)
        self.assertEqual(identities['factory'], self.factory)
        self.assertEqual((self.integration / module.DEFAULT_FACTORY_CHECKPOINT).read_bytes(), original)

    def test_explicit_checkpoint_fails_closed_without_default_fallback(self):
        with self.assertRaises(FileNotFoundError):
            module.collect(self.integration, self.platform, self.artifacts, self.firmware,
                self.api, factory_checkpoint='workspace/checkpoints/missing.json')
        with self.assertRaisesRegex(module.BundleError, 'relative'):
            module.collect(self.integration, self.platform, self.artifacts, self.firmware,
                self.api, factory_checkpoint='../outside.json')

    def test_invalid_factory_identity_rejected_before_catalogue_read(self):
        for key, value in [('version', '../escape'), ('image', '../escape.img'),
                           ('sourceRevision', 'main'), ('sha256', 'bad'), ('sizeBytes', True)]:
            name = 'workspace/checkpoints/invalid.json'
            self.put(self.integration / name, {'factory': {**self.factory, key: value}})
            with self.subTest(key=key), self.assertRaisesRegex(module.BundleError, 'identity invalid'):
                module.collect(self.integration, self.platform, self.artifacts, self.firmware,
                    self.api, factory_checkpoint=name)

    def test_missing_vdp_profile(self):
        self.inventory['unsignedVdpInputs'].pop()
        self.save_inventory()
        with self.assertRaisesRegex(module.BundleError, 'Incomplete VDP'):
            self.collect()

    def test_firmware_tamper(self):
        self.firmware.write_bytes(b'tampered')
        with self.assertRaisesRegex(module.BundleError, 'Firmware digest'):
            self.collect()

    def test_old_runtime_rejected(self):
        self.inventory['vdpPreparationSource']['commonAndAdvisoryRuntime'] = 'e' * 40
        self.save_inventory()
        with self.assertRaisesRegex(module.BundleError, 'runtime pin'):
            self.collect()

    def test_vdp_digest_mismatch(self):
        self.inventory['unsignedVdpInputs'][0]['sha256'] = '0' * 64
        self.save_inventory()
        with self.assertRaisesRegex(module.BundleError, 'Unsigned VDP digest'):
            self.collect()

    def test_signed_or_invalid_vdp_rejected(self):
        self.api[0]._inspect = lambda *args: (dict(problems=[], signedEnvelope=True, sha256='', readPathCount=7), {})
        with self.assertRaisesRegex(module.BundleError, 'inspection'):
            self.collect()

    def test_mutable_factory_rejected(self):
        self.image.chmod(0o644)
        with self.assertRaisesRegex(module.BundleError, 'immutable'):
            self.collect()

    def test_factory_manifest_mismatch(self):
        path = self.factory_dir / 'manifest.json'
        data = json.loads(path.read_text())
        data['factoryImage']['sha256'] = '0' * 64
        self.put(path, data)
        with self.assertRaisesRegex(module.BundleError, 'checkpoint'):
            self.collect()

    def test_symlink_rejected(self):
        self.firmware.unlink()
        self.firmware.symlink_to(self.image)
        with self.assertRaisesRegex(module.BundleError, 'symlink'):
            self.collect()

    def test_service_test_receipt_mismatch(self):
        path = self.artifacts / 'services/brake/builds' / ('d' * 40) / 'v1/output/evidence/ctest-results.xml'
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(module.BundleError, 'test receipt'):
            self.collect()

    def test_service_binary_pin_mismatch(self):
        self.inventory['serviceExports'][0]['bootstrapSha256'] = '0' * 64
        self.save_inventory()
        with self.assertRaisesRegex(module.BundleError, 'binary pins'):
            self.collect()

    def test_existing_output_and_disk_guard(self):
        args = (self.integration, self.platform, self.artifacts, self.firmware, self.output, self.api)
        with patch.object(module.shutil, 'disk_usage', return_value=SimpleNamespace(free=0)), self.assertRaisesRegex(module.BundleError, 'reserve'):
            module.assemble(*args)
        self.output.mkdir()
        with self.assertRaisesRegex(module.BundleError, 'new'):
            module.assemble(*args)

    def test_assembly_clones_only_factory_and_records_relative_payload(self):
        calls = []
        def copy(args, **kwargs):
            calls.append(args)
            shutil.copyfile(args[-2], args[-1])
        with patch.object(module.shutil, 'disk_usage', return_value=SimpleNamespace(free=100 * 2**30)), patch.object(module.subprocess, 'run', side_effect=copy):
            result = module.assemble(self.integration, self.platform, self.artifacts, self.firmware, self.output, self.api)
        self.assertEqual(calls[0][:3], ['/bin/cp', '-c', '-p'])
        self.assertFalse(result['runtimeSelectorsChanged'])
        self.assertFalse(result['externalDistributionApproved'])
        for row in result['files']:
            self.assertFalse(Path(row['path']).is_absolute())
            self.assertEqual(module.sha256(self.output / row['path']), row['sha256'])

    def test_clone_digest_failure_is_not_success(self):
        target = self.root / 'wrong.img'
        with patch.object(module.subprocess, 'run', side_effect=lambda *a, **k: target.write_bytes(b'wrong')):
            with self.assertRaisesRegex(module.BundleError, 'transfer'):
                module.clone_factory(self.image, target, self.factory)


if __name__ == '__main__':
    unittest.main()

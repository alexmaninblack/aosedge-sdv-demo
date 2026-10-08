# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import inspect
import unittest
from unittest.mock import patch
from aosedge_demo_orchestrator import component_runtime as runtime
from aosedge_demo_orchestrator import factory_mainline_gates as gates


class TimestampSuccessorFactoryTests(unittest.TestCase):
    def test_effective_image_version_is_not_inherited_from_old_configuration(self):
        values = dict(AOS_ROOTFS_IMAGE_VERSION='6.1.1-maninblack.41', MACHINE='qemuarm64',
                      DISTRO='aos-core', AOS_ARCHITECTURE='arm64', BB_NO_NETWORK='1', BB_FETCH_PREMIRRORONLY='1')
        data = '\n'.join(f'{key}="{value}"' for key, value in values.items())
        gates.check_factory_image(data, '41')
        for old in ('6.1.1-maninblack.11', '6.1.1-maninblack.27'):
            with self.assertRaisesRegex(ValueError, 'AOS_ROOTFS_IMAGE_VERSION'):
                gates.check_factory_image(data.replace('6.1.1-maninblack.41', old), '41')

    def test_exact_source_and_preserved_predecessor(self):
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.41'],
                         '3fd1f8eb8e8d51c7e89c9f89f1646c7d4f55494f')
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.40'],
                         '9adee816b4f942ceafb4d30da4adba318352bf59')
        self.assertEqual(gates.CM_LAUNCHER_TEST_COUNTS['41'], 53)
        self.assertEqual(gates.SM_LAUNCHER_TEST_COUNTS['41'], 32)
        self.assertIn('self.factory_suffix in ("40", "41")', inspect.getsource(gates.NativeGates.run))

    def test_committed_gate_tooling_and_kuksa_before_image(self):
        calls = []
        with patch.object(runtime.subprocess, 'check_output', side_effect=[b'', b'a' * 40, b'archive']), patch.object(runtime.subprocess, 'run'):
            result = runtime.stage_mainline_factory_gates([], calls.append, '/build', '/source', '41')
        self.assertIn('/factory41-gates-', result['conf'])
        self.assertIn('/qualification/factory-41.conf', '\n'.join(calls))
        build = inspect.getsource(runtime.build_factory)
        self.assertLess(build.index('targets += " kuksa-databroker"'), build.index('"-c compile " + targets'))


if __name__ == '__main__':
    unittest.main()

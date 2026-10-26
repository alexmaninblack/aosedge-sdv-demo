# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import inspect
from pathlib import Path
import tempfile
import unittest
from aosedge_demo_orchestrator import component_runtime as runtime
from aosedge_demo_orchestrator import factory_mainline_gates as gates


class ReservedPortFactoryTests(unittest.TestCase):
    def test_cold_build_budgets_do_not_change_default_or_runtime_timeouts(self):
        self.assertEqual(runtime.factory_build_timeouts(), dict(compile=1200, package=1200, image=2400))
        self.assertEqual(runtime.factory_build_timeouts(True), dict(compile=14400, package=7200, image=7200))
        with self.assertRaisesRegex(runtime.EnvironmentError, 'BUDGET_INVALID'):
            runtime.factory_build_timeouts('yes')

    def test_fresh_builder_uses_the_new_normal_owner_host_pin_not_legacy_alias(self):
        command = runtime.builder_ssh(legacy_alias=False)
        self.assertNotIn('HostKeyAlias=[127.0.0.1]:10023', command)
        self.assertIn('StrictHostKeyChecking=yes', command)
        self.assertIn('BatchMode=yes', command)
        self.assertIn('HostKeyAlias=[127.0.0.1]:10023', runtime.builder_ssh())

    def test_candidate_pin_and_prior_build_inputs_remain_distinct(self):
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.42'],
                         '81d098e5a958710d8c12a6bfdb86c7c493274920')
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.41'],
                         '3fd1f8eb8e8d51c7e89c9f89f1646c7d4f55494f')
        self.assertEqual(gates.SM_LAUNCHER_TEST_COUNTS['42'], gates.SM_LAUNCHER_TEST_COUNTS['41'])
        self.assertEqual(gates.CM_LAUNCHER_TEST_COUNTS['42'], gates.CM_LAUNCHER_TEST_COUNTS['41'])

    def test_rootfs_policy_is_checked_before_disk_assembly(self):
        source = inspect.getsource(runtime.build_factory)
        self.assertLess(source.index("' ports --root '"), source.index('assemble the same six-partition'))
        self.assertIn('FACTORY_ROOTFS_PATH_UNEXPECTED', source)

    def test_rootfs_gate_requires_exact_policy_and_finite_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                gates.port_policy(root)
            policy = root / 'usr/lib/sysctl.d/99-aos-kuksa-ports.conf'
            policy.parent.mkdir(parents=True)
            policy.write_text('# public policy\nnet.ipv4.ip_local_reserved_ports = 100-102,55555\n')
            for unit in ('nfs-mountd.service', 'kuksa-databroker.service'):
                p = root / 'usr/lib/systemd/system' / (unit + '.d/10-aos-kuksa-ports.conf')
                p.parent.mkdir(parents=True)
                p.write_text('[Unit]\nRequires=systemd-sysctl.service\nAfter=systemd-sysctl.service\n')
            gates.port_policy(root)
            policy.write_text('net.ipv4.ip_local_reserved_ports = 100-102\n')
            with self.assertRaisesRegex(ValueError, 'not reserved'):
                gates.port_policy(root)

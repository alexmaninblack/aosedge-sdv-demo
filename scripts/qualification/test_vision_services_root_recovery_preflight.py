# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import ast
from pathlib import Path
import runpy
import subprocess
import sys
import unittest


class ReadonlyPreflightTests(unittest.TestCase):
    def test_explicit_scenario_helpers_load_under_isolated_python(self):
        script=Path(__file__).with_name('vision_services_root_recovery_preflight.py')
        result=subprocess.run([sys.executable,'-I','-B',str(script),'--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('--attempt',result.stdout)

    def test_schema_projection_never_copies_defaults_or_arbitrary_response_fields(self):
        module=runpy.run_path(str(Path(__file__).with_name('vision_services_root_recovery_preflight.py')))
        value=module['schema_fields'](dict(update_component_ids=dict(type='array',required=True,read_only=False,
            default='DO_NOT_COPY',choices=['DO_NOT_COPY'],help_text='DO_NOT_COPY')))
        self.assertEqual(value,dict(update_component_ids=dict(type='array',required=True,read_only=False)))

    def test_the_preflight_defines_no_mutating_cloud_or_vm_operation(self):
        script=Path(__file__).with_name('vision_services_root_recovery_preflight.py');tree=ast.parse(script.read_bytes())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                for keyword in node.keywords:
                    if keyword.arg=='method' and isinstance(keyword.value,ast.Constant):
                        self.assertIn(keyword.value.value,('GET','OPTIONS'))
                if isinstance(node.func,ast.Attribute) and node.func.attr=='call' and len(node.args)>1:
                    self.assertIsInstance(node.args[1],ast.Constant);self.assertEqual(node.args[1].value,'GET')
        self.assertNotIn('VMService',script.read_text())


if __name__=='__main__':unittest.main()

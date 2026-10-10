# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline wizard tests. No real installer, credentials, Docker or network calls."""
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/prepare-macos.sh'


class PrepareMacTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='p', dir='/private/tmp' if sys.platform == 'darwin' else None)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def shell(self, body, input='', ok=True):
        result = subprocess.run(['/bin/bash', '-c', 'source ' + shlex.quote(str(SCRIPT)) + '\n' + body],
                                input=input, text=True, capture_output=True, timeout=15)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def executable(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/bash\n' + text)
        path.chmod(0o700)
        return str(path)

    def test_help_and_requirements_need_no_setup(self):
        for option in ('--help', '--requirements'):
            result = subprocess.run(['/bin/bash', str(SCRIPT), option], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        req = json.loads(result.stdout)
        # The standalone projection cannot silently drift from the build owners.
        engines = json.loads((ROOT / 'apps/presenter-ui/package.json').read_text())['engines']
        self.assertEqual((req['node'], req['npm']), (engines['node'], engines['npm']))
        lock = json.loads((ROOT / 'workspace/dependencies/carla-macos-arm64-r1.lock.json').read_text())
        self.assertEqual(req['pythonMinor'], lock['compatibility']['python'])

    def test_bad_cli_stops_before_host_access(self):
        for args in ('--oops', '--parent', '--xcode', '--state-dir'):
            result = self.shell('uname() { echo UNEXPECTED_HOST_PROBE; }; main ' + args, ok=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('UNEXPECTED_HOST_PROBE', result.stdout)

    def test_version_comparison(self):
        self.shell('version_at_least 3.24.0 3.24 && version_at_least 4.1.0 3.24 && ! version_at_least 3.23.9 3.24 && ! version_at_least broken 3.24')

    def test_paths_reject_links_traversal_and_relative_paths(self):
        (self.root / 'link').symlink_to(self.root, target_is_directory=True)
        for path in ('relative', str(self.root / 'link/x'), str(self.root)+'/../other', '/tmp/x\ny'):
            result = self.shell('safe_path ' + shlex.quote(path), ok=False)
            self.assertNotEqual(result.returncode, 0, path)
        self.shell('safe_path ' + shlex.quote(str(self.root / 'folder with spaces')))

    def test_capacity_and_disconnect_fail_closed(self):
        self.assertNotEqual(self.shell('FREE_KIB=1; check_capacity', ok=False).returncode, 0)
        result = self.shell('SELECTED_UUID=original; SDV_PARENT=/example; inspect_volume() { VOLUME_UUID=replacement; }; recheck_storage', ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('disconnected', result.stderr)

    def test_continuation_passes_environment_and_stops_on_bootstrap_failure(self):
        state = self.root/'state'
        state.mkdir()
        environment = state/'environment.sh'
        environment.write_text('export FIXTURE_ENV=loaded\n')
        environment.chmod(0o600)
        python = self.executable('continuation-python', 'printf "CONTINUED %s %s\\n" "$FIXTURE_ENV" "$SDV_WORKFLOW_VOLUME"\n')
        body = f'''STATE={shlex.quote(str(state))}; SDV_ROOT={shlex.quote(str(self.root))}
LOG={shlex.quote(str(self.root/'bootstrap.log'))}
SDV_PYTHON={shlex.quote(python)}; SELECTED_UUID=fixture-volume
recheck_storage() {{ :; }}
private_file() {{ :; }}
bootstrap_checkout() {{ printf 'BOOTSTRAP\\n'; return BOOTSTRAP_CODE; }}
continue_workflow
'''
        success = self.shell(body.replace('BOOTSTRAP_CODE', '0'))
        self.assertIn('CONTINUED loaded fixture-volume', success.stdout)
        fail = self.shell(body.replace('BOOTSTRAP_CODE', '12'), ok=False)
        self.assertEqual(fail.returncode, 1)
        self.assertIn('failed (exit 12)', fail.stderr)
        self.assertNotIn('CONTINUED', fail.stdout)

    def test_long_operation_plain_output_has_no_heartbeat_spam(self):
        result = self.shell(f'''LOG={shlex.quote(str(self.root/'progress.log'))}
recheck_storage() {{ :; }}
run_install 'Fixture tool preparation' /bin/bash -c 'echo diagnostic-only'
''')
        self.assertIn('Fixture tool preparation', result.stdout)
        self.assertIn('Done.', result.stdout)
        self.assertNotIn('diagnostic-only', result.stdout)
        self.assertNotIn('Still working', result.stdout)
        self.assertNotIn('\033', result.stdout)
        self.assertEqual((self.root/'progress.log').read_text(), 'diagnostic-only\n')

    def test_host_tool_capacity_is_separate_from_external_workspace(self):
        result = self.shell("df() { printf 'Filesystem blocks used avail\n/dev/fixture 100 99 1\n'; }; check_host_capacity", ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Host tool storage', result.stderr)

    def test_exact_node_and_architecture(self):
        node = self.executable('node', 'case "$1" in --version) echo v26.0.0 ;; -p) echo arm64 ;; esac\n')
        npm = self.executable('npm', 'echo 11.12.1\n')
        self.shell(f'node_ok {shlex.quote(node)} && npm_ok {shlex.quote(node)} {shlex.quote(npm)}')
        Path(node).write_text('#!/bin/bash\ncase "$1" in --version) echo v26.0.0 ;; -p) echo x64 ;; esac\n')
        self.assertNotEqual(self.shell('node_ok ' + shlex.quote(node), ok=False).returncode, 0)

    def test_owned_directory_collision_is_preserved(self):
        folder = self.root / 'foreign'
        folder.mkdir()
        (folder / 'keep').write_text('user content')
        result = self.shell('owned_dir ' + shlex.quote(str(folder)), ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((folder / 'keep').read_text(), 'user content')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS filesystem metadata')
    def test_owned_directory_repeat_and_state_are_data_not_code(self):
        state = self.root / 'state'
        sentinel = self.root / 'executed'
        value = '$(touch '+str(sentinel)+')'
        body = f'''umask 077
STATE={shlex.quote(str(state))}
owned_dir "$STATE"; owned_dir "$STATE"
SDV_PARENT={shlex.quote(value)}; SDV_TMP=/scratch; SELECTED_UUID=uuid
SDV_DRIVE_ACCOUNT=; SDV_BUILD_BINDING=; SDV_SIM_BINDING=; SDV_SIGNING_IDENTITY=; DEVELOPER_DIR=/xcode
save_choices
state_get SDV_PARENT
'''
        self.assertIn(value, self.shell(body).stdout)
        self.assertFalse(sentinel.exists())
        self.assertEqual((state / 'selections.tsv').stat().st_mode & 0o777, 0o600)

    def test_interrupted_python_reuses_interpreter_without_recreating_venv(self):
        body = '''SDV_ROOT=/fixture; SDV_PYTHON=/fixture/tools/python/bin/python3.12
SDV_CMAKE=/fixture/cmake; BASE_PYTHON=; PYTHON_OK=no
cmake_ok() { return 0; }; python_ok() { return 0; }; owned_dir() { :; }
install_formula() { echo UNEXPECTED_FORMULA; exit 50; }
run_install() { printf '%s\n' "$1"; }
/fixture/tools/python/bin/python3.12() { :; }
prepare_python_cmake
'''
        result = self.shell(body)
        self.assertNotIn('Prepare isolated Python', result.stdout)
        self.assertIn('Install Python packaging', result.stdout)

    def test_ready_node_is_never_downloaded_or_installed(self):
        result = self.shell('''SDV_NODE=/fixture/node; SDV_NPM=/fixture/npm; SDV_ROOT=/fixture
node_ok() { :; }; npm_ok() { :; }; run_install() { echo UNEXPECTED_INSTALL; exit 51; }
prepare_node''')
        self.assertNotIn('UNEXPECTED', result.stdout)

    def test_cancel_install_stops_owned_process_group(self):
        pidfile = self.root/'child-pid'
        log = self.root/'install.log'
        body = f'''source {shlex.quote(str(SCRIPT))}
LOG={shlex.quote(str(log))}; LOCKED=no
recheck_storage() {{ :; }}
trap 'cleanup' EXIT
trap 'exit 143' TERM
run_install fixture /bin/bash -c 'echo $$ > "$1"; exec sleep 30' _ {shlex.quote(str(pidfile))}
'''
        process = subprocess.Popen(['/bin/bash', '-c', body], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='backslashreplace')
        try:
            for _ in range(50):
                if pidfile.exists(): break
                time.sleep(.05)
            self.assertTrue(pidfile.exists())
            child_pid = int(pidfile.read_text())
            process.send_signal(signal.SIGTERM)
            output, error = process.communicate(timeout=8)
            self.assertNotIn('\\x', error, error)
            self.assertEqual(process.returncode, 143)
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=8)

    def test_bad_archive_is_not_extracted(self):
        work = self.root / 'cache/node'
        work.mkdir(parents=True)
        name = 'node-v26.0.0-darwin-arm64.tar.gz'
        (work / name).write_bytes(b'corrupt')
        (work / 'SHASUMS256.txt').write_text('0'*64 + '  ' + name + '\n')
        result = self.shell(f'''SDV_ROOT={shlex.quote(str(self.root))}; SDV_NODE=
owned_dir() {{ :; }}
run_install() {{ echo UNEXPECTED_INSTALL; exit 52; }}
prepare_node''', ok=False)
        self.assertIn('checksum mismatch', result.stderr)
        self.assertNotIn('UNEXPECTED', result.stdout)
        self.assertEqual((work/name).read_bytes(), b'corrupt')

    def bindings(self):
        paths = []
        for name, roles in (('build.json', ('vehicle-bases', 'factory-image')),
                            ('simulation.json', ('carla-runtime', 'host-support', 'gateway-sdk'))):
            path = self.root/name
            lock_name = 'developer-factory41-r1' if name == 'build.json' else 'carla-macos-arm64-r1'
            import hashlib
            lock = json.loads((ROOT/'workspace/dependencies'/f'{lock_name}.lock.json').read_text())
            lock_digest = hashlib.sha256(json.dumps(lock, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            path.write_text(json.dumps(dict(schemaVersion=1, lockDigest=lock_digest, folderId='folder_123456789',
                                            files={role: 'file_123456789_'+role for role in roles})))
            paths.append(path)
        return paths

    def drive_body(self, mode='local', python=None):
        a, b = self.bindings()
        return f'''SDV_PYTHON={shlex.quote(python or sys.executable)}
SDV_GCLOUD=/not-called; SDV_DRIVE_ACCOUNT=reader@example.invalid
STATE={shlex.quote(str(self.root))}; ADVANCED_INPUTS=yes; PRIVATE_INPUTS=yes
SDV_BUILD_BINDING={shlex.quote(str(a))}; SDV_SIM_BINDING={shlex.quote(str(b))}
drive_probe {mode}
'''

    def test_binding_local_checks_do_not_authenticate(self):
        result = self.shell(self.drive_body())
        self.assertIn('Drive access is not checked', result.stdout)

    def test_invalid_binding_is_sanitized(self):
        body = self.drive_body().replace('drive_probe local', 'SDV_BUILD_BINDING=/missing; drive_probe local')
        result = self.shell(body, ok=False)
        self.assertEqual(result.returncode, 12)
        self.assertNotIn('Traceback', result.stderr)

    def test_normal_prompt_does_not_ask_for_json_files(self):
        result = self.shell('''SDV_DRIVE_ACCOUNT=; CONFIGURE_ACCESS=no; ADVANCED_INPUTS=no
SDV_SIGNING_IDENTITY=; SDV_BUILD_BINDING=/missing; SDV_SIM_BINDING=/missing
ask() { echo "$1" >&2; printf reader@example.invalid; }
identity_ready() { :; }; save_choices() { :; }
choose_access''')
        self.assertNotIn('Google account', result.stderr)
        self.assertNotIn('Full path', result.stderr)
        self.assertIn('automatically', result.stdout)

    def test_automatic_path_ignores_legacy_manual_selection(self):
        result = self.shell('''STATE=/fixture; ADVANCED_INPUTS=no
SDV_BUILD_BINDING=/old/build; SDV_SIM_BINDING=/old/simulation
catalog_paths
printf '%s\\n' "$SDV_BUILD_BINDING" "$SDV_SIM_BINDING" "$SDV_PREPARED_SOURCE"''')
        self.assertNotIn('/old/', result.stdout)
        self.assertIn('/public/source-requirements.json', result.stdout)

    def test_public_tools_do_not_probe_or_install_gcloud(self):
        result = self.shell('''PRIVATE_INPUTS=no; SDV_DOCKER=/existing/docker; SDV_GCLOUD=
need_brew() { echo UNEXPECTED; exit 50; }
prepare_access_tools''')
        self.assertNotIn('UNEXPECTED', result.stdout)

    def test_private_mode_keeps_explicit_account_prompt(self):
        result = self.shell('''PRIVATE_INPUTS=yes; SDV_DRIVE_ACCOUNT=; ADVANCED_INPUTS=no
ask() { echo "$1" >&2; printf reader@example.invalid; }
identity_ready() { :; }; save_choices() { :; }
choose_access''')
        self.assertIn('Google account', result.stderr)

    def test_unpublished_public_catalog_stops_before_prompts_or_installation(self):
        result = self.shell('''uname() { case "$1" in -s) echo Darwin ;; -m) echo arm64 ;; esac; }
sw_vers() { echo 26.6.2; }; id() { echo 501; }
SDV_PUBLIC_CATALOG_URL=; SDV_PUBLIC_CATALOG_RECORD=
choose_storage() { echo UNEXPECTED; exit 50; }
main --state-dir /private/tmp/sdv-unused-public-probe''', ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('PUBLIC RELEASE NOT YET AVAILABLE', result.stdout)
        self.assertNotIn('UNEXPECTED', result.stdout)

    def python_interceptor(self, prefix):
        # Execute the real embedded helper against fixture-only stdlib stubs.
        wrapper = self.root/'python-fixture'
        wrapper.write_text('#!'+sys.executable+'\nimport sys\ncode=sys.stdin.read()\nsys.argv=sys.argv[3:]\nexec('+repr(prefix)+'+code)\n')
        wrapper.chmod(0o700)
        return str(wrapper)

    def test_drive_authorization_failure_does_not_leak_token_or_stderr(self):
        wrapper = self.python_interceptor('''import subprocess
subprocess.run=lambda *a,**k: subprocess.CompletedProcess(a,1,'SECRET_TOKEN','SECRET_DIAGNOSTIC: run gcloud auth login')
''')
        result = self.shell(self.drive_body('remote', wrapper), ok=False)
        self.assertEqual(result.returncode, 10)
        self.assertNotIn('SECRET', result.stdout+result.stderr)

    def test_drive_metadata_success_no_media_downloads_or_secret_output(self):
        wrapper = self.python_interceptor('''import json, subprocess, urllib.request
subprocess.run=lambda *a,**k: subprocess.CompletedProcess(a,0,'SECRET_TOKEN','')
class Response:
 def __init__(self,url): self.url=url
 def __enter__(self): return self
 def __exit__(self,*a): pass
 def read(self,n):
  url=self.url
  assert 'alt=media' not in url
  if '/about?' in url: value={'user':{'emailAddress':'reader@example.invalid'}}
  elif '/files/folder_' in url: value={'mimeType':'application/vnd.google-apps.folder','trashed':False}
  else: value={'id':url.split('/files/')[1].split('?')[0],'trashed':False,'parents':['folder_123456789'],'capabilities':{'canDownload':True}}
  return json.dumps(value).encode()
class Opener:
 def open(self,request,timeout):
  assert request.headers['Authorization']=='Bearer SECRET_TOKEN'
  assert request.get_method()=='GET'
  return Response(request.full_url)
urllib.request.build_opener=lambda *a: Opener()
''')
        result = self.shell(self.drive_body('remote', wrapper))
        self.assertIn('all five inputs checked', result.stdout)
        self.assertNotIn('SECRET', result.stdout+result.stderr)

    def test_docker_remote_context_is_rejected_without_info_or_lifecycle(self):
        wrapper = self.python_interceptor('''import subprocess
def run(args,**kwargs):
 assert args[1:]==['context','inspect','desktop-linux']
 return subprocess.CompletedProcess(args,0,'[{"Endpoints":{"docker":{"Host":"tcp://elsewhere:2376"}}}]','')
subprocess.run=run
''')
        result = self.shell(f'SDV_PYTHON={shlex.quote(wrapper)}; SDV_DOCKER=/fake; docker_ready', ok=False)
        self.assertEqual(result.returncode, 1)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS filesystem metadata')
    def wizard_fixture(self, mode='', input='yes\n', fail=False):
        # All external probes/installers are replaced; real orchestration and
        # local state/lock/environment behavior are exercised in a disposable root.
        body = f'''uname() {{ case "$1" in -s) echo Darwin ;; -m) echo arm64 ;; esac; }}
ask() {{ case "$1" in 'Short socket-test'*) printf '%s' {shlex.quote(str(self.root/'.tmp'))} ;; *) IFS= read -r fixture_answer; printf '%s' "$fixture_answer" ;; esac; }}
SDV_PUBLIC_CATALOG_URL=https://drive.google.com/uc?export=download; SDV_PUBLIC_CATALOG_RECORD=fixture-public-pin
sw_vers() {{ echo 26.6.2; }}
inspect_volume() {{ VOLUME_UUID=fixture-uuid; VOLUME_NAME=Fixture; VOLUME_MOUNT={shlex.quote(str(self.root))}; FREE_KIB=999999999; }}
load_choices() {{ DEVELOPER_DIR=/fixture/xcode; SDV_DRIVE_ACCOUNT=reader@example.invalid; SDV_BUILD_BINDING=/fixture/build.json; SDV_SIM_BINDING=/fixture/sim.json; SDV_SIGNING_IDENTITY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA; }}
discover() {{ XCODE_OK=yes; BREW=/fixture/brew; SDV_CMAKE=/fixture/cmake; BASE_PYTHON=/fixture/python; PYTHON_OK=yes; SDV_NODE=/fixture/node; SDV_NPM=/fixture/npm; SDV_DOCKER=/fixture/docker; SDV_GCLOUD=/fixture/gcloud; SDV_PYTHON=/fixture/python; }}
prepare_python_cmake() {{ [ -f "$STATE/python-done" ] || printf installed > "$STATE/python-done"; }}
prepare_node() {{ {'die "fixture interruption"' if fail else ':'}; }}
prepare_access_tools() {{ :; }}
docker_ready() {{ :; }}
choose_access() {{ :; }}
drive_probe() {{ say "fixture access $1"; }}
identity_ready() {{ :; }}
continue_workflow() {{ say 'WORKFLOW_CONTINUED'; }}
main --state-dir {shlex.quote(str(self.root/'state'))} --parent {shlex.quote(str(self.root))} {mode}
'''
        return self.shell(body, input=input, ok=not fail and input != 'no\n')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS filesystem metadata')
    def test_check_and_decline_never_create_state(self):
        result = self.wizard_fixture('--check', input='')
        self.assertIn('CHECK ONLY', result.stdout)
        self.assertFalse((self.root/'state').exists())
        result = self.wizard_fixture(input='no\n')
        self.assertIn('Cancelled', result.stdout)
        self.assertFalse((self.root/'state').exists())

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS filesystem metadata')
    def test_default_continues_but_prepare_only_and_check_do_not(self):
        self.assertIn('WORKFLOW_CONTINUED', self.wizard_fixture().stdout)
        self.assertNotIn('WORKFLOW_CONTINUED', self.wizard_fixture('--prepare-only').stdout)
        self.assertNotIn('WORKFLOW_CONTINUED', self.wizard_fixture('--check', input='').stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS filesystem metadata')
    def test_first_repeat_and_interrupted_resume(self):
        interrupted = self.wizard_fixture(fail=True)
        self.assertNotEqual(interrupted.returncode, 0)
        env = self.root/'state/environment.sh'
        self.assertIn('incomplete', env.read_text())
        self.assertFalse((self.root/'state/active').exists())
        self.assertFalse((self.root/'sdv/.tmp/.bootstrap').exists())
        done = self.root/'state/python-done'
        stamp = done.stat().st_mtime_ns
        for _ in range(2):
            result = self.wizard_fixture()
            self.assertIn('READY FOR SOURCE PREPARATION', result.stdout)
            self.assertEqual(done.stat().st_mtime_ns, stamp)
            self.assertFalse((self.root/'state/active').exists())
            self.assertFalse((self.root/'sdv/.tmp/.bootstrap').exists())
            self.assertEqual(env.stat().st_mode & 0o777, 0o600)
        for shell in ('/bin/bash', '/bin/zsh'):
            result = subprocess.run([shell, '-n', str(env)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS filesystem metadata')
    def test_environment_works_in_bash_zsh_and_rejects_missing_volume(self):
        self.wizard_fixture()
        env = self.root/'state/environment.sh'
        for shell in ('/bin/bash', '/bin/zsh'):
            for uuid in ('fixture-uuid', 'different-volume'):
                body = 'diskutil() { printf x; }; plutil() { printf %s ' + shlex.quote(uuid) + '; }; source ' + shlex.quote(str(env))
                result = subprocess.run([shell, '-c', body], capture_output=True, text=True)
                self.assertEqual(result.returncode == 0, uuid == 'fixture-uuid', result.stdout+result.stderr)

    def test_google_access_denied_does_not_trigger_missing_auth_code(self):
        wrapper = self.python_interceptor('''import io, subprocess, urllib.request, urllib.error
subprocess.run=lambda *a,**k: subprocess.CompletedProcess(a,0,'SECRET_TOKEN','')
class Opener:
 def open(self,request,timeout):
  raise urllib.error.HTTPError(request.full_url,403,'SECRET_PROVIDER_MESSAGE',{},io.BytesIO(b'{"error":{"errors":[{"reason":"forbidden"}]}}'))
urllib.request.build_opener=lambda *a: Opener()
''')
        result = self.shell(self.drive_body('remote', wrapper), ok=False)
        self.assertEqual(result.returncode, 12)
        self.assertNotIn('SECRET', result.stdout+result.stderr)

    def test_google_network_failure_preserves_login(self):
        wrapper = self.python_interceptor('''import subprocess
subprocess.run=lambda *a,**k: subprocess.CompletedProcess(a,1,'','SECRET_DETAILS: network timeout')
''')
        result = self.shell(self.drive_body('remote', wrapper), ok=False)
        self.assertEqual(result.returncode, 12)
        self.assertIn('preserved', result.stdout)
        self.assertNotIn('SECRET', result.stdout+result.stderr)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS filesystem metadata')
    def test_dead_lock_recovery_and_active_owner_rejection(self):
        self.wizard_fixture()
        lock = self.root/'state/active'
        lock.mkdir(mode=0o700)
        (lock/'pid').write_text(str(os.getpid()))
        (lock/'pid').chmod(0o600)
        result = self.wizard_fixture(fail=True)
        self.assertIn('still running', result.stderr)
        (lock/'pid').write_text('2147483647')
        result = self.wizard_fixture()
        self.assertIn('READY FOR SOURCE PREPARATION', result.stdout)
        self.assertFalse(lock.exists())


if __name__ == '__main__':
    unittest.main()

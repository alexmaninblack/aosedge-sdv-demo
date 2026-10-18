# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline fixtures only: no download, package manager, mount, UI or build."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / 'scripts/aosedge-sdv-lab.sh'
INSTALL = ROOT / 'scripts/launcher/install-macos.sh'
HEAVY = ROOT / 'scripts/launcher/heavy-macos.sh'
COMMON = ROOT / 'scripts/launcher/common-macos.sh'
DEVELOPER = ROOT / 'scripts/prepare-macos.sh'
CATALOG = ROOT / 'workspace/launcher-catalog.json'


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sdv-unit-', dir='/private/tmp' if sys.platform == 'darwin' else None)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.state = self.root / 'state'

    def shell(self, body, script=ENTRY, input='', ok=True):
        env = dict(os.environ, SDV_LAB_HELPER=str(DEVELOPER), SDV_LAB_COMMON=str(COMMON),
                   SDV_LAB_CATALOG=str(CATALOG), SDV_LAB_STATE=str(self.state))
        result = subprocess.run(['/bin/bash', '-c', 'source ' + shlex.quote(str(script)) + '\n' + body],
                                input=input, text=True, capture_output=True, timeout=15, env=env)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_pin_and_canonical_authority_projection(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/sync-launcher-pins'), '--check'],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_help_and_all_plans_have_no_host_or_state_side_effect(self):
        for args in ('--help', '--route A --plan', '--route B --plan', '--route C --component factory --plan',
                     '--route C --component simulator --plan'):
            result = self.shell(f'''uname() {{ echo UNEXPECTED_PROBE; exit 90; }}
curl() {{ echo UNEXPECTED_DOWNLOAD; exit 91; }}
lab_main {args} --state-dir {shlex.quote(str(self.state))}''')
            self.assertNotIn('UNEXPECTED', result.stdout)
            self.assertFalse(self.state.exists())

    def test_reader_menu_matches_readme_and_names_the_controller_image(self):
        readme = (ROOT / 'README.md').read_text()
        labels = ('1. Install and run the demo', '2. Build the demo and installer',
                  '3. Prepare tools to rebuild the controller image or simulator')
        for choice, component in (('1\n', None), ('2\n', None),
                                  ('3\n1\n', 'ARM64 virtual controller image (Factory)'),
                                  ('3\n2\n', 'Vehicle simulator (CARLA / Unreal)')):
            result = self.shell(f'''uname() {{ echo UNEXPECTED_PROBE; exit 90; }}
curl() {{ echo UNEXPECTED_DOWNLOAD; exit 91; }}
lab_main --plan --state-dir {shlex.quote(str(self.state))}''', input=choice)
            for label in labels:
                self.assertIn(label, readme)
                self.assertIn(label, result.stdout)
            if component:
                self.assertIn(component, readme)
                self.assertIn(component, result.stdout)
                self.assertIn('no build is started', result.stdout)
            self.assertNotIn('UNEXPECTED', result.stdout)
            self.assertFalse(self.state.exists())
        self.assertLess(readme.index('**Factory image**'), readme.index(labels[2]))

    def test_bad_option_or_wrong_route_stops_before_host_access(self):
        for args in ('--oops', '--route D', '--route', '--parent', '--route A --prepare-only',
                     '--route B --dmg /file', '--route A --component factory', '--route A --xcode /Xcode.app',
                     '--route C --component wrong', '--route B --check --plan'):
            result = self.shell('uname() { echo UNEXPECTED_HOST; }; lab_main ' + args, ok=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('UNEXPECTED_HOST', result.stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_menu_and_remembered_specialist_selection_are_data(self):
        state = shlex.quote(str(self.state))
        self.shell(f'LAB_STATE={state}; lab_state; printf "C:simulator\\n" > "$LAB_STATE/last-route"; chmod 600 "$LAB_STATE/last-route"')
        result = self.shell(f'lab_main --plan --state-dir {state}', input='\n')
        self.assertIn('route C simulator', result.stdout)
        self.assertIn('full-source qualification remain separate', result.stdout)
        (self.state/'last-route').write_text('$(touch bad)')
        result = self.shell(f'lab_main --plan --state-dir {state}', input='\n', ok=False)
        self.assertIn('Invalid saved route', result.stderr)

    def test_uncached_check_never_downloads_or_creates_state(self):
        result = self.shell(f'''LAB_STATE={shlex.quote(str(self.state))}; LAB_MODE=check
curl() {{ echo UNEXPECTED_DOWNLOAD; exit 91; }}
lab_fetch developer''', ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('UNEXPECTED', result.stdout)
        self.assertFalse(self.state.exists())

    def fetch_body(self, corrupt=False):
        source = self.root/'payload'
        source.write_bytes(b'corrupt' if corrupt else DEVELOPER.read_bytes())
        return f'''LAB_STATE={shlex.quote(str(self.state))}; LAB_MODE=run; LAB_LOCKED=no; LAB_FETCH_PID=; LAB_FETCH_TMP=
lab_state; trap lab_cleanup EXIT; lab_lock
curl() {{ local out; while [ "$#" -gt 0 ]; do if [ "$1" = --output ]; then out=$2; shift; fi; shift; done
printf x >> {shlex.quote(str(self.root/'calls'))}; cp {shlex.quote(str(source))} "$out"; }}
lab_fetch developer
'''

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_first_fetch_repeat_and_scratch_cleanup(self):
        body = self.fetch_body()
        self.shell(body)
        self.shell(body)
        self.assertEqual((self.root/'calls').read_text(), 'x')
        self.assertFalse((self.state/'active').exists())
        self.assertEqual([x.name for x in (self.state/'.tmp').iterdir()], ['.owner'])
        cached = next(p for p in (self.state/'modules').iterdir() if p.name.startswith('developer-'))
        self.assertEqual(hashlib.sha256(cached.read_bytes()).hexdigest(), hashlib.sha256(DEVELOPER.read_bytes()).hexdigest())

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_corrupt_download_and_changed_cache_are_never_executed(self):
        result = self.shell(self.fetch_body(corrupt=True), ok=False)
        self.assertIn('checksum or size differs', result.stderr)
        self.assertFalse(any(x.name.startswith('developer-') for x in (self.state/'modules').iterdir()))
        self.assertFalse((self.state/'active').exists())
        self.shell(self.fetch_body())
        cached = next(p for p in (self.state/'modules').iterdir() if p.name.startswith('developer-'))
        cached.write_bytes(b'changed')
        calls = (self.root/'calls').read_bytes()
        result = self.shell(self.fetch_body(), ok=False)
        self.assertIn('Changed helper cache', result.stderr)
        self.assertEqual((self.root/'calls').read_bytes(), calls)
        self.assertEqual(cached.read_bytes(), b'changed')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_active_or_foreign_lease_is_preserved(self):
        state = shlex.quote(str(self.state))
        result = self.shell(f'LAB_STATE={state}; lab_state; lab_lock; lab_lock', ok=False)
        self.assertIn('Another launcher', result.stderr)
        self.assertTrue((self.state/'active/pid').exists())
        (self.state/'active/pid').write_text('999999999\n')
        (self.state/'active/foreign').write_text('keep')
        result = self.shell(f'LAB_STATE={state}; lab_lock', ok=False)
        self.assertIn('Unexpected lease contents', result.stderr)
        self.assertEqual((self.state/'active/foreign').read_text(), 'keep')

    def test_symlinked_state_is_rejected(self):
        (self.root/'link').symlink_to(self.root)
        result = self.shell(f'LAB_STATE={shlex.quote(str(self.root/"link/state"))}; lab_state', ok=False)
        self.assertIn('unsafe', result.stderr.lower())
        self.assertFalse(self.state.exists())

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_cancel_transfer_closes_its_process_group_and_scratch(self):
        pidfile = self.root/'child'
        body = f'''source {shlex.quote(str(ENTRY))}
LAB_STATE={shlex.quote(str(self.state))}; LAB_MODE=run; LAB_FETCH_PID=; LAB_FETCH_TMP=; LAB_LOCKED=no
lab_state; trap lab_cleanup EXIT; trap 'exit 143' TERM; lab_lock
curl() {{ exec /bin/sh -c 'printf "%s" "$$" > "$1"; exec sleep 30' _ {shlex.quote(str(pidfile))}; }}
lab_fetch developer
'''
        process = subprocess.Popen(['/bin/bash', '-c', body], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for _ in range(100):
                if pidfile.exists() and pidfile.read_text(): break
                time.sleep(.02)
            self.assertTrue(pidfile.exists())
            # Exact fixture PID, without whole-host process-list permission.
            child_pid = int(pidfile.read_text())
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=8)
            self.assertEqual(process.returncode, 143)
            with self.assertRaises(ProcessLookupError): os.kill(child_pid, 0)
            self.assertFalse((self.state/'active').exists())
            self.assertEqual([p.name for p in (self.state/'.tmp').iterdir()], ['.owner'])
        finally:
            if process.poll() is None:
                process.terminate(); process.communicate(timeout=8)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_common_import_restores_its_storage_guard_after_library_source(self):
        result = self.shell('route_import; route_recheck() { printf "CURRENT_GUARD\\n"; }; recheck_storage', script=COMMON)
        self.assertIn('CURRENT_GUARD', result.stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_install_verify_first_repeat_and_changed_file(self):
        dmg = self.root/'small fixture.dmg'
        dmg.write_bytes(b'fixture-one')
        expected = hashlib.sha256(dmg.read_bytes()).hexdigest()
        self.state.mkdir(); work = self.root/'work'; work.mkdir()
        body = f'''install_import; umask 077
STATE={shlex.quote(str(self.state))}; ROUTE_WORK={shlex.quote(str(work))}
run_install() {{ shift; printf 'HASHED\\n'; "$@"; }}
install_verify_dmg {shlex.quote(str(dmg))} 11 {expected}
'''
        self.assertIn('HASHED', self.shell(body, script=INSTALL).stdout)
        repeated = self.shell(body, script=INSTALL)
        self.assertIn('reusing unchanged', repeated.stdout)
        self.assertNotIn('HASHED', repeated.stdout)
        dmg.write_bytes(b'fixture-two')
        result = self.shell(body, script=INSTALL, ok=False)
        self.assertIn('checksum differs', result.stderr)
        self.assertEqual(dmg.read_bytes(), b'fixture-two')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_install_wrong_size_or_link_never_hashes_or_mounts(self):
        dmg = self.root/'fixture.dmg'; dmg.write_bytes(b'bad')
        (self.root/'link.dmg').symlink_to(dmg)
        for path, size in ((dmg, 8), (self.root/'link.dmg', 3)):
            result = self.shell(f'''install_import; STATE=/not-used; ROUTE_WORK=/not-used
run_install() {{ echo UNEXPECTED_HASH; }}
install_verify_dmg {shlex.quote(str(path))} {size} {'a'*64}''', script=INSTALL, ok=False)
            self.assertNotIn('UNEXPECTED_HASH', result.stdout)
            self.assertIn('DMG path or size', result.stderr)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_install_check_has_no_developer_tools_or_installer_action(self):
        result = self.shell('''install_import; install_import() { :; }
route_host() { :; }; install_docker() { :; }
discover() { echo UNEXPECTED_DEVELOPER_TOOLS; exit 90; }
route_context() { echo UNEXPECTED_WRITE; exit 90; }
install_mount() { echo UNEXPECTED_MOUNT; exit 90; }
install_main --check''', script=INSTALL)
        self.assertIn('LOCAL HOST CHECKS PASS', result.stdout)
        self.assertNotIn('UNEXPECTED', result.stdout)
        self.assertFalse(self.state.exists())

    def heavy_fixture(self):
        return f'''heavy_import; heavy_import() {{ :; }}
route_host() {{ :; }}; route_storage() {{ SDV_ROOT={shlex.quote(str(self.root))}; }}
heavy_discover() {{ XCODE_OK=yes; SDV_CMAKE=/fixture/cmake; PYTHON_OK=yes; }}
heavy_ninja() {{ :; }}; heavy_qemu() {{ :; }}
route_context() {{ :; }}; route_recheck() {{ :; }}
heavy_save_parent() {{ :; }}
prepare_python_cmake() {{ echo REUSED_TOOLS; }}
'''

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_heavy_reuses_tools_and_remains_explicitly_partial(self):
        for component in ('factory', 'simulator'):
            result = self.shell(self.heavy_fixture() + f'heavy_main --component {component} --parent /fixture',
                                script=HEAVY, input='yes\n', ok=False)
            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            self.assertIn('HOST TOOLS PREPARED — FULL SOURCE NOT READY', result.stdout)
            self.assertIn('REUSED_TOOLS', result.stdout)
            label = ('ARM64 virtual controller image (Factory)' if component == 'factory'
                     else 'Vehicle simulator (CARLA / Unreal)')
            self.assertIn(label, result.stdout)
            self.assertIn('No controller image, simulator or DMG was built.', result.stdout)
            self.assertFalse(self.state.exists())

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_heavy_read_only_check_and_decline_never_prepare(self):
        for suffix, answer in (('--check', ''), ('', 'no\n')):
            result = self.shell(self.heavy_fixture() + f'heavy_main --component factory --parent /fixture {suffix}',
                                script=HEAVY, input=answer, ok=False)
            self.assertNotIn('REUSED_TOOLS', result.stdout)
            self.assertEqual(result.returncode, 0 if suffix else 2)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_incompatible_qemu_bottle_never_installs(self):
        self.root.joinpath('qemu.json').write_text('{}')
        result = self.shell(f'''heavy_import
ROUTE_WORK={shlex.quote(str(self.root))}; BREW=/fixture/brew
need_brew() {{ :; }}
/fixture/brew() {{ printf '{{}}'; }}
/usr/bin/plutil() {{ echo wrong-version; }}
route_field() {{ echo 11.0.3; }}
install_formula() {{ echo UNEXPECTED_INSTALL; exit 90; }}
heavy_install_qemu''', script=HEAVY, ok=False)
        self.assertNotIn('UNEXPECTED', result.stdout)
        self.assertIn('does not match the pinned', result.stderr)

    def test_dispatch_fetches_only_the_selected_graph_and_preserves_arguments(self):
        for route, component, roles in (('A', '', ['developer', 'catalog', 'common', 'drive-parser', 'install']),
                                        ('B', '', ['developer']),
                                        ('C', 'factory', ['developer', 'catalog', 'common', 'heavy'])):
            result = self.shell(f'''LAB_ROUTE={route}; LAB_COMPONENT={component}; LAB_MODE=check
LAB_PARENT='/workspace with spaces'; LAB_DMG=; LAB_XCODE=; LAB_PREPARE_ONLY=no
LAB_STATE={shlex.quote(str(self.state))}
lab_fetch() {{ printf 'FETCH:%s\\n' "$1"; LAB_FETCHED="/fixture/$1"; }}
lab_execute() {{ printf 'ARG:%s\\n' "$@"; }}
lab_dispatch''')
            self.assertEqual(re.findall(r'^FETCH:(.*)$', result.stdout, re.M), roles)
            self.assertIn('ARG:/workspace with spaces', result.stdout)
            self.assertIn('ARG:--check', result.stdout)

    def test_drive_head_does_not_apply_html_payload_limit(self):
        text=INSTALL.read_text()
        head=text.split('--head',1)[1].split('|| return 1',1)[0]
        self.assertNotIn('--max-filesize',head)
        self.assertIn('--max-filesize 65536',text.split('html)',1)[1].split('binary)',1)[0])
        self.assertIn('--max-filesize "$size"',text.split('binary)',1)[1])

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_mount_tracks_borrowed_and_new_media_separately(self):
        dmg = self.root/'fixture.dmg'; dmg.write_bytes(b'fixture')
        before = self.root/'before.plist'; mounted = self.root/'mounted.plist'
        mounted.write_bytes(plistlib.dumps({'system-entities': [
            {'dev-entry': '/dev/disk999'}, {'dev-entry': '/dev/disk999s1', 'mount-point': '/Volumes/unit-only'}]}))
        for borrowed in (False, True):
            before.write_bytes(plistlib.dumps({'images': [{'image-path': str(dmg)}] if borrowed else []}))
            result = self.shell(f'''install_import; ROUTE_WORK={shlex.quote(str(self.root))}
ROUTE_MEDIA=; ROUTE_MEDIA_NEW=no
hdiutil() {{ case "$1" in info) /bin/cat {shlex.quote(str(before))} ;; attach) /bin/cat {shlex.quote(str(mounted))} ;; *) exit 90 ;; esac; }}
install_mount {shlex.quote(str(dmg))}
printf 'OWNED:%s\\n' "$ROUTE_MEDIA_NEW"''', script=INSTALL)
            self.assertIn('OWNED:' + ('no' if borrowed else 'yes'), result.stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_only_owned_pre_handoff_media_is_detached(self):
        for owned, handoff, detached in (('no', 'no', False), ('yes', 'yes', False), ('yes', 'no', True)):
            receipt = self.root/'detached'
            if receipt.exists(): receipt.unlink()
            self.shell(f'''route_import
ROUTE_MEDIA=/dev/disk999; ROUTE_MEDIA_NEW={owned}; ROUTE_HANDOFF={handoff}
ROUTE_WORK=; LOCKED=no; CHILD_PID=
hdiutil() {{ printf x > {shlex.quote(str(receipt))}; }}
true; route_cleanup''', script=COMMON)
            self.assertEqual(receipt.exists(), detached)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_setup_signature_pin_and_handoff_do_not_claim_installation(self):
        mount = self.root/'mount'
        catalog = json.loads(CATALOG.read_bytes())['operator']
        app = mount/catalog['setupBundle']; leaf=app/'Contents/Resources/tooling/scripts/distribution/setup_release.json'
        leaf.parent.mkdir(parents=True); leaf.write_text(json.dumps({'manifestSha256': catalog['manifestSha256']}))
        (mount/catalog['kitDirectory']).mkdir()
        for team in (catalog['setupTeam'], 'WRONGTEAM0'):
            result = self.shell(f'''install_import; INSTALL_MOUNT={shlex.quote(str(mount))}; ROUTE_HANDOFF=no
/usr/bin/codesign() {{ if [ "$1" = -dvv ]; then printf 'Identifier={catalog['setupIdentifier']}\\nTeamIdentifier={team}\\n'; fi; }}
/usr/bin/open() {{ printf 'OPEN_REQUESTED\\n'; }}
install_setup''', script=INSTALL, ok=(team == catalog['setupTeam']))
            if team == catalog['setupTeam']:
                self.assertIn('OPEN_REQUESTED', result.stdout)
                self.assertIn('not yet verified installed', result.stdout)
            else:
                self.assertNotIn('OPEN_REQUESTED', result.stdout)
                self.assertIn('Setup identity differs', result.stderr)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_specialist_repeat_reuses_parent_and_refuses_replaced_volume(self):
        state = self.state/'Heavy-factory'; state.mkdir(parents=True)
        selected = state/'selections.tsv'
        selected.write_text(f'parent\t{self.root}\nvolume\tfirst-volume\n'); selected.chmod(0o600)
        body = '''heavy_import
route_storage() { printf 'PARENT:%s\\n' "$1"; SELECTED_UUID=VOLUME; }
heavy_parent '' factory'''
        result = self.shell(body.replace('VOLUME', 'first-volume'), script=HEAVY)
        self.assertIn('PARENT:' + str(self.root), result.stdout)
        changed = self.shell(body.replace('VOLUME', 'another-volume'), script=HEAVY, ok=False)
        self.assertIn('different disk replaced', changed.stderr)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_missing_saved_dmg_never_prompts_or_falls_back(self):
        selected = self.state/'Install/selected-dmg'; selected.parent.mkdir(parents=True)
        selected.write_text(str(self.root/'missing.dmg')); selected.chmod(0o600)
        result = self.shell('''install_import; install_import() { :; }
route_host() { :; }; install_docker() { :; }
/usr/bin/osascript() { echo UNEXPECTED_PICKER; exit 90; }
install_main''', script=INSTALL, ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Saved DMG is unavailable', result.stdout)
        self.assertNotIn('UNEXPECTED_PICKER', result.stdout)

    def download_fixture(self, mode='complete', volume='fixture-volume'):
        """Real shell/parser/state with a nine-byte fake curl; never network/UI."""
        digest = hashlib.sha256(b'abcdefghi').hexdigest()
        parser = ROOT/'scripts/launcher/drive-download-macos.pl'
        url = 'https://drive.google.com/uc?export=download&id=public_file_123456789'
        return f'''install_import; install_import() {{ :; }}
SDV_LAB_DRIVE_PARSER={shlex.quote(str(parser))}
FIXTURE_MODE={shlex.quote(mode)}; FIXTURE_VOLUME={shlex.quote(volume)}
route_host() {{ :; }}; install_docker() {{ :; }}
route_field() {{ case "$1" in operator.bytes) echo 9 ;; operator.sha256) echo {digest} ;; operator.file) echo fixture.dmg ;; operator.downloadURL) echo {shlex.quote(url)} ;; *) echo fixture ;; esac; }}
route_storage() {{ SDV_PARENT=$1; SDV_ROOT="$1/sdv"; SDV_TMP="$SDV_ROOT/.tmp"; SELECTED_UUID=$FIXTURE_VOLUME; }}
route_context() {{ umask 077; STATE="$SDV_LAB_STATE/Install"; ROUTE_WORK={shlex.quote(str(self.root/'request'))}; mkdir -p "$STATE" "$ROUTE_WORK" "$SDV_ROOT/cache"; exec 9>&1; }}
run_install() {{ shift; "$@" || die 'Fixture transfer stopped; repeat explicitly.'; }}
install_mount() {{ echo MOUNTED; }}; install_setup() {{ echo OPENED; }}
curl() {{
  local out= headers= offset=0 head=no arg data=abcdefghi
  printf '%s ' "$@" >> {shlex.quote(str(self.root/'curl-args'))}; printf '\\n' >> {shlex.quote(str(self.root/'curl-args'))}
  while [ "$#" -gt 0 ]; do
    arg=$1; shift
    case "$arg" in --head) head=yes ;; --output) out=$1; shift ;; --dump-header) headers=$1; shift ;; --continue-at) offset=$1; shift ;; esac
  done
  if [ "$head" = yes ]; then printf 'HTTP/2 200\\r\\nContent-Type: application/octet-stream\\r\\nContent-Length: 9\\r\\n\\r\\n' > "$out"; return; fi
  printf 'GET:%s\\n' "$offset" >> {shlex.quote(str(self.root/'gets'))}
  if [ "$offset" = 0 ]; then printf 'HTTP/2 200\\r\\n'; else printf 'HTTP/2 206\\r\\nContent-Range: bytes %s-8/9\\r\\n' "$offset"; fi > "$headers"
  printf 'Content-Type: application/octet-stream\\r\\nContent-Length: %s\\r\\n\\r\\n' "$((9-offset))" >> "$headers"
  case "$FIXTURE_MODE" in
    interrupt) printf abcd >> "$out"; return 18 ;;
    terminate) printf abcd >> "$out"; kill -TERM $$; return 99 ;;
    wrong-range) printf 'HTTP/2 206\\r\\nContent-Type: application/octet-stream\\r\\nContent-Range: bytes 4-8/99\\r\\nContent-Length: 5\\r\\n\\r\\n' > "$headers" ;;
    ignored-range) printf 'HTTP/2 200\\r\\nContent-Type: application/octet-stream\\r\\nContent-Length: 9\\r\\n\\r\\n' > "$headers" ;;
    html) printf 'HTTP/2 200\\r\\nContent-Type: text/html\\r\\n\\r\\n' > "$headers"; printf "Sorry, you can not download: quota exceeded" >> "$out"; return 0 ;;
    oversized) printf efghij >> "$out"; return 0 ;;
    collision) printf foreign > {shlex.quote(str(self.root/'sdv/cache/fixture.dmg'))} ;;
  esac
  printf '%s' "${{data:$offset}}" >> "$out"
}}
'''

    def run_download(self, mode='complete', volume='fixture-volume', first=False, ok=True):
        suffix = ' --parent ' + shlex.quote(str(self.root)) if first else ''
        return self.shell(self.download_fixture(mode, volume) + 'install_main' + suffix,
                          script=INSTALL, input='yes\n', ok=ok)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_download_interrupt_resume_then_verified_handoff(self):
        first = self.run_download('interrupt', first=True, ok=False)
        part = self.root/'sdv/cache/fixture.dmg.part'
        self.assertNotEqual(first.returncode, 0)
        self.assertEqual(part.read_bytes(), b'abcd')
        self.assertNotIn('OPENED', first.stdout)
        second = self.run_download()
        self.assertIn('Previously selected DMG', second.stdout)
        self.assertIn('OPENED', second.stdout)
        self.assertEqual((self.root/'sdv/cache/fixture.dmg').read_bytes(), b'abcdefghi')
        self.assertEqual((self.root/'gets').read_text().splitlines(), ['GET:0', 'GET:4'])
        self.assertFalse(part.exists())
        self.assertFalse(part.with_name(part.name+'.receipt').exists())
        gets = (self.root/'gets').read_text()
        self.run_download()
        self.assertEqual((self.root/'gets').read_text(), gets)
        transfer = [r for r in (self.root/'curl-args').read_text().splitlines() if '--dump-header' in r]
        self.assertTrue(all('--speed-time 90' in r and '--max-time' not in r for r in transfer))

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_download_process_loss_is_resumable(self):
        lost = self.run_download('terminate', first=True, ok=False)
        self.assertNotEqual(lost.returncode, 0)
        self.assertIn('OPENED', self.run_download().stdout)
        self.assertEqual((self.root/'gets').read_text().splitlines(), ['GET:0', 'GET:4'])

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_bad_ranges_rollback_only_new_bytes(self):
        self.run_download('interrupt', first=True, ok=False)
        part = self.root/'sdv/cache/fixture.dmg.part'
        for mode in ('wrong-range', 'ignored-range', 'oversized'):
            result = self.run_download(mode, ok=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('OPENED', result.stdout)
            self.assertEqual(part.read_bytes(), b'abcd')
        self.assertIn('OPENED', self.run_download().stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_quota_html_never_becomes_retained_media(self):
        result = self.run_download('html', first=True, ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('OPENED', result.stdout)
        self.assertEqual((self.root/'sdv/cache/fixture.dmg.part').read_bytes(), b'')
        self.assertIn('quota exceeded', result.stdout+result.stderr)
        self.assertIn('OPENED', self.run_download().stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_replaced_volume_and_payload_identity_stop_before_network(self):
        self.run_download('interrupt', first=True, ok=False)
        calls = (self.root/'gets').read_text()
        result = self.run_download(volume='replacement-volume', ok=False)
        self.assertIn('volume was replaced', result.stderr)
        self.assertEqual((self.root/'gets').read_text(), calls)
        part = self.root/'sdv/cache/fixture.dmg.part'
        part.rename(part.with_name('retained-original'))
        part.write_bytes(b'abcd'); part.chmod(0o600)
        result = self.run_download(ok=False)
        self.assertIn('another package, file or volume', result.stderr)
        self.assertEqual((self.root/'gets').read_text(), calls)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_changed_prefix_is_rejected_by_full_checksum(self):
        self.run_download('interrupt', first=True, ok=False)
        part = self.root/'sdv/cache/fixture.dmg.part'
        part.write_bytes(b'Zbcd')
        result = self.run_download(ok=False)
        self.assertIn('checksum differs', result.stderr)
        self.assertNotIn('MOUNTED', result.stdout)
        self.assertNotIn('OPENED', result.stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_unknown_partial_and_late_destination_are_preserved(self):
        part = self.root/'sdv/cache/fixture.dmg.part'
        part.parent.mkdir(parents=True); part.write_bytes(b'foreign'); part.chmod(0o600)
        result = self.run_download(first=True, ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(part.read_bytes(), b'foreign')
        self.assertFalse((self.root/'gets').exists())
        part.unlink()  # only this test's exact fixture
        result = self.run_download('collision', ok=False)
        self.assertIn('both files preserved', result.stderr)
        self.assertEqual((self.root/'sdv/cache/fixture.dmg').read_bytes(), b'foreign')
        self.assertEqual(part.read_bytes(), b'abcdefghi')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_complete_partial_needs_no_second_transfer(self):
        self.run_download('interrupt', first=True, ok=False)
        (self.root/'sdv/cache/fixture.dmg.part').write_bytes(b'abcdefghi')
        calls = (self.root/'gets').read_text()
        self.assertIn('OPENED', self.run_download().stdout)
        self.assertEqual((self.root/'gets').read_text(), calls)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_changed_package_or_unsafe_receipt_never_transfers(self):
        self.run_download('interrupt', first=True, ok=False)
        calls = (self.root/'gets').read_text()
        record = self.state/'Install/download-selection'
        original = record.read_text()
        record.write_text(original.replace(hashlib.sha256(b'abcdefghi').hexdigest(), 'a'*64))
        result = self.run_download(ok=False)
        self.assertIn('selection differs', result.stderr)
        self.assertEqual((self.root/'gets').read_text(), calls)
        record.write_text(original)
        receipt = self.root/'sdv/cache/fixture.dmg.part.receipt'
        receipt.write_text('x'*513+'\n')
        result = self.run_download(ok=False)
        self.assertIn('unsafe partial', result.stderr)
        self.assertEqual((self.root/'gets').read_text(), calls)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS metadata and plutil')
    def test_operator_explicit_new_parent_recovers_legacy_missing_selection(self):
        selected = self.state/'Install/selected-dmg'; selected.parent.mkdir(parents=True)
        missing = self.root/'legacy-missing.dmg'
        selected.write_text(str(missing)); selected.chmod(0o600)
        self.assertIn('OPENED', self.run_download(first=True).stdout)
        self.assertFalse(missing.exists())

    def test_delegate_receives_interactive_input_and_exact_exit_status(self):
        child = self.root/'delegate.sh'
        child.write_text('read -r answer\nprintf "INPUT:%s\\n" "$answer"\nexit 2\n')
        result = self.shell('LAB_ROUTE_PID=; lab_execute ' + shlex.quote(str(child)), input='yes\n', ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('INPUT:yes', result.stdout)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS lease metadata')
    def test_cancel_delegate_releases_launcher_lease(self):
        child = self.root/'delegate.sh'
        pidfile = self.root/'delegate-pid'
        child.write_text('printf "%s" "$$" > ' + shlex.quote(str(pidfile)) + '\nexec sleep 30\n')
        body = f'''source {shlex.quote(str(ENTRY))}
LAB_STATE={shlex.quote(str(self.state))}; LAB_LOCKED=no; LAB_FETCH_PID=; LAB_FETCH_TMP=; LAB_ROUTE_PID=
lab_state; trap lab_cleanup EXIT; trap 'exit 143' TERM; lab_lock
lab_execute {shlex.quote(str(child))}
'''
        process = subprocess.Popen(['/bin/bash', '-c', body], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for _ in range(100):
                if pidfile.exists() and pidfile.read_text(): break
                time.sleep(.02)
            self.assertTrue(pidfile.exists())
            delegate = int(pidfile.read_text())
            process.send_signal(signal.SIGTERM); process.communicate(timeout=8)
            with self.assertRaises(ProcessLookupError): os.kill(delegate, 0)
            self.assertFalse((self.state/'active').exists())
        finally:
            if process.poll() is None:
                process.terminate(); process.communicate(timeout=8)


if __name__ == '__main__':
    unittest.main()

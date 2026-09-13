# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""One authorized Test32 CM A/B/A experiment, not a presentation operation."""

import json
import base64
import gzip
import hashlib
from pathlib import Path
import shlex
import subprocess
import sys

from .component_runtime import builder_ssh, builder, BUILDER_PROJECT, SOURCE, ARTIFACT
from .environment import EnvironmentError, JOURNAL, atomic_json, factory_for
from .status import now, read_json

WORK = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-communicationmanager/git"
PATCH = "0002-reconcile-stale-instance-snapshot.patch"
INSTALLED = "85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d"
OUTPUT = ARTIFACT.with_name("cm-comparison-20260912")
REFRESH_OUTPUT = ARTIFACT.with_name("cm-idle-full-status-20260913")
REFRESH_VM = "c7b8f9d8-68ea-4b65-b444-8b01595eb110"
REFRESH_UNIT = "d90798f6-a32c-40cc-8129-26a0f1343a67"


def build_idle_refresh():
    """Compile the approved CM-only proof from the warm .32 source, offline."""
    paths = {
        "aos_core_lib_cpp": ["src/core/cm/updatemanager/" + name for name in (
            "config.hpp", "desiredstatushandler.cpp", "unitstatushandler.hpp", "unitstatushandler.cpp",
            "tests/updatemanager.cpp", "tests/stubs/senderstub.hpp")],
        "aos_core_cpp": ["src/cm/" + name for name in (
            "config/config.hpp", "config/config.cpp", "config/tests/config.cpp", "app/aoscore.cpp")],
    }
    files = []
    for repository, names in paths.items():
        root = SOURCE / "build" / repository
        for name in names:
            before = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=root)
            after = (root / name).read_bytes()
            prefix = "git/" if repository == "aos_core_cpp" else "service-update-deps/aos_core_lib_cpp/"
            files.append(dict(path=prefix + name, before=base64.b64encode(before).decode(),
                after=base64.b64encode(after).decode(), sha256=hashlib.sha256(after).hexdigest()))
    REFRESH_OUTPUT.mkdir(mode=0o700, parents=True, exist_ok=True)
    existing = read_json(REFRESH_OUTPUT / "manifest.json") if (REFRESH_OUTPUT / "manifest.json").exists() else {}
    if existing:
        if existing.get("inputs") != [dict(path=f["path"], sha256=f["sha256"]) for f in files]:
            raise EnvironmentError("CM_REFRESH_SOURCE_CHANGED_AFTER_QUALIFIED_BUILD")
        return dict(existing, noOp=True)
    import tempfile
    attempt = Path(tempfile.mkdtemp(prefix="build-", dir=REFRESH_OUTPUT))
    payload = dict(work=WORK, output=BUILDER_PROJECT + "/cm-idle-full-status-" + attempt.name,
        files=files, installed=INSTALLED)
    atomic_json(attempt / "intent.json", dict(startedAt=now(), state="BUILD_STARTED",
        files=[dict(path=f["path"], sha256=f["sha256"]) for f in files]))
    script = r'''
import base64, hashlib, json, os, shlex, shutil, subprocess, sys
from pathlib import Path
c=json.load(sys.stdin); p=Path(c['work']); out=Path(c['output'])
assert not out.exists(), 'attempt already exists'
assert hashlib.sha256((p/'package/usr/bin/aos_cm_app').read_bytes()).hexdigest()==c['installed']
original={}
for item in c['files']:
 f=p/item['path']; expected=base64.b64decode(item['before'])
 assert f.read_bytes()==expected, 'warm baseline mismatch: '+item['path']
 original[f]=expected
out.mkdir(mode=0o700)
cache=dict((x.split(':',1)[0],x.split('=',1)[1]) for x in (p/'build/CMakeCache.txt').read_text().splitlines() if ':' in x and '=' in x and not x.startswith(('#','//')))
run=(p/'temp/run.do_compile').read_text(); assert run.count('\ndo_compile\n')==1
env=os.environ.copy()
env['PATH']=shlex.split(next(x for x in run.splitlines() if x.startswith('export PATH=')))[1].split('=',1)[1]
def logged(name, args, **kwargs):
 with (out/(name+'.log')).open('wb') as log:
  result=subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=300, env=env, **kwargs)
 if result.returncode:
  print(json.dumps(dict(state='FAILED',stage=name,tail=(out/(name+'.log')).read_text()[-6000:])))
  raise RuntimeError('target failed: '+name)
try:
 for item in c['files']: (p/item['path']).write_bytes(base64.b64decode(item['after']))
 compile_script=run.replace('\ndo_compile\n','\ncmake --build '+str(p/'build')+' --target aos_cm_app aos_cm_config_test -- -j6\n')
 logged('cm-build',['bash','-s'], input=compile_script.encode())
 tests=p/'service-update-launcher-tests'
 logged('test-configure',[cache['CMAKE_COMMAND'],'-S',str(p/'service-update-deps/aos_core_lib_cpp'),'-B',str(tests),'-G',cache['CMAKE_GENERATOR'],'-DCMAKE_MAKE_PROGRAM='+cache['CMAKE_MAKE_PROGRAM'],'-DWITH_TEST=ON','-DWITH_MBEDTLS=OFF','-DWITH_OPENSSL=OFF','-DFETCHCONTENT_FULLY_DISCONNECTED=ON','-DCMAKE_GTEST_DISCOVER_TESTS_DISCOVERY_MODE=PRE_TEST','-DCMAKE_TOOLCHAIN_FILE='+str(p/'toolchain.cmake')])
 logged('test-build',[cache['CMAKE_COMMAND'],'--build',str(tests),'--target','aos_core_cm_updatemanager_test','--parallel','6'])
 loader=p/'recipe-sysroot/usr/lib/ld-linux-aarch64.so.1'
 libs=str(p/'recipe-sysroot/lib')+':'+str(p/'recipe-sysroot/usr/lib')
 for name,root,filename in (('update-tests',tests,'aos_core_cm_updatemanager_test'),('config-tests',p/'build','aos_cm_config_test')):
  matches=list(root.rglob(filename)); assert len(matches)==1
  logged(name,[str(loader),'--library-path',libs,str(matches[0])])
  assert '[  PASSED  ]' in (out/(name+'.log')).read_text()
  assert '[  SKIPPED ]' not in (out/(name+'.log')).read_text()
 binary=out/'aos_cm_app'; shutil.copyfile(p/'build/src/cm/app/aos_cm_app',binary)
 subprocess.run([cache['CMAKE_STRIP'],'--strip-unneeded',str(binary)],check=True,capture_output=True,env=env)
 raw=binary.read_bytes(); assert raw[:6]==b'\x7fELF\x02\x01' and raw[18:20]==b'\xb7\x00'
 manifest=dict(state='BUILT_TESTED',executableSha256=hashlib.sha256(raw).hexdigest(),sizeBytes=len(raw),installedBaselineSha256=c['installed'],idleFullStatusInterval='60s',defaultInterval='0s',tests=['updatemanager','cm-config'],testSummary=[line for name in ('update-tests','config-tests') for line in (out/(name+'.log')).read_text().splitlines() if '[  PASSED  ]' in line])
finally:
 for f,raw in original.items(): f.write_bytes(raw)
manifest.update(warmSourceRestored=True,fullImageBuilt=False)
(out/'manifest.json').write_text(json.dumps(manifest))
print(json.dumps(manifest))
'''
    print("Test32: compile CM and focused status/config tests; no image build", file=sys.stderr, flush=True)
    try:
        proc = subprocess.run(builder_ssh() + ["python3 -c " + shlex.quote(script)],
            input=json.dumps(payload).encode(), capture_output=True, timeout=900)
        (attempt / "build.log").write_bytes(proc.stdout + proc.stderr)
        if proc.returncode:
            raise EnvironmentError("CM_REFRESH_BUILD_FAILED:" + str(attempt / "build.log"))
        manifest = json.loads(proc.stdout)
        raw = subprocess.check_output(builder_ssh() + ["cat " + payload["output"] + "/aos_cm_app"], timeout=25)
        if hashlib.sha256(raw).hexdigest() != manifest["executableSha256"]:
            raise EnvironmentError("CM_REFRESH_TRANSFER_DIGEST_MISMATCH")
        (REFRESH_OUTPUT / "aos_cm_app").write_bytes(raw)
        manifest.update(preparedAt=now(), inputs=[dict(path=f["path"],sha256=f["sha256"]) for f in files])
        atomic_json(REFRESH_OUTPUT / "manifest.json", manifest)
        return manifest
    finally:
        builder("test", "stop")


def apply_idle_refresh(environment):
    from .source import SourceDriver
    from .vm import VMService
    with environment._writer():
        state = read_json(environment.root / JOURNAL)
        vehicle = state.get("vehicles", {}).get("test", {})
        if (vehicle.get("localVmId") != REFRESH_VM or vehicle.get("unitId") != REFRESH_UNIT
                or factory_for(state, "test").get("sha256") !=
                "f56e037ff6ce11d1dea769055dc160a5a9a8061bbdd2d67745a3042181be2f14"):
            raise EnvironmentError("CM_REFRESH_REQUIRES_CURRENT_TEST_32")
        prior = state.get("cmIdleFullStatusProof", {})
        if prior:
            if prior.get("state") == "COMPLETED":
                return dict(prior["result"], noOp=True)
            raise EnvironmentError("CM_REFRESH_RECONCILE_EXISTING_ATTEMPT")
        manifest = read_json(REFRESH_OUTPUT / "manifest.json")
        if manifest.get("state") != "BUILT_TESTED" or manifest.get("installedBaselineSha256") != INSTALLED:
            raise EnvironmentError("CM_REFRESH_TESTED_BUILD_REQUIRED")
        raw = (REFRESH_OUTPUT / "aos_cm_app").read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["executableSha256"]:
            raise EnvironmentError("CM_REFRESH_ARTIFACT_DIGEST_MISMATCH")
        record = dict(state="ATTEMPT_STARTED", startedAt=now(), sha256=manifest["executableSha256"])
        state["cmIdleFullStatusProof"] = record
        atomic_json(environment.root / JOURNAL, state)
        driver = SourceDriver(VMService(environment))
        try:
            with driver.operation(timeout=70):
                result = driver.guest(state, "test", "component-cm-apply", target="test",
                    proof="factory32-idle-full-status", restartCm=True, sha256=manifest["executableSha256"],
                    binary=base64.b64encode(gzip.compress(raw, mtime=0)).decode())
        except (EnvironmentError, OSError, ValueError, subprocess.SubprocessError):
            record["state"] = "RECONCILIATION_REQUIRED"
            atomic_json(environment.root / JOURNAL, state)
            raise EnvironmentError("CM_REFRESH_RECONCILE_EXISTING_ATTEMPT") from None
        record.update(state="COMPLETED", result=result, confirmedAt=now())
        atomic_json(environment.root / JOURNAL, state)
        return result


def restore_idle_refresh_cache():
    """Restore the warm recipe's compiled CM, not the running Test proof."""
    manifest = read_json(REFRESH_OUTPUT / "manifest.json")
    if not manifest.get("warmSourceRestored"):
        raise EnvironmentError("CM_REFRESH_SOURCE_RECONCILIATION_REQUIRED")
    if manifest.get("warmCompiledBaselineRestored"):
        return dict(state="RESTORED", noOp=True)
    script = r'''
import hashlib,json,struct,subprocess,sys
from pathlib import Path
p=Path(sys.argv[1]); out=Path(sys.argv[2])
assert not (out/'restore-manifest.json').exists(), 'already restored; reconcile instead'
run=(p/'temp/run.do_compile').read_text(); assert run.count('\ndo_compile\n')==1
assert b'mIdleFullStatusInterval' not in (p/'git/src/cm/config/config.hpp').read_bytes()
assert b'mIdleFullStatusInterval' not in (p/'service-update-deps/aos_core_lib_cpp/src/core/cm/updatemanager/config.hpp').read_bytes()
run=run.replace('\ndo_compile\n','\ncmake --build '+str(p/'build')+' --target aos_cm_app -- -j6\n')
out.mkdir(mode=0o700,exist_ok=True)
with (out/'restore-cache.log').open('wb') as log:
 subprocess.run(['bash','-s'],input=run.encode(),stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
binary=(p/'build/src/cm/app/aos_cm_app').read_bytes()
packaged=(p/'package/usr/bin/aos_cm_app').read_bytes()
assert hashlib.sha256(packaged).hexdigest()==sys.argv[3]
def allocated(data):
 assert data[:6]==b'\x7fELF\x02\x01' and data[18:20]==b'\xb7\x00'
 offset=struct.unpack_from('<Q',data,40)[0]; size,count=struct.unpack_from('<HH',data,58)
 result=[]
 for i in range(count):
  _,typ,flags,addr,pos,length,*_=struct.unpack_from('<IIQQQQIIQQ',data,offset+i*size)
  if flags&2: result.append((typ,flags,addr,length,hashlib.sha256(data[pos:pos+length]).hexdigest() if typ!=8 else None))
 return result
assert allocated(binary)==allocated(packaged), 'restored compiled code differs from packaged baseline'
result=dict(state='RESTORED',warmCompiledBaselineRestored=True,installedBaselineSha256=sys.argv[3])
(out/'restore-manifest.json').write_text(json.dumps(result)); print(json.dumps(result))
'''
    try:
        result = subprocess.run(builder_ssh() + ["python3 -c " + shlex.quote(script) + " "
            + WORK + " " + BUILDER_PROJECT + "/cm-idle-full-status-cache-restore " + INSTALLED],
            capture_output=True, timeout=340)
        (REFRESH_OUTPUT / "restore-cache.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise EnvironmentError("CM_REFRESH_CACHE_RESTORE_RECONCILIATION_REQUIRED")
        restored = json.loads(result.stdout)
        manifest.update(warmCompiledBaselineRestored=True, cacheRestoredAt=now())
        atomic_json(REFRESH_OUTPUT / "manifest.json", manifest)
        return restored
    finally:
        builder("test", "stop")


def build_comparison():
    """Reuse the exact warm target; change one source file, then restore it."""
    import shutil
    if shutil.disk_usage(OUTPUT.parent).free < 60 * 1024**3:
        raise EnvironmentError("CM_COMPARISON_FREE_SPACE_BELOW_60_GIB")
    if OUTPUT.exists():
        raise EnvironmentError("CM_COMPARISON_BUILD_ALREADY_ATTEMPTED")
    relative = "src/core/cm/launcher/instancemanager.cpp"
    repository = SOURCE / "build/aos_core_lib_cpp"
    before = subprocess.check_output(["git", "show", "60cb83535f773762c61ac5f544b31b7b88c502e3:" + relative], cwd=repository)
    after = (repository / relative).read_bytes()
    payload = dict(work=WORK, output=BUILDER_PROJECT + "/cm-comparison-20260912", relative=relative,
        before=base64.b64encode(before).decode(), after=base64.b64encode(after).decode(), installed=INSTALLED)
    OUTPUT.mkdir(mode=0o700)
    atomic_json(OUTPUT / "intent.json", dict(startedAt=now(), state="BUILD_STARTED", changedSource=relative,
        beforeSha256=hashlib.sha256(before).hexdigest(), afterSha256=hashlib.sha256(after).hexdigest()))
    # Run the saved Yocto compile environment, targeting only aos_cm_app.
    # No bitbake, fetch, configure, package, image or changes to layer selection.
    script = r'''
import base64, hashlib, json, os, shutil, struct, subprocess, sys
from pathlib import Path
c=json.load(sys.stdin); p=Path(c['work']); out=Path(c['output'])
assert not out.exists(), 'comparison already attempted'
assert shutil.disk_usage(p).free >= 60*1024**3, 'Builder free space below 60 GiB'
src=p/'service-update-deps/aos_core_lib_cpp'/c['relative']
before=base64.b64decode(c['before']); after=base64.b64decode(c['after'])
assert src.read_bytes()==after, 'warm source does not match the pinned patch'
binary=p/'build/src/cm/app/aos_cm_app'
packaged=p/'package/usr/bin/aos_cm_app'
assert hashlib.sha256(packaged.read_bytes()).hexdigest()==c['installed'], 'packaged baseline mismatch'
assert hashlib.sha256(binary.read_bytes()).hexdigest()=='1ee6ad0a821de89c40b4b108b25b89b8afe338fdced9b0cd6a678df0b9f93936', 'warm binary mismatch'
def allocated(data):
 assert data[:6]==b'\x7fELF\x02\x01' and data[18:20]==b'\xb7\x00'
 offset=struct.unpack_from('<Q',data,40)[0]; size,count=struct.unpack_from('<HH',data,58)
 result=[]
 for i in range(count):
  _,typ,flags,addr,pos,length,*_=struct.unpack_from('<IIQQQQIIQQ',data,offset+i*size)
  if flags&2: result.append((typ,flags,addr,length,hashlib.sha256(data[pos:pos+length]).hexdigest() if typ!=8 else None))
 return result
assert allocated(binary.read_bytes())==allocated(packaged.read_bytes()), 'installed code differs from warm binary'
cache=(p/'build/CMakeCache.txt').read_text().splitlines()
strip=next(x.split('=',1)[1] for x in cache if x.startswith('CMAKE_STRIP:FILEPATH='))
run=(p/'temp/run.do_compile').read_text()
assert run.count('\ndo_compile\n')==1
run=run.replace('\ndo_compile\n', '\ncmake --build '+str(p/'build')+' --target aos_cm_app -- -j4\n')
out.mkdir(mode=0o700)
def compile_target(name):
 with (out/(name+'.log')).open('wb') as log:
  subprocess.run(['bash','-s'],input=run.encode(),stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
result=None
try:
 src.write_bytes(before)
 compile_target('without-patch')
 shutil.copyfile(binary,out/'aos-cm-without-patch')
 subprocess.run([strip,'--strip-unneeded',str(out/'aos-cm-without-patch')],check=True,capture_output=True)
 raw=(out/'aos-cm-without-patch').read_bytes()
 assert allocated(raw)
 result=dict(executableSha256=hashlib.sha256(raw).hexdigest(),sizeBytes=len(raw),
  installedBaselineSha256=c['installed'],warmBinaryMatchesInstalledCode=True,
  removedPatch='0002-reconcile-stale-instance-snapshot.patch',changedSource=c['relative'])
finally:
 src.write_bytes(after)
 compile_target('restore-cache')
 assert src.read_bytes()==after
 assert allocated(binary.read_bytes())==allocated(packaged.read_bytes()), 'restored compile differs from baseline'
if result:
 result.update(sourceRestored=True,compiledBaselineRestored=True)
 (out/'manifest.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result))
'''
    print("Test CM comparison: compile one target without snapshot patch, then restore warm source/build", file=sys.stderr, flush=True)
    try:
        proc = subprocess.run(builder_ssh() + ["python3 -c " + shlex.quote(script)], input=json.dumps(payload).encode(),
            capture_output=True, timeout=660)
        if proc.returncode:
            # The fixed script contains no secret-bearing inputs or log output.
            (OUTPUT / "build-error.txt").write_bytes(proc.stderr[-5000:])
            raise EnvironmentError("CM_COMPARISON_BUILD_FAILED_SEE_BOUNDED_EVIDENCE")
        manifest = json.loads(proc.stdout)
        raw = subprocess.check_output(builder_ssh() + ["cat " + payload["output"] + "/aos-cm-without-patch"], timeout=25)
        if hashlib.sha256(raw).hexdigest() != manifest["executableSha256"]:
            raise EnvironmentError("CM_COMPARISON_TRANSFER_DIGEST_MISMATCH")
        (OUTPUT / "aos-cm-without-patch").write_bytes(raw)
        manifest.update(preparedAt=now(), sourceRevision="04fc8270c55ff5c35f1e98af534a5efccb035464")
        atomic_json(OUTPUT / "manifest.json", manifest)
        return manifest
    finally:
        builder("test", "stop")


def compare(environment, target, phase):
    if target != "test":
        raise EnvironmentError("CM_COMPARISON_TEST_ONLY")
    if phase == "refresh-build":
        return build_idle_refresh()
    if phase == "refresh-apply":
        return apply_idle_refresh(environment)
    if phase == "refresh-cache-restore":
        return restore_idle_refresh_cache()
    if phase == "startup":
        from .source import SourceDriver
        from .vm import VMService
        state = read_json(environment.root / JOURNAL)
        driver = SourceDriver(VMService(environment))
        with driver.operation(timeout=35):
            return driver.guest(state, "test", "component-cm-startup", target="test")
    if phase == "build":
        return build_comparison()
    if phase == "inspect":
        # Fixed build metadata and public source only; no environment/credentials.
        script = '''from pathlib import Path
import hashlib, json
p=Path(%r)
result={}
for name in ('build/CMakeCache.txt','temp/run.do_compile','temp/run.do_configure'):
 f=p/name
 result[name]=[line for line in f.read_text().splitlines() if any(k in line for k in ('AOS_CORE','AOS_API','CMAKE_HOME','CMAKE_BUILD_TYPE','CMAKE_MAKE_PROGRAM','CMAKE_STRIP','do_compile','cmake --build','ninja','oe_runmake'))] if f.exists() else None
result['binaries']=[dict(path=str(f),size=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in (p/'build').rglob('aos_cm_app') if f.is_file()]
result['sources']=[str(f) for f in p.rglob('instancemanager.cpp')]
result['packaged']=[dict(path=str(f),size=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for name in ('package/usr/bin/aos_cm_app','packages-split/aos-communicationmanager/usr/bin/aos_cm_app','image/usr/bin/aos_cm_app') if (f:=p/name).is_file()]
result['compileTail']=(p/'temp/run.do_compile').read_text().splitlines()[-18:]
print(json.dumps(result))
''' % WORK
        raw = subprocess.check_output(builder_ssh() + ["python3 -c " + shlex.quote(script)], timeout=20)
        return json.loads(raw)
    if phase not in ("control", "without-patch", "restore"):
        raise EnvironmentError("CM_COMPARISON_PHASE_NOT_PREPARED")
    from .source import SourceDriver
    from .vm import VMService
    with environment._writer():
        state = read_json(environment.root / JOURNAL)
        vehicle = state.get("vehicles", {}).get("test", {})
        if (vehicle.get("localVmId") != "5aa1f8e4-a111-4467-a6cc-fb269c62a7a8"
                or vehicle.get("unitId") != "923b9820-999b-41bb-91db-b2a2c469e743"
                or factory_for(state, "test").get("sha256") !=
                "f56e037ff6ce11d1dea769055dc160a5a9a8061bbdd2d67745a3042181be2f14"):
            raise EnvironmentError("CM_COMPARISON_REQUIRES_AUTHORIZED_TEST_32")
        proof = state.setdefault("cmComparison20260912", {})
        if phase == "without-patch" and proof.get("control", {}).get("state") != "COMPLETED":
            raise EnvironmentError("CM_COMPARISON_CONTROL_REQUIRED")
        if phase == "restore" and not proof.get("without-patch"):
            raise EnvironmentError("CM_COMPARISON_WITHOUT_PATCH_NOT_ATTEMPTED")
        extra = {}
        if phase != "control":
            manifest = read_json(OUTPUT / "manifest.json")
            if not (manifest.get("sourceRestored") and manifest.get("compiledBaselineRestored")
                    and manifest.get("installedBaselineSha256") == INSTALLED):
                raise EnvironmentError("CM_COMPARISON_QUALIFIED_BINARY_REQUIRED")
            raw = (OUTPUT / "aos-cm-without-patch").read_bytes()
            if hashlib.sha256(raw).hexdigest() != manifest["executableSha256"]:
                raise EnvironmentError("CM_COMPARISON_ARTIFACT_DIGEST_MISMATCH")
            extra = dict(phase=phase, sha256=manifest["executableSha256"])
            if phase == "without-patch":
                extra["binary"] = base64.b64encode(gzip.compress(raw, mtime=0)).decode()
        record = proof.get(phase)
        if record:
            if record.get("state") == "COMPLETED":
                return dict(record["result"], noOp=True)
            raise EnvironmentError("CM_COMPARISON_RECONCILE_EXISTING_ATTEMPT")
        record = dict(state="ATTEMPT_STARTED", startedAt=now(), phase=phase)
        proof[phase] = record
        atomic_json(environment.root / JOURNAL, state)
        driver = SourceDriver(VMService(environment))
        try:
            with driver.operation(timeout=60):
                result = driver.guest(state, "test", "component-cm-apply", target="test",
                    proof="factory32-delivery-control" if phase == "control" else "factory32-cm-comparison",
                    restartCm=True, **extra)
        except (EnvironmentError, OSError, ValueError, subprocess.SubprocessError):
            record["state"] = "RECONCILIATION_REQUIRED"
            atomic_json(environment.root / JOURNAL, state)
            raise EnvironmentError("CM_COMPARISON_RECONCILE_EXISTING_ATTEMPT") from None
        record.update(state="COMPLETED", result=result, confirmedAt=now())
        atomic_json(environment.root / JOURNAL, state)
        return result

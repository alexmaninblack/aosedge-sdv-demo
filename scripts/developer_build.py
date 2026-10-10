# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Human-facing continuation of the one-file launcher; calls existing owners."""
from contextlib import redirect_stdout, redirect_stderr
import fcntl
import io
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile
import threading

from developer_bootstrap import WorkflowError, require, safe, read, save, validate_checkout
from developer_catalog import source_check, CatalogError
from reproduction.core import LabError

ROOT = Path(__file__).resolve().parents[1]
PLAN = 'workspace/releases/1.2.0-rc.1-public-build-chain-r1.json'
INPUTS = 'workspace/releases/1.2.0-rc.1-source-factory-packaging.json'
RELEASE = 'workspace/releases/1.2.0-rc.1-source-factory-setup.json'


class OwnerOutput(io.TextIOBase):
    """Retain owner diagnostics, show only bounded progress, remember last result."""
    def __init__(self, log, screen):
        self.log, self.screen = log, screen
        self.pending, self.last = '', None

    def write(self, text):
        self.log.write(text)
        self.log.flush()
        self.pending += text
        while '\n' in self.pending:
            line, self.pending = self.pending.split('\n', 1)
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                self.last = row
                event = row.get('event') or row.get('stage')
                detail = row.get('detail', row.get('value', ''))
                if event in ('CHAIN_STEP_STARTED', 'CHAIN_STEP_VERIFIED', 'BUILD_REUSED', 'SOURCE_READY'):
                    if isinstance(detail, str) and re.fullmatch('[a-zA-Z0-9._-]{1,100}', detail):
                        print('  ' + event.replace('_', ' ').lower() + ': ' + detail,
                              file=self.screen, flush=True)
        # Never accumulate a boundless non-line-terminated tool message.
        if len(self.pending) > 2**20:
            self.pending = ''
        return len(text)

    def flush(self):
        self.log.flush()


class Owner:
    def __init__(self, directory):
        self.directory = directory
        self.screen = sys.stdout
        self.last_log = None

    def __call__(self, title, args):
        from reproduction.cli import main as lab_main
        fd, path = tempfile.mkstemp(prefix='workflow-', suffix='.log', dir=self.directory)
        self.last_log = path
        done = threading.Event()

        def heartbeat():
            elapsed = 0
            while not done.wait(30):
                elapsed += 30
                print(f'  Working: {title} ({elapsed}s). Details: {path}', file=self.screen, flush=True)

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            with os.fdopen(fd, 'w') as log:
                output = OwnerOutput(log, self.screen)
                with redirect_stdout(output), redirect_stderr(output):
                    code = lab_main(list(map(str, args)))
                result = output.last
            if code != 0:
                reason = failure_reason(result)
                raise WorkflowError(f'{title} stopped (exit {code}). {reason} Details: {path}')
            require(isinstance(result, dict), f'{title} returned no result. Details: {path}')
            return result
        finally:
            done.set()
            thread.join()


def failure_reason(result):
    if not isinstance(result, dict):
        return 'No verified result was returned.'
    if result.get('status') == 'SPACE_REPORT':
        docker = result.get('dockerStorage') or {}
        if docker.get('status') == 'BLOCKED':
            return 'Docker storage check failed: ' + str(docker.get('reason', 'See the diagnostic log.'))[:1000]
        if not (result.get('producerStorageCompatibility') or {}).get('compatible', True):
            return ('The selected frozen build owners do not support this storage layout, or their policy is unavailable. '
                    'A reviewed successor build plan is required; shared Docker storage was not moved.')
        if result.get('fitsCheckedPools') is False:
            return 'Insufficient capacity on a checked volume. See capacityPools in the diagnostic log for available and required bytes.'
        return 'Storage checks are incomplete. See the diagnostic log; no build was started.'
    return str(result.get('reason', 'Inspect the retained owner diagnostic.'))[:2000]


def configuration(env):
    names = ('SDV_ROOT', 'SDV_TMP', 'SDV_PYTHON', 'SDV_NODE', 'SDV_NPM',
             'SDV_CMAKE', 'SDV_DOCKER', 'SDV_SIGNING_IDENTITY', 'SDV_BUILD_BINDING',
             'SDV_SIM_BINDING', 'SDV_PREPARED_SOURCE', 'SDV_WORKFLOW_VOLUME')
    require(all(env.get(k) for k in names), 'Prepared environment is incomplete. Rerun the downloaded launcher.')
    config = {k: env[k] for k in names}
    config.update({k: env.get(k, '') for k in ('SDV_DRIVE_ACCOUNT', 'SDV_GCLOUD')})
    root = safe(config['SDV_ROOT'])
    require(ROOT == root/'source', 'Run the continuation from the selected source checkout, not another workspace.')
    return config


def resolve_dmg(build_root, result):
    """Use this invocation's chain record, never a newest-file search."""
    from reproduction.core import digest
    from reproduction import media
    require(result.get('status') == 'CHAIN_BUILT_NOT_QUALIFIED'
            and re.fullmatch('[a-f0-9]{64}', result.get('chainKey', '')),
            'The build chain did not report a complete engineering candidate.')
    record_path = safe(build_root/'builds/chains'/(result['chainKey']+'.json'))
    record = read(record_path)
    require(record.get('status') == 'CHAIN_BUILT_NOT_QUALIFIED', 'Incomplete chain receipt.')
    state = read(build_root/'preparation.json')
    matches = []
    for key in record['completed'].values():
        require(re.fullmatch('[a-f0-9]{64}', key), 'Invalid chain result key.')
        row = state['builds'][key]
        if row['target'] == 'dmg':
            require(digest(row['inputs']) == key, 'DMG build identity differs.')
            output = safe(build_root/'builds/dmg'/key)
            receipt = media.verify(output, row['inputs'])
            matches.extend(safe(output/name) for name in receipt['stamps'] if name.endswith('.dmg'))
    require(len(matches) == 1, 'Expected one DMG in this exact verified chain result.')
    return str(matches[0]), str(record_path)


def execute(config, owner, resolve=resolve_dmg):
    root = safe(config['SDV_ROOT'])
    control = safe(root/'.developer-preparation')
    source = root/'source'
    selected = read(control/'root-source.json')
    require(selected['volumeUUID'] == config['SDV_WORKFLOW_VOLUME'], 'Selected volume differs from source preparation.')
    validate_checkout(source, selected['revision'])
    source_check(config['SDV_PREPARED_SOURCE'], source)
    build = root/'build'
    inputs = root/'inputs'
    progress = dict(schemaVersion=1, rootRevision=selected['revision'], status='RUNNING', stage='plan')
    save(control/'workflow.json', progress)

    def step(label, args):
        progress.update(status='RUNNING', stage=label)
        save(control/'workflow.json', progress)
        print(label, flush=True)
        return owner(label, args)

    try:
        plan = step('[1/5] Checking the selected build plan', ['plan', '--profile', 'developer', '--build-plan', source/PLAN])
        require(plan.get('profile') == 'developer' and plan.get('orderedDeveloperChain'), 'Missing developer build plan.')
        package_plan = owner('Input size plan', ['inputs', 'plan'])
        print('  Binary inputs: %.2f GB to download if uncached; %.2f GB unpacked.' %
              (package_plan['archiveBytes']/1e9, package_plan['unpackedBytes']/1e9), flush=True)
        # Space is checked before Git acquisition and again before archive transfer.
        space_args = ['space', '--storage', build, '--build-plan', source/PLAN, '--docker', config['SDV_DOCKER']]
        owner('Storage and producer compatibility', space_args)
        step('[2/5] Preparing pinned component sources', ['prepare', '--profile', 'developer', '--storage', build, '--sources-only'])
        owner('Verify pinned sources', ['verify', '--storage', build, '--sources-only'])
        owner('Storage before binary inputs', space_args)
        args = ['inputs', 'prepare', '--storage', inputs, '--binding', config['SDV_BUILD_BINDING'],
                '--simulation-binding', config['SDV_SIM_BINDING']]
        binding = read(config['SDV_BUILD_BINDING'])
        if binding.get('schemaVersion') == 1:
            require(config['SDV_DRIVE_ACCOUNT'] and config['SDV_GCLOUD'], 'Explicit private input access is missing.')
            args += ['--account', config['SDV_DRIVE_ACCOUNT'], '--gcloud', config['SDV_GCLOUD']]
        prepared = step('[3/5] Downloading or reusing verified build inputs', args)
        require(prepared.get('status') == 'BUILD_INPUTS_READY_NOT_PROFILE_QUALIFIED', 'Incomplete build inputs.')
        for name in ('kitInputs', 'gatewaySdk', 'factoryInputs'):
            path = safe(prepared[name])
            require(path.is_relative_to(inputs) and path.is_dir(), 'Input result points outside the selected workspace.')
        # The canonical prepare call already verifies cached/extracted inputs;
        # no duplicate complete archive read is needed here.
        save(control/'input-paths.json', prepared)
        owner('Storage before compilation', space_args)
        args = ['build', '--target', 'all', '--storage', build, '--build-plan', source/PLAN,
                '--kit-inputs', prepared['kitInputs'], '--gateway-sdk', prepared['gatewaySdk'],
                '--factory-inputs', prepared['factoryInputs'], '--input-checkpoint', INPUTS,
                '--release-checkpoint', RELEASE, '--test-tmp-parent', config['SDV_TMP'],
                '--ui-python', '/usr/bin/python3', '--prepare-dependencies']
        for flag, key in (('python', 'SDV_PYTHON'), ('node', 'SDV_NODE'), ('npm', 'SDV_NPM'),
                          ('cmake', 'SDV_CMAKE'), ('docker', 'SDV_DOCKER'), ('signing-identity', 'SDV_SIGNING_IDENTITY')):
            args += ['--'+flag, config[key]]
        result = step('[4/5] Building and signing the developer DMG', args)
        validate_checkout(source, selected['revision'])
        print('[5/5] Locating the verified result', flush=True)
        dmg, receipt = resolve(build, result)
        progress.update(status='CHAIN_BUILT_NOT_QUALIFIED', stage='complete', dmg=dmg, chainReceipt=receipt)
        save(control/'workflow.json', progress)
        print('\nBUILD COMPLETE — engineering candidate, not release-qualified.\nDMG: '+dmg+'\nBuild receipt: '+receipt+
              '\nNothing was installed, launched or published.', flush=True)
        return 0
    except BaseException:
        progress.update(status='STOPPED')
        save(control/'workflow.json', progress)
        raise


def main():
    # SIGTERM must unwind canonical child owners just like Ctrl+C, not orphan
    # their isolated compiler/Git process groups.
    def cancel(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    try:
        config = configuration(os.environ)
        os.chdir(ROOT)
        control = safe(Path(config['SDV_ROOT'])/'.developer-preparation')
        lock = safe(control/'workflow.lock')
        fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise WorkflowError('Another workflow is running in this workspace.') from None
            return execute(config, Owner(control))
    except KeyboardInterrupt:
        print('\nSTOPPED — completed results and partial work preserved. Rerun the same launcher after resolving any reported partial-output issue.', file=sys.stderr)
        return 130
    except (WorkflowError, CatalogError, LabError, OSError, ValueError, KeyError, TypeError) as error:
        print('\nSTOP: '+(str(error) if isinstance(error, (WorkflowError, CatalogError, LabError)) else
                           'Workflow metadata or a local dependency is unavailable. Existing work was preserved.')+
              '\nResolve the cause, then rerun the same downloaded launcher. No automatic retry or source update.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

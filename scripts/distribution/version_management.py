# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Engineering selection/recovery, independent of native activation and Cloud."""

import argparse
import json
import os
from pathlib import Path
import sys

# Trusted tool source only; never import code from the package being inspected.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import installed_control as control
from aosedge_demo_orchestrator.runtime_paths import instance, small_json
from installation import Store, atomic_record, fsync_directory, private_directory
from installation_inputs import Bundle, InstallError, parse, read_small, require


def compatible(bundle):
    manifest = parse(read_small(bundle.root / 'application-manifest.json', 2**20))
    require(manifest.get('installedStateContract') == control.CONTRACT, 'STATE_COMPATIBILITY_UNSUPPORTED')


class Versions:
    def __init__(self, store, state):
        self.store = store
        self.state, self.identity = instance(state)
        require(not self.state.is_relative_to(store.root) and not store.root.is_relative_to(self.state),
                'STATE_PACKAGE_OVERLAP')

    def read(self):
        self.store.guard()
        value = control.selection(self.state, self.identity)
        if value:
            require(value['storePath'] == str(self.store.root) and value['volumeUUID'] == self.store.uuid,
                    'SELECTION_STORE_MISMATCH')
        return value

    def status(self):
        with control.lease(self.state / control.LOCK):
            value = self.read()
            return dict(status='SELECTED_NOT_STARTED' if value and value['current'] else 'NOT_SELECTED',
                        revision=value['revision'] if value else 0,
                        current=value['current'] if value else None,
                        previous=value['previous'] if value else None,
                        runtimeChanged=False, userDataChanged=False)

    def change(self, action, revision, digest=None):
        require(action in ('select', 'rollback', 'unselect'), 'SELECTION_ACTION_INVALID')
        require(type(revision) is int and 0 <= revision < 2**53, 'SELECTION_REVISION_INVALID')
        if action == 'select':
            control.pin(digest)
        else:
            require(digest is None, 'SELECTION_UNEXPECTED_VERSION')
        require(self.store.inspect(), 'INSTALL_STORE_MISSING')
        with self.store.writer(), control.lease(self.state / control.LOCK, exclusive=True):
            value = self.read()
            require(revision == (value['revision'] if value else 0), 'SELECTION_STALE_REVISION')
            control.quiescent(self.state, self.store.root)
            current = value['current'] if value else None
            previous = value['previous'] if value else None
            if action == 'rollback':
                require(previous is not None, 'ROLLBACK_NOT_AVAILABLE')
                digest = previous
            if digest is not None:
                control.repair_complete(self.store.root, digest)
                with control.lease(self.store.root / 'receipts' / (digest + '.use.lock')):
                    bundle = Bundle(self.store.root / 'versions' / digest, digest)
                    compatible(bundle)
                    bundle.verify()
                    receipt, _ = small_json(self.store.root / 'receipts' / (digest + '.json'), 4096, owned=True)
                    require(receipt == self.store.receipt(bundle, bool(receipt.get('reused'))), 'INSTALL_RECEIPT_INVALID')
            if current == digest:
                return dict(status='SELECTED_NOT_STARTED' if current else 'NOT_SELECTED', revision=revision,
                            current=current, previous=previous, reused=True, runtimeChanged=False,
                            userDataChanged=False, bytesFreed=0)
            require(revision + 1 < 2**53, 'SELECTION_REVISION_EXHAUSTED')
            # Unselect retains the last chosen version for an explicit restore.
            next_value = dict(schemaVersion=1, instanceId=self.identity, storePath=str(self.store.root),
                volumeUUID=self.store.uuid, stateContract=control.CONTRACT, revision=revision+1,
                current=digest, previous=current if current is not None else (previous if previous != digest else None))
            self.store.guard()
            control.commit_selection(self.state, next_value)
            require(self.read() == next_value, 'SELECTION_POSTCONDITION_FAILED')
            return dict(status='SELECTED_NOT_STARTED' if digest else 'UNSELECTED_DATA_RETAINED',
                        revision=next_value['revision'], current=digest, previous=next_value['previous'],
                        reused=False, runtimeChanged=False, userDataChanged=False, bytesFreed=0)


def repair(store, source, digest, *, copier=None, checkpoint=lambda stage: None):
    """Preserve damaged bytes; explicit replay reconciles every promotion gap."""
    control.pin(digest)
    source = Path(source).absolute()
    source_bundle = store.plan(source, digest)
    compatible(source_bundle)
    require(store.inspect(), 'INSTALL_STORE_MISSING')
    options = {'copier': copier} if copier is not None else {}
    with store.writer(), control.lease(store.root / 'receipts' / (digest + '.use.lock'), exclusive=True):
        control.unused((store.root,))
        quarantine = store.root / 'quarantine'
        work = quarantine / digest
        transaction = work / 'transaction.json'
        target = store.root / 'versions' / digest
        original = work / 'original'
        replacement_store = work / 'replacement-store'
        replacement = replacement_store / 'versions' / digest
        identity = dict(schemaVersion=1, manifestSha256=digest, volumeUUID=store.uuid)
        if work.exists() or work.is_symlink():
            private_directory(quarantine)
            private_directory(work)
            entries = {p.name for p in work.iterdir()}
            require(entries <= {'transaction.json', 'transaction.json.pending', 'original', 'replacement-store'},
                    'REPAIR_WORK_UNRECOGNIZED')
            if not transaction.exists() and not transaction.is_symlink():
                # The first record can be interrupted after mkdir or while
                # writing its fixed private temporary. No promotion happened.
                require(entries <= {'transaction.json.pending'} and target.is_dir()
                        and not target.is_symlink(), 'REPAIR_RECONCILIATION_REQUIRED')
                source_bundle.verify()
                atomic_record(transaction, dict(identity, status='REPAIRING'))
            record, _ = small_json(transaction, 4096, owned=True)
            require(record in (dict(identity, status='REPAIRING'), dict(identity, status='REPAIRED')),
                    'REPAIR_TRANSACTION_INVALID')
            if record['status'] == 'REPAIRED':
                result = store.verify(digest)  # A second damaged generation is not overwritten.
                return dict(status='REPAIRED_PROGRAM_ONLY', reused=True, originalPreserved=True,
                            manifestSha256=digest, runtimeChanged=False, userDataChanged=False)
        else:
            require(target.exists() and not target.is_symlink() and target.is_dir(), 'REPAIR_VERSION_MISSING')
            try:
                verified = store.verify(digest)
            except InstallError as error:
                require(str(error).startswith(('INPUT_', 'APPLICATION_', 'SOURCE_', 'FACTORY_', 'REQUIRED_', 'JSON_')),
                        'REPAIR_VERIFICATION_UNAVAILABLE')
            else:
                atomic_record(store.root / 'receipts' / (digest + '.json'), verified)
                return dict(status='PROGRAM_VERIFIED_NO_REPAIR', reused=True, originalPreserved=False,
                            receiptReconciled=True,
                            manifestSha256=digest, runtimeChanged=False, userDataChanged=False)
            source_bundle.verify()  # Reject an invalid repair source before changing the target.
            private_directory(quarantine, True)
            private_directory(work, True)
            atomic_record(transaction, dict(identity, status='REPAIRING'))
        # No unknown combination is interpreted as permission to overwrite.
        require(not original.is_symlink(), 'REPAIR_WORK_UNRECOGNIZED')
        if not original.exists():
            require(target.is_dir() and not target.is_symlink(), 'REPAIR_RECONCILIATION_REQUIRED')
            staging = Store(replacement_store, store.uuid, store.volume_probe)
            staging.install(source, digest, **options)
            control.unused((store.root,))
            store.guard()
            checkpoint('BEFORE_ORIGINAL_MOVE')
            os.rename(target, original)
            fsync_directory(target.parent); fsync_directory(work)
            checkpoint('AFTER_ORIGINAL_MOVE')
        if replacement.exists():
            require(not target.exists() and not target.is_symlink(), 'REPAIR_PROMOTION_CONFLICT')
            valid = Bundle(replacement, digest)
            compatible(valid); valid.verify()
            store.guard()
            os.rename(replacement, target)
            fsync_directory(replacement.parent); fsync_directory(target.parent)
            checkpoint('AFTER_REPLACEMENT_MOVE')
        require(target.is_dir() and original.is_dir() and not original.is_symlink(), 'REPAIR_RECONCILIATION_REQUIRED')
        final = store.verify(digest)
        atomic_record(store.root / 'receipts' / (digest + '.json'), final)
        atomic_record(transaction, dict(identity, status='REPAIRED'))
        return dict(status='REPAIRED_PROGRAM_ONLY', reused=False, originalPreserved=True,
                    manifestSha256=digest, runtimeChanged=False, userDataChanged=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('status', 'select', 'rollback', 'unselect', 'repair'))
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--volume-uuid', required=True)
    parser.add_argument('--instance-root', type=Path)
    parser.add_argument('--revision', type=int)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--source', type=Path)
    args = parser.parse_args(argv)
    try:
        store = Store(args.store, args.volume_uuid)
        if args.action == 'repair':
            require(args.source is not None and args.instance_root is None and args.revision is None,
                    'REPAIR_ARGUMENTS_INVALID')
            result = repair(store, args.source, args.manifest_sha256)
        else:
            require(args.instance_root is not None and args.source is None, 'SELECTION_ARGUMENTS_INVALID')
            if args.action == 'status':
                require(args.revision is None and args.manifest_sha256 is None, 'SELECTION_ARGUMENTS_INVALID')
            versions = Versions(store, args.instance_root)
            result = versions.status() if args.action == 'status' else versions.change(args.action, args.revision, args.manifest_sha256)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError) as error:
        text = str(error)
        reason = text if isinstance(error, InstallError) or isinstance(error, ValueError) and text.startswith('INSTALLED_') else 'VERSION_IO_UNAVAILABLE'
        print(json.dumps(dict(status='BLOCKED', reason=reason)))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

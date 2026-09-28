# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Offline, non-activating installation transactions for a complete pinned kit."""

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import stat
import subprocess
import time
from uuid import UUID

from installation_inputs import (Bundle, InstallError, SHA, digest, file_info, identity,
                                 inventory, parse, read_small, require, unlinked)

RESERVE = 90 * 2**30
STORE_ENTRIES = {'store.json', 'writer.lock', 'staging', 'versions', 'receipts', 'quarantine'}


def fsync_directory(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def volume_identity(path):
    # diskutil accepts a device/mountpoint, not an arbitrary existing directory.
    # df resolves firmlinks and nested APFS mounts; never parse its mount name.
    before = path.stat().st_dev
    found = subprocess.run(['/bin/df', '-P', str(path)], capture_output=True, timeout=15,
                           env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'})
    require(found.returncode == 0, 'INSTALL_VOLUME_UNAVAILABLE')
    lines = found.stdout.decode('utf-8').splitlines()
    require(len(lines) == 2 and lines[1].split(), 'INSTALL_VOLUME_INVALID')
    device = lines[1].split()[0]
    require(re.fullmatch(r'/dev/disk\d+(?:s\d+)+', device), 'INSTALL_VOLUME_INVALID')
    result = subprocess.run(['/usr/sbin/diskutil', 'info', '-plist', device],
                            capture_output=True, timeout=15)
    require(result.returncode == 0, 'INSTALL_VOLUME_UNAVAILABLE')
    try:
        info = plistlib.loads(result.stdout)
        require(isinstance(info, dict), 'INSTALL_VOLUME_INVALID')
        require(info.get('GlobalPermissionsEnabled') is True, 'INSTALL_VOLUME_OWNERSHIP_REQUIRED')
        mount = info.get('MountPoint')
        require(isinstance(mount, str) and mount.startswith('/'), 'INSTALL_VOLUME_INVALID')
        require(info.get('DeviceNode') == device and path.stat().st_dev == before
                and Path(mount).stat().st_dev == before,
                'INSTALL_VOLUME_CHANGED')
        return str(UUID(info['VolumeUUID'])).upper()
    except InstallError:
        raise
    except (KeyError, ValueError, plistlib.InvalidFileException):
        raise InstallError('INSTALL_VOLUME_INVALID') from None


def private_directory(path, create=False):
    unlinked(path)
    if create and not path.exists():
        path.mkdir(mode=0o700)
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o700, 'INSTALL_STORE_DIRECTORY_UNSAFE')


def atomic_record(path, value):
    temporary = path.with_name(path.name + '.pending')
    if temporary.exists() or temporary.is_symlink():
        info = file_info(temporary)
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600,
                'INSTALL_PENDING_RECORD_UNSAFE')
        temporary.unlink()
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write((json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fsync_directory(path.parent)


def copy_file(source, target, clone=True):
    """Clone only on the same device; unsupported clone explicitly falls back."""
    if clone and source.stat().st_dev == target.parent.stat().st_dev:
        done = subprocess.run(['/bin/cp', '-c', '-p', str(source), str(target)],
                              capture_output=True, timeout=180)
        if done.returncode == 0:
            return
        if target.exists() or target.is_symlink():
            file_info(target)
            target.unlink()
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst, 4*2**20)
        dst.flush()
        os.fsync(dst.fileno())
    target.chmod(stat.S_IMODE(source.stat().st_mode))


class Store:
    def __init__(self, root, expected_volume_uuid, volume_probe=volume_identity):
        self.root = unlinked(root)
        try:
            self.uuid = str(UUID(expected_volume_uuid)).upper()
        except (ValueError, TypeError, AttributeError):
            raise InstallError('INSTALL_VOLUME_ID_INVALID') from None
        self.volume_probe = volume_probe
        require(self.root.parent.is_dir(), 'INSTALL_PARENT_MISSING')
        self.device = self.root.parent.stat().st_dev
        self.guard()

    def guard(self, full=True):
        unlinked(self.root)
        path = self.root if self.root.exists() else self.root.parent
        require(path.stat().st_dev == self.device, 'INSTALL_VOLUME_CHANGED')
        if full:
            require(self.volume_probe(path) == self.uuid, 'INSTALL_VOLUME_CHANGED')

    def inspect(self):
        self.guard()
        if not self.root.exists():
            return False
        private_directory(self.root)
        entries = {p.name for p in self.root.iterdir()}
        require(entries <= STORE_ENTRIES, 'INSTALL_STORE_UNRECOGNIZED')
        require('store.json' in entries, 'INSTALL_STORE_UNRECOGNIZED')
        marker = self.root/'store.json'
        require(file_info(marker).st_uid == os.getuid(), 'INSTALL_STORE_NOT_OWNED')
        value = parse(read_small(marker, 4096))
        require(value == dict(schemaVersion=1, kind='aosedge-package-store', volumeUUID=self.uuid),
                'INSTALL_STORE_BINDING_INVALID')
        return True

    @contextmanager
    def writer(self):
        if not self.inspect():
            self.root.mkdir(mode=0o700)
            atomic_record(self.root/'store.json', dict(schemaVersion=1, kind='aosedge-package-store', volumeUUID=self.uuid))
        lock = self.root/'writer.lock'
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                    and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600,
                    'INSTALL_LOCK_UNSAFE')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise InstallError('INSTALL_BUSY') from None
            self.guard()
            self.inspect()
            for name in ('staging', 'versions', 'receipts'):
                private_directory(self.root/name, True)
            yield
        finally:
            os.close(fd)

    def space(self, remaining, full=True):
        self.guard(full)
        path = self.root if self.root.exists() else self.root.parent
        require(shutil.disk_usage(path).free >= RESERVE + remaining, 'INSTALL_SPACE_INSUFFICIENT')

    def plan(self, source, pin):
        source = unlinked(source)
        require(not (source == self.root or source.is_relative_to(self.root)
                     or self.root.is_relative_to(source)), 'INSTALL_SOURCE_STORE_OVERLAP')
        self.inspect()
        bundle = Bundle(source, pin)
        self.space(0 if (self.root/'versions'/pin).exists() else bundle.total_bytes)
        return bundle

    def receipt(self, bundle, reused=False):
        return dict(schemaVersion=1, status='INSTALLED_NOT_ACTIVATED',
                    manifestSha256=bundle.pin, volumeUUID=self.uuid,
                    files=len(bundle.rows), logicalBytes=bundle.total_bytes,
                    reused=reused, runtimeChanged=False, operatorStateCopied=False,
                    cloudAccessed=False, activeVersionSelected=False)

    def verify(self, pin):
        require(isinstance(pin, str) and SHA.fullmatch(pin), 'RELEASE_PIN_INVALID')
        require(self.inspect(), 'INSTALL_STORE_MISSING')
        private_directory(self.root/'versions')
        bundle = Bundle(self.root/'versions'/pin, pin)
        bundle.verify()
        self.guard()
        return self.receipt(bundle, True)

    def install(self, source, pin, progress=lambda event: None, copier=copy_file):
        bundle = self.plan(source, pin)
        with self.writer():
            target = self.root/'versions'/pin
            stage = self.root/'staging'/pin
            if target.exists() or target.is_symlink():
                verified = Bundle(target, pin)
                verified.verify()
                self.space(0)
                result = self.receipt(verified, True)
                atomic_record(self.root/'receipts'/(pin+'.json'), result)
                self._finish_stage(stage)
                return result
            transaction = dict(schemaVersion=1, manifestSha256=pin, volumeUUID=self.uuid)
            if stage.exists() or stage.is_symlink():
                private_directory(stage)
                require({p.name for p in stage.iterdir()} <= {'transaction.json', 'bundle', 'copy.pending'},
                        'INSTALL_STAGING_UNRECOGNIZED')
                require(parse(read_small(stage/'transaction.json', 4096)) == transaction,
                        'INSTALL_TRANSACTION_MISMATCH')
            else:
                private_directory(stage, True)
                atomic_record(stage/'transaction.json', transaction)
            destination = stage/'bundle'
            private_directory(destination, True)
            current = inventory(destination)
            require(current <= bundle.rows.keys(), 'INSTALL_STAGING_UNDECLARED_FILE')
            pending = stage/'copy.pending'
            if pending.exists() or pending.is_symlink():
                info = file_info(pending)
                require(info.st_uid == os.getuid(), 'INSTALL_PENDING_FILE_UNSAFE')
                pending.unlink()
            copied = 0
            verified_identities = {}
            last_checkpoint = time.monotonic()
            for index, (name, row) in enumerate(sorted(bundle.rows.items()), 1):
                bundle.unchanged(name)
                src, dst = bundle.root/name, destination/name
                self.guard(False)
                if index == 1 or time.monotonic()-last_checkpoint >= 2:
                    self.space(bundle.total_bytes-copied)
                    last_checkpoint = time.monotonic()
                if name in current:
                    info = file_info(dst)
                    require(info.st_size == row.size and stat.S_IMODE(info.st_mode) == row.mode
                            and digest(dst) == row.sha256, 'INSTALL_STAGED_FILE_CHANGED')
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    copier(src, pending)
                    info = file_info(pending)
                    require(info.st_size == row.size and stat.S_IMODE(info.st_mode) == row.mode
                            and digest(pending) == row.sha256, 'INSTALL_TRANSFER_MISMATCH')
                    # Flush cloned bytes too, before this file becomes resumable.
                    with pending.open('rb') as stream:
                        os.fsync(stream.fileno())
                    bundle.unchanged(name)
                    os.rename(pending, dst)
                    fsync_directory(dst.parent)
                verified_identities[name] = identity(dst)
                copied += row.size
                progress(dict(stage='COPY_VERIFIED', files=index, totalFiles=len(bundle.rows),
                              bytes=copied, totalBytes=bundle.total_bytes))
            bundle.check_inventory()
            for name in bundle.rows:
                bundle.unchanged(name)
            require(inventory(destination) == set(bundle.rows), 'INSTALL_FINAL_INVENTORY_MISMATCH')
            require(all(identity(destination/name) == value for name, value in verified_identities.items()),
                    'INSTALL_STAGED_FILE_CHANGED')
            self.guard()
            self.space(0)
            os.rename(destination, target)
            fsync_directory(target.parent)
            result = self.receipt(bundle)
            atomic_record(self.root/'receipts'/(pin+'.json'), result)
            self._finish_stage(stage)
            return result

    def _finish_stage(self, stage):
        if not stage.exists():
            return
        private_directory(stage)
        require({p.name for p in stage.iterdir()} == {'transaction.json'}, 'INSTALL_STAGING_NOT_EMPTY')
        require(parse(read_small(stage/'transaction.json', 4096)) ==
                dict(schemaVersion=1, manifestSha256=stage.name, volumeUUID=self.uuid),
                'INSTALL_TRANSACTION_MISMATCH')
        (stage/'transaction.json').unlink()
        stage.rmdir()
        fsync_directory(stage.parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'install', 'verify'))
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--volume-uuid', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    try:
        store = Store(args.store, args.volume_uuid)
        if args.action == 'verify':
            result = store.verify(args.manifest_sha256)
        else:
            require(args.source is not None, 'INSTALL_SOURCE_REQUIRED')
            if args.action == 'plan':
                bundle = store.plan(args.source, args.manifest_sha256)
                result = dict(status='PLAN_ELIGIBLE_NOT_INSTALLED', files=len(bundle.rows),
                              logicalBytes=bundle.total_bytes, requiredFreeBytes=RESERVE+bundle.total_bytes,
                              manifestSha256=bundle.pin, payloadDigestsVerified=False)
            else:
                result = store.install(args.source, args.manifest_sha256)
        print(json.dumps(result))
        return 0
    except InstallError as error:
        print(json.dumps(dict(status='BLOCKED', reason=str(error))))
        return 2
    except (OSError, subprocess.SubprocessError):
        print(json.dumps(dict(status='BLOCKED', reason='INSTALL_IO_UNAVAILABLE')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

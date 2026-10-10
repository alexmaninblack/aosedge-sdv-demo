# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Terminal-only presentation; progress never acts as a completion receipt."""
import os
import re
import shutil
import threading
import time

NAMES = {
    'carla-runtime': 'CARLA simulator', 'host-support': 'Mac runtime support',
    'gateway-sdk': 'Gateway SDK', 'vehicle-bases': 'Vehicle platform packages',
    'factory-image': 'Factory controller image', 'presenter': 'Presenter and Driving Control',
    'cloud-sdk': 'Cloud SDK', 'brake-backend': 'Brake backend', 'tire-backend': 'Tire backend',
    'backend-export': 'Backend images', 'brake-v1': 'Brake service V1',
    'brake-v2': 'Brake service V2', 'brake-v3': 'Brake service V3', 'tire-v1': 'Tire service V1',
    'gateway': 'Vehicle Gateway', 'preparation': 'Vehicle installation inputs',
    'host-runtime': 'Mac runtime', 'backend-inputs': 'Backend installation inputs',
    'vm-runtime': 'Virtual controller runtime', 'application': 'Lab application',
    'setup': 'Signed Setup application', 'dmg': 'Installer DMG',
}


def label(value):
    return NAMES.get(value, value.replace('-', ' '))


def size(value):
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if value < 1024 or unit == 'TiB':
            return f'{value:.1f} {unit}'
        value /= 1024


def duration(seconds):
    seconds = max(0, int(seconds))
    return f'{seconds // 60}m {seconds % 60:02d}s' if seconds >= 60 else f'{seconds}s'


class Display:
    def __init__(self, screen, title='', *, clock=time.monotonic):
        self.screen, self.clock = screen, clock
        self.tty = screen.isatty() and os.environ.get('TERM') != 'dumb'
        self.lock = threading.RLock()
        self.title, self.phase = title, ''
        self.done = self.total = None
        self.units = 'bytes'
        self.started = self.clock()
        self.offset = 0
        self.frame = 0
        self.last_draw = -1e9
        self.last_bucket = None
        self.chain_done = self.chain_total = 0
        self.completed = set()
        self.artifact = ''
        self.expected = 0
        self.active = False
        self.transfer_updated = self.started

    def begin(self, title, phase='', total=None, done=0, units='bytes'):
        with self.lock:
            if self.active:
                if self.tty:
                    self.draw(force=True)
                self._end_line()
            self.title, self.phase = title, phase
            self.total, self.done, self.units = total, done if total else None, units
            self.started = self.clock()
            self.offset = done
            self.transfer_updated = self.started
            self.last_bucket = None
            print('  ' + title, file=self.screen, flush=True)
            self.active = True
            self.draw(force=True)

    def _end_line(self):
        if self.tty:
            self.screen.write('\n')
            self.screen.flush()

    def draw(self, force=False):
        with self.lock:
            if not self.active:
                return
            now = self.clock()
            if not force and now - self.last_draw < .2:
                return
            self.frame += 1
            spinner = '|/-\\'[self.frame % 4]
            if self.total:
                done = min(self.total, max(0, self.done))
                fraction = done / self.total
                bar = '#' * int(fraction * 20) + '-' * (20 - int(fraction * 20))
                if self.units == 'steps':
                    # This fraction counts verified steps, never estimated build time.
                    tail = f'{done}/{self.total} steps verified {spinner}'
                else:
                    tail = f'{fraction:5.1%}  {size(done)} / {size(self.total)}'
                    if self.phase == 'Downloading' and done < self.total:
                        elapsed = now - self.started
                        rate = (done - self.offset) / elapsed if elapsed >= 1 else 0
                        if now - self.transfer_updated >= 5:
                            tail += '  waiting for data'
                        elif rate > 0:
                            tail += f'  {size(rate)}/s  ~{duration((self.total-done)/rate)} left'
                line = f'[{bar}] {tail}'
                bucket = int(fraction * 4)
            else:
                position = self.frame % 16
                bar = '-' * position + '====' + '-' * (16 - position)
                line = f'[{bar}] {self.phase or "Working"} {spinner}'
                bucket = 0
            if self.tty:
                width = max(10, shutil.get_terminal_size((100, 24)).columns - 1)
                self.screen.write('\r\033[2K' + ('  ' + line)[:width])
            elif force or bucket != self.last_bucket:
                # Redirected logs have no animation, escape codes or heartbeat spam.
                print('  ' + line, file=self.screen)
            self.screen.flush()
            self.last_draw, self.last_bucket = now, bucket

    def update(self, done):
        with self.lock:
            if type(done) is int and self.total and 0 <= done <= self.total:
                if done != self.done:
                    self.transfer_updated = self.clock()
                self.done = done
                self.draw(force=done == self.total)

    def finish(self, success):
        with self.lock:
            if self.active:
                if self.tty:
                    self.draw(force=True)
                self._end_line()
                print('  ' + ('Done.' if success else 'Stopped; see the error below.'),
                      file=self.screen, flush=True)
                self.active = False

    def event(self, event, detail):
        with self.lock:
            if event == 'ARTIFACT_SELECTED' and isinstance(detail, dict):
                role, name, total = detail.get('role'), detail.get('file'), detail.get('bytes')
                if role in NAMES and isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_.+-]{1,160}', name) and type(total) is int and total > 0:
                    self.artifact, self.expected = label(role) + ' — ' + name, total
                    self.begin(self.artifact, 'Checking verified cache')
            elif event == 'DOWNLOAD_STARTED' and isinstance(detail, dict) and self.artifact:
                offset = detail.get('offset')
                if type(offset) is int and 0 <= offset <= self.expected:
                    self.begin(self.artifact, 'Downloading', self.expected, offset)
            elif event == 'DOWNLOAD_BYTES':
                self.update(detail)
            elif event == 'VERIFY_STARTED' and self.artifact:
                self.begin('Verifying download — ' + self.artifact, 'Verifying', self.expected)
            elif event == 'VERIFY_BYTES':
                self.update(detail)
            elif event in ('ARTIFACT_VERIFIED', 'ARTIFACT_REUSED') and self.artifact:
                self.begin(('Verified — ' if event == 'ARTIFACT_VERIFIED' else 'Reusing verified cache — ') + self.artifact,
                           'Ready', self.expected, self.expected)
            elif event == 'EXTRACT_STARTED' and isinstance(detail, dict) and detail.get('role') in NAMES:
                self.begin('Unpacking — ' + label(detail['role']), 'Unpacking', detail.get('totalBytes'))
            elif event == 'EXTRACT_BYTES' and isinstance(detail, dict):
                self.update(detail.get('bytes'))
            elif event == 'EXTRACT_FINISHED':
                self.update(self.total)
            elif event == 'INPUTS_VERIFYING':
                self.begin('Checking prepared build inputs', 'Verifying files and manifests')
            elif event == 'CHAIN_STARTED' and type(detail) is int and detail > 0:
                self.chain_total, self.chain_done = detail, 0
                self.completed.clear()
            elif event == 'CHAIN_STEP' and isinstance(detail, str) and detail in NAMES:
                self.begin('Building — ' + label(detail), 'Working', self.chain_total or None,
                           self.chain_done, 'steps')
            elif event == 'CHAIN_STEP_VERIFIED' and isinstance(detail, str) and detail not in self.completed:
                self.completed.add(detail)
                self.chain_done += 1
                self.update(self.chain_done)
            elif event in ('FETCH_SOURCE', 'SOURCE_READY') and isinstance(detail, str) and re.fullmatch(r'[a-zA-Z0-9._-]{1,100}', detail):
                self.begin(('Preparing source — ' if event == 'FETCH_SOURCE' else 'Source ready — ') + label(detail),
                           'Checking sources')

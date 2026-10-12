# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One owned SSH connection for fresh read adapters; never an owner-state cache."""
import os
from pathlib import Path
import signal
import stat
import subprocess
import time
import remote_harness as h


class ReadTransport:
    def __init__(self, transport, scratch):
        self.transport=transport
        self.socket=h.unlinked(Path(scratch)/'reads.sock')
        info=self.socket.parent.stat()
        h.require(info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700
                  and len(os.fsencode(self.socket))<100 and not self.socket.exists(),
                  'PRIVATE_READ_TRANSPORT_REQUIRED')
        self.master=None;self.active=None;self.closed=False;self.calls=[]
        self.started=None;self.startup_seconds=None

    def arguments(self, control=None):
        args=h.ssh_args(self.transport)
        if control:
            args[-1:-1]=['-S',str(self.socket),'-O',control]
        else:
            args[-1:-1]=['-o','ControlMaster=no','-o','ControlPath='+str(self.socket),
                         '-o','ProxyCommand=/usr/bin/false']
        return args

    def __enter__(self):
        self.started=time.monotonic()
        args=h.ssh_args(self.transport)
        args[-1:-1]=['-N','-o','ControlMaster=yes','-o','ControlPath='+str(self.socket),
                     '-o','ControlPersist=no']
        self.master=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        try:
            end=time.monotonic()+12
            while not self.socket.exists():
                h.require(self.master.poll() is None and time.monotonic()<end,'READ_TRANSPORT_NOT_READY')
                time.sleep(.05)
            h.run(self.arguments('check'),timeout=3)
            self.startup_seconds=round(time.monotonic()-self.started,3)
            return self
        except BaseException:
            self.close();raise

    def remote(self, script, timeout=60):
        h.require(self.master is not None and self.master.poll() is None and self.socket.exists()
                  and not self.closed and self.active is None,'READ_TRANSPORT_LOST_NO_RECONNECT')
        started=time.monotonic();outcome='FAIL'
        task=subprocess.Popen(self.arguments()+['/bin/sh -s'],stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,
                              start_new_session=True)
        self.active=task
        try:
            try: output,_=task.communicate(script,timeout=timeout)
            except subprocess.TimeoutExpired:
                self.cancel();raise h.Error('READ_TRANSPORT_TIMEOUT_NO_RETRY') from None
            h.require(task.returncode==0,'READ_TRANSPORT_COMMAND_FAILED')
            h.require(len(output.encode())<=4*2**20,'READ_TRANSPORT_RESPONSE_TOO_LARGE')
            outcome='PASS';return output
        finally:
            if task.poll() is None:self.cancel()
            self.active=None
            self.calls.append(dict(seconds=round(time.monotonic()-started,3),outcome=outcome))

    def cancel(self):
        task=self.active
        if task is None or task.poll() is not None:return
        # Exact owned local SSH client group, never any demo or shared SSH owner.
        os.killpg(task.pid,signal.SIGTERM)
        try:task.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(task.pid,signal.SIGKILL);task.communicate(timeout=3)

    def close(self):
        self.cancel()
        if self.master is not None:
            if self.master.poll() is None:
                try:h.run(self.arguments('exit'),timeout=3)
                except (ValueError,subprocess.SubprocessError):self.master.terminate()
            try:self.master.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.master.terminate();self.master.wait(timeout=3)
            h.require(self.master.poll() is not None,'READ_TRANSPORT_CLOSE_UNCONFIRMED')
        if self.socket.exists():
            h.require(stat.S_ISSOCK(self.socket.lstat().st_mode),'READ_SOCKET_TYPE_CHANGED')
            self.socket.unlink()  # Owned abandoned socket, after exact master exit.
        self.closed=True

    def __exit__(self,*args):self.close()

    def report(self):
        return dict(transport='PINNED_SSH_MULTIPLEX',connectionsStarted=int(self.master is not None),
            startupSeconds=self.startup_seconds,requests=len(self.calls),
            requestSeconds=round(sum(r['seconds'] for r in self.calls),3),
            failedRequests=sum(r['outcome']!='PASS' for r in self.calls),
            freshWorkerPerRead=True,cachedOwnerResponses=False,automaticReconnect=False,
            closed=self.closed and (self.master is None or self.master.poll() is not None)
                and not self.socket.exists(),activeClientClosed=self.active is None or self.active.poll() is not None)

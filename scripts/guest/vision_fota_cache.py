#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Acquire four recipe-pinned native-tool sources, separately from offline builds."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request

PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')
DOWNLOADS=Path('/home/yocto/yocto-cache/downloads')
ARCHIVES={
 'lzo-2.10.tar.gz':('c0f892943208266f9b6543b3ae308fab6284c5c90e627931446fb49b4221a072',[
   'https://www.oberhumer.com/opensource/lzo/download/lzo-2.10.tar.gz',
   'https://downloads.yoctoproject.org/mirror/sources/lzo-2.10.tar.gz']),
 'libostree-2024.5.tar.xz':('bc12d8493db64152093ee5be77cf62a29cc67a4a9e430dc987103e78aada4a6f',[
   'https://github.com/ostreedev/ostree/releases/download/v2024.5/libostree-2024.5.tar.xz'])}
REPOSITORIES={
 'github.com.lz4.lz4.git':('https://github.com/lz4/lz4.git','5ff839680134437dbf4678f3d0c7b371d84f4964'),
 'github.com.plougher.squashfs-tools.git':('https://github.com/plougher/squashfs-tools.git','d8cb82d9840330f9344ec37b992595b5d7b44184')}


def main():
    assert os.uname().machine=='aarch64' and PROJECT.is_dir() and DOWNLOADS.is_dir()
    receipt=PROJECT/'vision-fota-cache-01.json';assert not receipt.exists()
    rows=[]
    with tempfile.TemporaryDirectory(prefix='vision-fota-cache-',dir=PROJECT/'.tmp') as temporary:
        stage=Path(temporary)
        for name,(digest,urls) in ARCHIVES.items():
            target=DOWNLOADS/name;assert not target.is_symlink()
            if not target.exists():
                source=stage/name
                for url in urls:
                    try:
                        with urllib.request.urlopen(url,timeout=45) as response:
                            assert response.geturl().startswith('https://')
                            raw=response.read(64*1024**2+1);assert len(raw)<=64*1024**2
                        assert hashlib.sha256(raw).hexdigest()==digest
                        source.write_bytes(raw);source.chmod(0o644);os.rename(source,target);break
                    except urllib.error.HTTPError:
                        if url==urls[-1]:raise
            assert target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==digest
            rows.append(dict(name=name,sha256=digest,bytes=target.stat().st_size))
            print(json.dumps(dict(stage='pinned-source',name=name,state='READY')),flush=True)
        (DOWNLOADS/'git2').mkdir(exist_ok=True)
        for name,(url,revision) in REPOSITORIES.items():
            target=DOWNLOADS/'git2'/name;assert not target.is_symlink()
            if not target.exists():
                source=stage/name
                subprocess.run(['git','clone','--bare','--mirror',url,str(source)],check=True,capture_output=True,timeout=180)
                assert subprocess.check_output(['git','--git-dir='+str(source),'rev-parse',revision+'^{commit}'],text=True).strip()==revision
                os.rename(source,target)
            assert subprocess.check_output(['git','--git-dir='+str(target),'rev-parse',revision+'^{commit}'],text=True).strip()==revision
            rows.append(dict(name=name,revision=revision));print(json.dumps(dict(stage='pinned-source',name=name,state='READY')),flush=True)
    value=dict(outcome='PASS_PINNED_SOURCE_CACHE_ACQUISITION',sources=rows,bitbakeNetworkGuardChanged=False)
    receipt.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value),flush=True)


if __name__=='__main__':main()

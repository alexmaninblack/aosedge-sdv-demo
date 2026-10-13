# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit current native/UI sources beside retained historical binary inputs."""
from pathlib import Path
import re
from .core import ROOT, require, read_json, atomic_json, run_command
from .sources import git, check_source

ROLES = ('integration', 'vehicle-gateway')


def validate(value, release):
    require(isinstance(value,dict) and set(value)==set(ROLES), 'Incomplete native source selection')
    for role,row in value.items():
        require(isinstance(row,dict) and set(row)=={'repository','revision'} and
                row['repository']==release.sources[role]['repository'] and
                isinstance(row['revision'],str) and re.fullmatch('[a-f0-9]{40}',row['revision']),
                'Invalid native source authority')
    return value


def location(storage,role,row):
    if role=='integration' and git(ROOT,['rev-parse','HEAD'],storage.environment())==row['revision']:
        return ROOT
    return storage.path('sources/native-ui/'+role+'/'+row['revision'])


def prepare(storage,selection,acquire,progress):
    validate(selection,storage.release);env=storage.environment();paths={}
    for role,row in selection.items():
        path=location(storage,role,row);paths[role]=path
        if path==ROOT:
            check_source(path,row,env);continue
        marker=path.parent/(path.name+'.json')
        if marker.exists():
            require(read_json(marker)==row,'Native source marker differs')
        else:
            require(acquire and not path.exists(),'Native source requires explicit preparation')
            path.parent.mkdir(parents=True,mode=0o700,exist_ok=True);atomic_json(marker,row)
        if not path.exists():path.mkdir(mode=0o700)
        if not (path/'.git').exists():
            require(not any(path.iterdir()),'Native source collision; preserved')
            git(path,['init','--quiet'],env)
        remotes=git(path,['remote'],env).splitlines()
        if not remotes:git(path,['remote','add','origin',row['repository']],env)
        require(git(path,['remote','get-url','origin'],env)==row['repository'],'Native source remote differs')
        head=run_command(['git','-C',path,'rev-parse','--verify','HEAD'],env=env)
        if head.returncode:
            require(acquire and {p.name for p in path.iterdir()}=={'.git'},'Incomplete native source; preserved')
            progress('PREPARE_NATIVE_SOURCE',role)
            # Use locally available immutable commits without another network transfer.
            local=ROOT if role=='integration' else None
            git(path,['fetch','--quiet','--depth=1','--no-tags',str(local or 'origin'),row['revision']],env,timeout=180)
            git(path,['checkout','--quiet','--detach',row['revision']],env)
        check_source(path,row,env)
    return paths


def verified(storage,selection):
    validate(selection,storage.release);paths={}
    for role,row in selection.items():
        path=location(storage,role,row);check_source(path,row,storage.environment());paths[role]=path
    return paths

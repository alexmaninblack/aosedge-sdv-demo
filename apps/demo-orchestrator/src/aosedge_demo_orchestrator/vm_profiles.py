# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fixed VM resource selections; no arbitrary QEMU/resource overrides."""

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class VMProfile:
    name: str
    cpus: int
    memory_mib: int
    test_ssh_port: int
    test_only: bool


MAIN = VMProfile('aos-main-qemuarm64-v1', 2, 2048, 10022, False)
VISION = VMProfile('aos-vision-main-qemuarm64-v1', 4, 4096, 12022, True)
PROFILES = MappingProxyType({p.name: p for p in (MAIN, VISION)})


def resolve(name):
    if type(name) is not str or name not in PROFILES:
        raise ValueError('VM_RESOURCE_PROFILE_UNSUPPORTED')
    return PROFILES[name]


def binding(state, name):
    """Legacy journals mean Main. A retained journal cannot be re-profiled."""
    profile = resolve(name)
    if state.get('vmProfile', MAIN.name) != profile.name:
        raise ValueError('VM_RESOURCE_PROFILE_BINDING_MISMATCH')
    if profile.test_only and set(state.get('vehicles', {})) != {'test'}:
        raise ValueError('VISION_VM_REQUIRES_TEST_ONLY')
    return profile

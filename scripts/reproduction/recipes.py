# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""File-level packaging recipe inputs, without importing or running an owner."""
import ast
from pathlib import Path

from .core import require, regular

APP = 'apps/demo-orchestrator/src/aosedge_demo_orchestrator'
DIST = 'scripts/distribution'
CONTRACTS = (
    'vdp-compatibility-profile/vdp-compatibility-profile.v1.json',
    'qm-advisory-profile/qm-advisory-profile.v1.json',
    'brake-telemetry-window/brake-telemetry-window-profile.v1.json',
    'brake-health-model/brake-health-model-profile.v1.json',
    'brake-health-runtime/brake-health-runtime-profile.v1.json',
    'tire-health-model/tire-health-product-profile.v1.json',
)
LOCKS = (
    'portable-host-launch/host-runtime.lock.json',
    'portable-preparation-inputs/vehicle-inputs.lock.json',
    'portable-vm-launch/vm-runtime.lock.json',
    'portable-cloud-backend-inputs/cloud-runtime.lock.json',
    'portable-cloud-backend-inputs/backend-inputs.lock.json',
)
ENTRIES = {
    'preparation': ('vehicle_inputs', 'aosedge_demo_orchestrator.components',
                    'aosedge_demo_orchestrator.component_build', 'aosedge_demo_orchestrator.service_packages'),
    'host-runtime': ('native_bundle', 'ui_helpers', 'aosedge_demo_orchestrator.host_runtime'),
    # These workers also import application and its validators before dispatch.
    'backend-inputs': ('application', 'candidate_inputs', 'installation_inputs',
                       'aosedge_demo_orchestrator.host_runtime',
                       'aosedge_demo_orchestrator.preparation_inputs', 'aosedge_demo_orchestrator.vm_runtime'),
    'vm-runtime': ('application', 'candidate_inputs', 'vm_inputs',
                   'aosedge_demo_orchestrator.host_runtime',
                   'aosedge_demo_orchestrator.preparation_inputs', 'aosedge_demo_orchestrator.vm_runtime'),
    'application': ('application', 'candidate_inputs', 'installation_inputs',
                    'aosedge_demo_orchestrator.host_runtime',
                    'aosedge_demo_orchestrator.preparation_inputs', 'aosedge_demo_orchestrator.vm_runtime'),
    'setup': ('setup_build',),
    'dmg': ('full_dmg',),
}
ADAPTERS = {
    'preparation': ('packaging', 'preparation_worker'),
    'host-runtime': ('host', 'host_worker'),
    'backend-inputs': ('package_chain', 'package_worker'),
    'vm-runtime': ('package_chain', 'package_worker'),
    'application': ('package_chain', 'package_worker'),
    'setup': ('media', 'media_worker'),
    'dmg': ('media', 'media_worker'),
}


def module_map(tracked):
    modules = {}
    for name in tracked:
        path = Path(name)
        if path.suffix != '.py':
            continue
        if path.parent.as_posix() == DIST:
            modules[path.stem] = name
        elif name.startswith(APP + '/'):
            parts = list(path.relative_to(Path(APP).parent).with_suffix('').parts)
            if parts[-1] == '__init__':
                parts.pop()
            modules['.'.join(parts)] = name
    return modules


def local_closure(root, tracked, entries):
    """Follow all static imports, including deferred imports and package initializers.

    This is conservative at module granularity, not function-level reachability.
    Non-Python inputs are explicit below and checked against owner constants in CI.
    """
    modules = module_map(tracked)
    pending, seen = list(entries), set()
    while pending:
        name = pending.pop()
        require(name in modules, 'Packaging recipe module is missing: ' + name)
        if name in seen:
            continue
        seen.add(name)
        path = modules[name]
        package = name if Path(path).name == '__init__.py' else name.rpartition('.')[0]
        if package and package != name:
            pending.append(package)
        tree = ast.parse(regular(root/path).read_bytes(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                candidates = [alias.name for alias in node.names]
                required = candidates
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    parts = package.split('.')
                    require(package and node.level <= len(parts), 'Recipe import escapes package')
                    prefix = '.'.join(parts[:len(parts)-node.level+1])
                    base = prefix + ('.' + node.module if node.module else '')
                else:
                    base = node.module or ''
                candidates = [base] + [base+'.'+alias.name for alias in node.names]
                required = [base]
            else:
                continue
            for imported in required:
                if imported.startswith('aosedge_demo_orchestrator'):
                    require(imported in modules, 'Local recipe import is missing: '+imported)
            pending.extend(candidate for candidate in candidates if candidate in modules)
    return {modules[name] for name in seen}


def paths(root, tracked, target):
    require(target in ENTRIES, 'Unknown packaging recipe target')
    chosen = local_closure(root, tracked, ENTRIES[target])
    # Shared guard/identity helpers remain dependencies of every adapter.
    chosen.update('scripts/reproduction/'+name+'.py' for name in
                  ('core', 'sources', 'artifacts', 'cloud', 'packaging', 'recipes', *ADAPTERS[target]))
    chosen.add('scripts/validate-release-definition')
    chosen.add('workspace/releases/release.schema.json')
    if target in ('host-runtime', 'backend-inputs', 'vm-runtime', 'application', 'setup', 'dmg'):
        chosen.add('scripts/reproduction/host.py')
    if target == 'host-runtime':
        chosen.update(('scripts/reproduction/build.py', 'scripts/reproduction/gateway.py',
                       'workspace/gateway-build-sdk.lock.json'))
    if target in ('backend-inputs', 'vm-runtime', 'application', 'setup', 'dmg'):
        chosen.add('scripts/reproduction/build_results.py')
        chosen.update(('scripts/reproduction/package_chain.py', 'scripts/reproduction/containers.py'))
        chosen.add('workspace/releases/1.2.0-rc.1-packaging.json')
        chosen.add('workspace/releases/kit028-setup042.json')
        # candidate_inputs validates every declared group, not just the output group.
        chosen.update('contracts/'+name for name in LOCKS)
    if target == 'preparation':
        chosen.update(('scripts/reproduction/services.py',
                       'workspace/checkpoints/reproduction-services-20261008.json',
                       'workspace/checkpoints/factory-41-candidate.json',
                       'workspace/checkpoints/factory-41-source-20261008.json',
                       'workspace/distribution-stage0-inventory.json', 'LICENSE'))
        chosen.update('contracts/'+name for name in CONTRACTS)
    if target == 'vm-runtime':
        chosen.update(('scripts/host/aosvm-dns-bridge', 'LICENSE'))
    if target in ('application', 'setup'):
        # Every Python module is exported, even when a build does not import it.
        chosen.update(name for name in tracked if name.startswith(APP+'/') and name.endswith('.py'))
        chosen.update(('LICENSE', 'workspace/repositories.json', 'config/aosvm-single-node-unitconfig.json',
                       'contracts/qm-advisory-profile/advisory-readiness.v1.json'))
        chosen.update('contracts/'+name for name in CONTRACTS)
    if target in ('setup', 'dmg'):
        chosen.add('workspace/releases/1.2.0-rc.1-setup.json')
        # Kept even for successor mode: release() remains an imported fallback guard.
        chosen.add(DIST+'/setup_release.json')
    if target == 'setup':
        chosen.add(DIST+'/native/Setup.swift')
        # Shipped helper inputs are not necessarily imported during compilation.
        chosen.update(local_closure(root, tracked, ('setup_bridge', 'setup_cloud', 'setup_launch',
                                                  'setup_backends', 'installation',
                                                  'installation_inputs', 'version_management')))
    require(chosen <= set(tracked), 'Packaging recipe input is missing or untracked')
    return sorted(chosen)

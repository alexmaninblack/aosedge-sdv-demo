# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fixed staging journey and pure postconditions; no product effects here."""

MUTATIONS = {'dependency', 'setup', 'vm-access', 'presenter-start', 'presenter', 'control', 'mode', 'poweroff', 'shutdown', 'restore'}

# A shutdown changes the experimental conditions. Do not combine observations
# across it into a passing Reset, offline or ignition result.
CONTINUOUS_GROUPS = (
    ('reset-brake-before', 'reset-brake-independent'),
    ('reset-tire-before', 'reset-tire-independent'),
    ('offline-off', 'cloud-online'),
    ('ignition-before', 'ignition-preserved'),
)


def resolve(value, context):
    if isinstance(value, str) and value.startswith('$'):
        result = context
        for part in value[1:].split('.'):
            result = result[part]
        return result
    if isinstance(value, dict):
        return {key: resolve(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve(item, context) for item in value]
    return value


def evaluate(check, context):
    args = resolve(check, context)
    name = args['test']
    if name == 'equals':
        return args['actual'] == args['expected']
    if name == 'all':
        return all(evaluate(item, context) for item in check['checks'])
    if name == 'ready-vdp':
        row = args['actual']
        return (row.get('activeVersion') == args['version'] and row.get('vdpData') == 'REPORTED_READY'
                and str(row.get('vdpRestarts')) == '0' and row.get('processSlotMatches') is True)
    if name == 'ready-service':
        return any(row.get('version') == args['version'] and row.get('run_state') == 'active'
                   and not row.get('error_message') and row.get('error_exit_code') in (0, None)
                   for row in args['actual'].get('instances', []))
    if name == 'published-service':
        row = args['actual']
        return (row.get('stage') == 'READY' and row.get('source') == 'AOS_CLOUD_ONLY'
                and row.get('version') == args['version'] and row.get('serviceId') == args['serviceId']
                and bool(row.get('deploymentId')) and bool(row.get('versionId')))
    if name == 'new-product':
        old = set(args['before']['productIds'])
        return any(row['id'] not in old and row['version'] == args['version']
                   for row in args['actual']['products'])
    if name == 'receiving-inputs':
        return any(row.get('version') == args['version'] and row.get('fresh') is True
            and row.get('connection') == 'CONNECTED' and row.get('input') == 'RECEIVING'
            and row.get('inputReason') == 'NONE' and isinstance(row.get('instance'), dict)
            and bool(row['instance'].get('instanceId'))
            for row in args['actual'].get('functions', []))
    if name == 'restarted-inputs':
        # VDP readiness does not mean each consumer has finished authorization
        # and subscription. Require a fresh post-restart producer generation,
        # not a still-green retained observation from the previous boot.
        before = [r for r in args['before'].get('functions', []) if r.get('version') == args['version']]
        after = [r for r in args['actual'].get('functions', []) if r.get('version') == args['version']]
        return any(row.get('fresh') is True and row.get('connection') == 'CONNECTED'
            and row.get('input') == 'RECEIVING' and row.get('inputReason') == 'NONE'
            and type(row.get('generation')) is int
            and any(row.get('instance') == old.get('instance') and type(old.get('generation')) is int
                and row['generation'] > old['generation'] for old in before)
            for row in after)
    if name == 'advisory-applied':
        old = set(args.get('before', {}).get('productIds', []))
        eligible = set(args['actual']['productIds']) - old
        # D4-016.4: initial Brake V3 activation uses the persisted V2 condition;
        # refreshes keep that decision even after a newer assessment arrives.
        if args.get('activationSourceVersion'):
            eligible.update(row['id'] for row in args['actual'].get('products', [])
                if row['id'] in old and row['version'] == args['activationSourceVersion']
                and row.get('quality') == 'VALID_DEMO_SYNTHETIC'
                and row.get('currentBand') == 'INSPECTION_RECOMMENDED')
        return any(row['version'] == args['version'] and row['state'] == 'APPLIED'
                   and row['assessmentId'] in eligible
                   for row in args['actual'].get('advisories', []))
    if name == 'safe-stop':
        row = args['actual']['controller']
        return (row['fresh'] and not row['held'] and row['mode'] == 'SAFE_STOP'
                and row['speed'] <= .5 and row['brake'] >= .99)
    if name == 'autopilot-moving':
        row = args['actual']['controller']
        return (row.get('fresh') is True and row.get('held') is False and row.get('mode') == 'AUTOPILOT'
                and type(row.get('speed')) in (int, float) and row['speed'] > 1)
    if name == 'reset-independent':
        before, after, team, other = args['before'], args['after'], args['team'], args['other']
        return (after[team]['resetState'] == 'CLEARED'
                and after[team]['resetId'] == args['commandId']
                and before['local']['teams'][other]['model'] == after['local']['teams'][other]['model']
                and all(set(before[t]['productIds']) <= set(after[t]['productIds']) for t in ('brake', 'tire')))
    if name == 'offline':
        before, after = args['before'], args['after']
        return (after['local']['bootId'] == before['local']['bootId']
                and after['local']['identity'] == before['local']['identity']
                and all(s['ActiveState'] == 'active' and s['Result'] == 'success'
                        and s['NRestarts'] == '0' for s in after['local']['services'].values())
                and bool(after['local']['services'])
                and all(before[t]['productIds'] == after[t]['productIds'] for t in ('brake', 'tire'))
                and all(after['local']['teams'][t]['queuedIds'] for t in ('brake', 'tire')))
    if name == 'offline-progress':
        before, after = args['before'], args['after']
        return evaluate(dict(test='offline', before=before, after=after), {}) and all(
            before['local']['teams'][t]['model'] != after['local']['teams'][t]['model'] for t in ('brake', 'tire'))
    if name == 'recovered':
        before, after = args['before'], args['after']
        return (before['local']['bootId'] == after['local']['bootId'] and all(
            not after['local']['teams'][t]['queuedIds'] and
            set(before['local']['teams'][t]['queuedAssessmentIds']) <= set(after[t]['productIds'])
            for t in ('brake', 'tire')))
    if name == 'ignition':
        before, after = args['before'], args['after']
        return (before['local']['bootId'] != after['local']['bootId']
            and before['local']['identity'] == after['local']['identity']
            and evaluate(dict(test='safe-stop', actual=after['local']), {})
            and all(before['local']['teams'][t]['model'] == after['local']['teams'][t]['model']
                    and set(before[t]['productIds']) <= set(after[t]['productIds']) for t in ('brake', 'tire')))
    raise ValueError('UNKNOWN_POSTCONDITION')


def plan(config):
    steps = []
    def add(identity, kind, **extra):
        steps.append(dict(id=identity, kind=kind, **extra))
    def op(identity, action, **args):
        add(identity, 'presenter', args=dict(action=action, **args), timeout=360)
    def read(identity, query, until=None, **args):
        row = dict(args=dict(query=query, **args), timeout=180)
        if until: row['until'] = until
        add(identity, 'observe', **row)
    def maneuver(identity, team):
        add(identity, 'control', args=dict(action='exercise', team=team), timeout=90)
    def sample(identity):
        read(identity, 'combined')
    def vdp(profile):
        key = 'vdp-' + profile
        add(key+'-safe', 'mode', args=dict(mode='safe_stop'), timeout=30)
        read(key+'-safe-observed', 'local', dict(test='safe-stop', actual='$sample'))
        if profile == 'v1':
            # Existing Test-set releases can arrive immediately at provisioning.
            # Let that already-issued update settle before publishing a new one.
            read(key+'-prior-update-settled', 'component-idle',
                 dict(test='equals', actual='$sample.idle', expected=True))
        op(key+'-prepare', 'prepare', profile=profile)
        op(key+'-publish', 'publish', version='$'+key+'-prepare.version')
        read(key+'-ready', 'component', dict(test='ready-vdp', actual='$sample', version='$'+key+'-prepare.version'))
    def service(team, profile, first=False):
        key = team + '-' + profile
        op(key+'-prepare', 'service-prepare', team=team, profile=profile)
        op(key+'-publish', 'service-publish', release='$'+key+'-prepare.release')
        read(key+'-published', 'publication', dict(test='published-service', actual='$sample',
             version='$'+key+'-prepare.version', serviceId='$'+key+'-publish.serviceId'),
             release='$'+key+'-prepare.release')
        if first: op(key+'-assign', 'service-assign', serviceId='$'+key+'-publish.serviceId')
        read(key+'-ready', 'service', dict(test='ready-service', actual='$sample', version='$'+key+'-prepare.version'), team=team)
        read(key+'-before', 'backend', team=team)
        maneuver(key+'-maneuver', team)
        read(key+'-product', 'backend', dict(test='new-product', actual='$sample',
             before='$'+key+'-before', version='$'+key+'-prepare.version'), team=team)
        if team == 'tire' or profile == 'v3':
            check = dict(test='advisory-applied', actual='$sample',
                         version='$'+key+'-prepare.version', before='$'+key+'-before')
            if team == 'brake' and profile == 'v3':
                check['activationSourceVersion'] = '$brake-v2-prepare.version'
            read(key+'-advisory', 'backend', check, team=team)
    add('installed', 'observe', args=dict(query='installed'))
    add('docker', 'dependency', timeout=120)
    add('backend-images', 'setup', args=dict(action='prepare-backends'), timeout=180)
    add('cloud-pair', 'setup', args=dict(action='cloud-pair'), timeout=150)
    add('cloud-ready', 'setup', args=dict(action='cloud-check'), timeout=150)
    add('vm-access', 'vm-access', timeout=30)
    add('cloud-subjects', 'setup', args=dict(action='cloud-subjects'), timeout=150)
    add('presenter', 'presenter-start', timeout=90)
    op('controller-create', 'create', image=config['image'])
    op('controller-start', 'start-vms')
    # Provision binds Gateway credentials before Test-set membership only
    # when the simulator is already running. Membership may immediately
    # offer the existing Cloud component, so starting simulation later can
    # deadlock first onboarding against an active FOTA transaction.
    op('simulation', 'start-simulation')
    op('provision', 'provision')
    op('connect', 'connect-test')
    vdp('v1'); service('brake', 'v1', first=True)
    vdp('v2'); service('brake', 'v2')
    vdp('v3'); service('brake', 'v3'); service('tire', 'v1', first=True)
    for team, other in (('brake', 'tire'), ('tire', 'brake')):
        sample('reset-'+team+'-before')
        op('reset-'+team, 'backend-reset', team=team)
        read('reset-'+team+'-cleared', 'backend', dict(test='equals', actual='$sample.resetState', expected='CLEARED'), team=team)
        sample('reset-'+team+'-after')
        add('reset-'+team+'-independent', 'assert', check=dict(test='reset-independent',
            before='$reset-'+team+'-before', after='$reset-'+team+'-after', team=team, other=other,
            commandId='$reset-'+team+'.commandId'))
    add('return-to-road', 'control', args=dict(action='return-to-road'), timeout=60)
    add('offline-off', 'control', args=dict(action='connectivity-off'), timeout=60)
    sample('offline-before')
    maneuver('offline-brake', 'brake'); maneuver('offline-tire', 'tire')
    sample('offline-after')
    add('offline-local-progress', 'assert', check=dict(test='offline-progress', before='$offline-before', after='$offline-after'))
    add('offline-soak', 'hold', args=dict(query='combined'), seconds=300,
        check=dict(test='offline', before='$offline-before', after='$sample'), timeout=60)
    read('cloud-offline', 'platform', dict(test='equals', actual='$sample.online', expected='OFFLINE'))
    sample('offline-final')
    add('offline-on', 'control', args=dict(action='connectivity-on'), timeout=60)
    read('offline-delivered', 'combined', dict(test='recovered', before='$offline-final', after='$sample'))
    read('cloud-online', 'platform', dict(test='equals', actual='$sample.online', expected='ONLINE'))
    add('ignition-safe', 'mode', args=dict(mode='safe_stop'), timeout=30)
    read('ignition-safe-observed', 'local', dict(test='safe-stop', actual='$sample'))
    sample('ignition-before')
    add('ignition-off', 'poweroff', timeout=30)
    read('ignition-stopped', 'snapshot', dict(test='equals', actual='$sample.process', expected='STOPPED'))
    op('ignition-on', 'start-vms')
    read('ignition-vdp-ready', 'component', dict(test='ready-vdp', actual='$sample', version='$vdp-v3-prepare.version'))
    sample('ignition-after')
    add('ignition-preserved', 'assert', check=dict(test='ignition', before='$ignition-before', after='$ignition-after'))
    for team in ('brake', 'tire'):
        key = 'brake-v3' if team == 'brake' else 'tire-v1'
        read('ignition-'+team+'-inputs', 'backend', dict(test='restarted-inputs', actual='$sample',
            before='$ignition-before.'+team, version='$'+key+'-prepare.version'), team=team)
        maneuver('ignition-'+team+'-maneuver', team)
        read('ignition-'+team+'-product', 'backend', dict(test='new-product', actual='$sample',
            before='$ignition-before.'+team, version='$'+key+'-prepare.version'), team=team)
    # Finish is deliberately a separately scoped endpoint, never default cleanup.
    add('shutdown', 'shutdown', timeout=120)
    return steps

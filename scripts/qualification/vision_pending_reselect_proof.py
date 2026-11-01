# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Exact in-memory candidate for Source generation refresh during first wait."""
RESUME=r'''
def resume_initial_projection(request,trust,item,material,expected):
    require(request['action'] in ('trust-configure','trust-restore'),'FIRST_INSTALL_RESUME_ONLY')
    before=first_install_state()
    selected=INPUTS/'selected.json';binding=INPUTS/'viss-update-binding'
    old={path:read(path,0o644) for path in (selected,binding)}
    previous_selected=json.loads(old[selected]);previous_binding=json.loads(old[binding])
    next_selected=json.loads(expected[selected][0]);next_binding=json.loads(expected[binding][0])
    previous_generation=previous_selected['selectedSource']['assignmentGeneration']
    generation=next_selected['selectedSource']['assignmentGeneration']
    require(type(previous_generation) is int and type(generation) is int
        and 1<=previous_generation<=generation<2**63
        and previous_binding['assignmentGeneration']==previous_generation,'FIRST_INSTALL_RESUME_GENERATION_INVALID')
    previous_selected['selectedSource']['assignmentGeneration']=generation
    previous_binding['assignmentGeneration']=generation
    require(previous_selected==next_selected and previous_binding==next_binding,'FIRST_INSTALL_RESUME_IDENTITY_CHANGED')
    persistent={path:value for path,value in expected.items() if path not in (DROPIN,selected,binding)}
    require(all(read(path,mode)==value for path,(value,mode) in persistent.items()),'FIRST_INSTALL_RESUME_ENROLLMENT_CHANGED')
    present=os.path.lexists(DROPIN)
    require(not present or read(DROPIN,0o644)==expected[DROPIN][0],'FIRST_INSTALL_RESUME_DROPIN_CONFLICT')
    validate_material(trust,item,material)
    trust.call(['systemctl','--no-block','stop','aos-sm.service'])
    try:
        deadline=time.monotonic()+20
        while True:
            values=dict(line.split('=',1) for line in trust.call([
                'systemctl','show','aos-sm.service','-p','ActiveState','-p','Job']).splitlines() if '=' in line)
            if values.get('ActiveState')=='inactive' and values.get('Job') in ('','0'):break
            require(time.monotonic()<deadline,'FIRST_INSTALL_WRITER_STOP_TIMEOUT');time.sleep(.25)
        require(first_install_state()==before,'FIRST_INSTALL_STATE_CHANGED')
        require(all(read(path,mode)==value for path,(value,mode) in persistent.items())
            and all(read(path,0o644)==value for path,value in old.items()),'FIRST_INSTALL_RESUME_INPUT_CHANGED')
        require(os.path.lexists(DROPIN)==present and (not present or read(DROPIN,0o644)==expected[DROPIN][0]),'FIRST_INSTALL_RESUME_DROPIN_CONFLICT')
        for path in (selected,binding,DROPIN):
            value,mode=expected[path];trust.write(path,value,mode)
        require(first_install_state()==before,'FIRST_INSTALL_STATE_CHANGED')
        trust.call(['systemctl','daemon-reload'])
    except BaseException:
        trust.call(['systemctl','--no-block','start','aos-sm.service'])
        raise
    trust.activate_consumers(['aos-sm.service'])
    return dict(configured=True,noOp=False,smRestarted=True,resumedPendingFirstInstall=True,
        persistentEnrollmentUnchanged=True,transactionPreservedAtResume=True,**status(trust))
'''

BRANCH='''    if transaction.exists() or transaction.is_symlink():
        if all(path.is_file() and not path.is_symlink() for path in expected):
            if all(read(path,mode)==value for path,(value,mode) in expected.items()):
                return dict(configured=True,noOp=True,smRestarted=False,**status(trust))
            return resume_initial_projection(request,trust,item,material,expected)
        if all(path.is_file() and not path.is_symlink() for path in expected if path!=DROPIN):
            return resume_initial_projection(request,trust,item,material,expected)
        return initial_projection(request,trust,item,material,expected)
'''


def candidate(source):
    begin=source.index('    if transaction.exists() or transaction.is_symlink():')
    end=source.index('    changed = False',begin)
    return source[:begin]+BRANCH+source[end:]+RESUME

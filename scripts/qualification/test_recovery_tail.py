# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from recovery_tail import recovery_plan, release_context, continued_context


class RecoveryGuards(unittest.TestCase):
    def test_interrupted_native_gate_needs_separate_completed_installed_checks(self):
        pilot=dict(outcome='FAIL',scenario='release-continuation',candidate='a'*64,test='bound',ownersClosed=True)
        browser=dict(outcome='FAIL',scenario='release-continuation',stages=[dict(stage=s,outcome='PASS')
            for s in ('vdp-v2','brake-v2','vdp-v3','brake-v3','tire-v1')]+[
                dict(stage='return-to-road',outcome='FAIL',code='NATIVE_UI_BROKER_UNAVAILABLE')])
        events=[]
        for i,(action,team,profile,v) in enumerate((('prepare',None,'v3','152.0.0'),
                ('service-prepare','brake','v3','129.0.0'),('service-prepare','tire','v1','65.0.0'))):
            events += [dict(state='DISPATCH_INTENT',requestId=str(i),action=action,team=team,profile=profile),
                       dict(requestId=str(i),productState='COMPLETED',version=v)]
        installed=dict(pilot,outcome='PASS',scenario='installed')
        installed_browser=dict(outcome='PASS',scenario='installed',stages=[dict(stage=s,outcome='PASS')
            for s in ('installed-details','brake-independent-reset','tire-independent-reset','confirmed-stop')])
        self.assertEqual(continued_context(pilot,browser,events,installed,installed_browser,'a'*64,'bound')
                         ['tire-v1-prepare']['version'],'65.0.0')
        for change in ({'outcome':'FAIL'},{'test':'other'},{'ownersClosed':False}):
            with self.assertRaises(ValueError):
                continued_context(pilot,browser,events,dict(installed,**change),installed_browser,'a'*64,'bound')
        with self.assertRaises(ValueError):
            continued_context(pilot,dict(browser,stages=browser['stages'][:-1]),events,
                              installed,installed_browser,'a'*64,'bound')
        with self.assertRaises(ValueError):
            continued_context(pilot,browser,events[:-1],installed,installed_browser,'a'*64,'bound')
    def test_scope_has_no_create_publication_assignment_or_deletion(self):
        steps = recovery_plan(dict(image='6.1.1-maninblack.41/main-qemuarm64'))
        self.assertEqual(steps[-1]['id'],'shutdown')
        self.assertEqual(next(s for s in steps if s['id']=='offline-soak')['seconds'],300)
        self.assertFalse(any(s.get('args',{}).get('action') in
            ('create','prepare','publish','service-publish','service-assign','provision','reset') for s in steps))
        self.assertIn('ignition-off',[s['id'] for s in steps])
        self.assertIn('demo-restart-tire-product',[s['id'] for s in steps])

    def test_context_requires_completed_correlated_versions_and_same_candidate(self):
        pilot=dict(outcome='PASS',scenario='release-continuation',candidate='a'*64,test='bound',ownersClosed=True)
        browser=dict(outcome='PASS',scenario='release-continuation',stages=[dict(stage=s,outcome='PASS')
            for s in ('vdp-v3','brake-v3','tire-v1','confirmed-stop')])
        events=[]
        for i,(action,team,profile,v) in enumerate((('prepare',None,'v3','152.0.0'),
                ('service-prepare','brake','v3','129.0.0'),('service-prepare','tire','v1','65.0.0'))):
            events += [dict(state='DISPATCH_INTENT',requestId=str(i),action=action,team=team,profile=profile),
                       dict(requestId=str(i),productState='COMPLETED',version=v)]
        self.assertEqual(release_context(pilot,browser,events,'a'*64,'bound')['vdp-v3-prepare']['version'],'152.0.0')
        for change in ({'outcome':'FAIL'},{'candidate':'b'*64},{'test':'other'},{'ownersClosed':False}):
            with self.assertRaises(ValueError): release_context(dict(pilot,**change),browser,events,'a'*64,'bound')
        with self.assertRaises(ValueError): release_context(pilot,browser,events[:-1],'a'*64,'bound')


if __name__ == '__main__': unittest.main()

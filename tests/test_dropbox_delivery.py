# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from release_automation import CampaignError, atomic, configuration, execute, read
from reproduction import dropbox_delivery as d
from reproduction.artifacts import identity

URL='https://www.dropbox.com/scl/fi/file_public_123/AosEdge-SDV-Lab-1.2.0-rc.3.dmg?rlkey=reader_public_123&dl=1'
ACCOUNT='dbid:approved_account_123'


class Cloud:
    def __init__(self):
        self.data=bytearray();self.remote=None;self.shared=[];self.calls=[];self.fail=None
        self.sessions=0;self.appends=0;self.finishes=0;self.links_created=0
    def client(self):return FakeClient(self)


class FakeClient:
    def __init__(self, cloud):self.cloud=cloud
    def preflight(self, folder, size):
        self.cloud.calls.append(('preflight',size));return 'id:approved_folder'
    def metadata(self, path):
        self.cloud.calls.append(('metadata',path));return self.cloud.remote
    def links(self,path):
        self.cloud.calls.append(('links',path));return list(self.cloud.shared)
    def call(self, route, value=None, *, data=None):
        c=self.cloud;c.calls.append((route,value))
        if route.startswith('files/upload_session/'):
            blocks=b''.join(hashlib.sha256(data[n:n+4*2**20]).digest()
                            for n in range(0,len(data),4*2**20))
            assert value['content_hash']==hashlib.sha256(blocks).hexdigest()
        if route.endswith('/start'):
            assert data==b'';c.sessions+=1;result={'session_id':'private_upload_session'}
        elif route.endswith('/append_v2'):
            cursor=value['cursor'];assert cursor['session_id']=='private_upload_session'
            if cursor['offset']!=len(c.data):
                raise d.APIError(409,{'.tag':'incorrect_offset','correct_offset':len(c.data)})
            if data:c.appends+=1;c.data.extend(data)
            result=None
        elif route.endswith('/finish'):
            assert data==b'';assert value['commit']['mode']=='add'
            assert set(value['commit'])=={'path','mode','autorename','strict_conflict','mute'}
            assert value['commit']['autorename'] is False and value['commit']['strict_conflict'] is True
            assert value['cursor']['offset']==len(c.data)
            c.finishes+=1
            c.remote={'.tag':'file','id':'id:published_dmg','name':value['commit']['path'].rsplit('/',1)[1],
                      'path_lower':value['commit']['path'].lower(),'size':len(c.data),
                      'content_hash':hashlib.sha256(hashlib.sha256(bytes(c.data)).digest()).hexdigest(),'rev':'0123456789ab'}
            result=c.remote
        elif route=='sharing/create_shared_link_with_settings':
            assert value['path']==c.remote['id'];c.links_created+=1
            c.shared=[dict(c.remote,url=URL.replace('dl=1','dl=0'),
                link_permissions={'resolved_visibility':{'.tag':'public'},'allow_download':True})]
            result=c.shared[0]
        else:raise AssertionError(route)
        if c.fail==route and (data or route.endswith('/finish') or 'sharing/' in route):
            c.fail=None;raise CampaignError('DROPBOX_CONNECTION_INTERRUPTED')
        return result


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.source=self.root/'source.dmg'
        self.source.write_bytes(b'0123456789abcdefghijklmnop')
        self.expected=dict(productVersion='1.2.0-rc.3',file='AosEdge-SDV-Lab-1.2.0-rc.3.dmg',
                           bytes=self.source.stat().st_size,
                           sha256=hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.selected=dict(provider='dropbox',credentialFile=str(self.root/'credentials'),
                           folderPath='/releases',accountId=ACCOUNT)
        self.state=self.root/'private-upload.json';self.cloud=Cloud()
        self.addCleanup(patch.stopall);patch.object(d,'CHUNK',8).start()
    def upload(self, **kw):
        return d.upload(self.cloud.client(),self.source,self.expected,self.selected,self.state,**kw)
    def publish(self):
        with patch.object(d,'observe',return_value={'anonymousHead':True}):
            return d.publish(self.cloud.client(),self.source,self.expected,self.selected,self.state)
    def test_first_create_then_repeat_sends_payload_only_once(self):
        first=self.upload();counts=(self.cloud.sessions,self.cloud.appends,self.cloud.finishes)
        self.assertEqual(bytes(self.cloud.data),self.source.read_bytes())
        self.assertEqual(self.upload(),first)
        self.assertEqual((self.cloud.sessions,self.cloud.appends,self.cloud.finishes),counts)
        self.assertEqual(self.state.stat().st_mode & 0o777,0o600)
        self.assertNotIn('sessionId',first)
    def test_lost_append_acknowledgement_resumes_from_remote_cursor(self):
        self.cloud.fail='files/upload_session/append_v2'
        with self.assertRaisesRegex(CampaignError,'INTERRUPTED'):self.upload()
        self.assertEqual(len(self.cloud.data),8)
        self.assertEqual(read(self.state)['offset'],0);self.assertEqual(read(self.state)['inflight'],8)
        self.upload()
        self.assertEqual(bytes(self.cloud.data),self.source.read_bytes())
        self.assertEqual(self.cloud.sessions,1)
        self.assertEqual(self.cloud.appends,4)
    def test_unsent_journaled_append_is_safe_to_continue(self):
        self.cloud.fail='files/upload_session/append_v2'
        with self.assertRaises(CampaignError):self.upload()
        self.cloud.data.clear();self.cloud.appends=0
        self.upload();self.assertEqual(bytes(self.cloud.data),self.source.read_bytes())
    def test_lost_finish_response_reconciles_without_second_finish(self):
        self.cloud.fail='files/upload_session/finish'
        with self.assertRaises(CampaignError):self.upload()
        self.assertEqual(read(self.state)['phase'],'finishing')
        self.upload();self.assertEqual(self.cloud.finishes,1);self.assertEqual(self.cloud.sessions,1)
    def test_lost_sharing_response_reconciles_existing_link(self):
        self.cloud.fail='sharing/create_shared_link_with_settings'
        with self.assertRaises(CampaignError):self.publish()
        result=self.publish()
        self.assertEqual(result['downloadURL'],URL);self.assertEqual(self.cloud.links_created,1)
        self.assertEqual(self.cloud.finishes,1)
    def test_provider_hash_is_dropbox_block_hash_not_sha256(self):
        payload=self.source.read_bytes()
        with patch.object(d,'BLOCK',4):
            _,actual=d.source_hashes(self.source,self.expected,None,lambda:None)
        expected=hashlib.sha256(b''.join(hashlib.sha256(payload[n:n+4]).digest()
                                        for n in range(0,len(payload),4))).hexdigest()
        self.assertEqual(actual,expected);self.assertNotEqual(actual,self.expected['sha256'])
    def test_existing_foreign_file_is_never_replaced(self):
        self.upload();self.cloud.remote['content_hash']='f'*64
        with self.assertRaisesRegex(CampaignError,'CONFLICT'):self.upload()
        self.assertEqual(self.cloud.finishes,1)
    def test_same_bytes_changed_revision_is_rejected(self):
        self.upload();self.cloud.remote['rev']='abcdef012345'
        with self.assertRaisesRegex(CampaignError,'REVISION_CHANGED'):self.upload()
    def test_deleted_publication_cannot_silently_reupload(self):
        self.upload();self.cloud.remote=None
        with self.assertRaisesRegex(CampaignError,'FILE_MISSING'):self.upload()
        self.assertEqual(self.cloud.sessions,1)
    def test_source_change_rejects_saved_session(self):
        self.upload();self.source.write_bytes(b'x'*self.expected['bytes'])
        with self.assertRaisesRegex(CampaignError,'BINDING_CHANGED'):self.upload()
    def test_wrong_verified_source_does_not_create_session(self):
        with self.assertRaisesRegex(CampaignError,'VERIFIED_SOURCE'):
            self.upload(verified_source={'identity':identity(self.source),'sha256':'a'*64})
        self.assertEqual(self.cloud.sessions,0)
    def test_expected_sha_checked_before_any_payload(self):
        self.expected['sha256']='a'*64
        with self.assertRaisesRegex(CampaignError,'SOURCE_BYTES'):self.upload()
        self.assertEqual(self.cloud.sessions,0)
    def test_folder_or_account_rebinding_is_rejected(self):
        self.upload();self.selected['accountId']='dbid:foreign_account_123'
        with self.assertRaisesRegex(CampaignError,'BINDING_CHANGED'):self.upload()
    def test_shared_link_must_match_file_revision_and_public_download_permission(self):
        self.publish()
        for field,value in [('rev','abcdef012345'),('id','id:other'),('path_lower','/other')]:
            original=self.cloud.shared[0][field];self.cloud.shared[0][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(CampaignError,'PUBLIC_LINK'):
                self.publish()
            self.cloud.shared[0][field]=original
        self.cloud.shared[0]['link_permissions']['allow_download']=False
        with self.assertRaisesRegex(CampaignError,'PUBLIC_LINK'):self.publish()
        self.assertEqual(self.cloud.links_created,1)
    def test_publication_reverification_performs_no_mutation(self):
        facts=self.publish();self.cloud.calls.clear()
        with patch.object(d,'observe',return_value={'anonymousHead':True}):
            d.verify(self.cloud.client(),self.expected,self.selected,facts)
        self.assertFalse(any('session/' in route or 'create_shared' in route for route,_ in self.cloud.calls))
    def test_late_remote_revision_change_prevents_publication_success(self):
        def changed(*args):
            self.cloud.remote['rev']='abcdef012345'
            return {'anonymousHead':True}
        with patch.object(d,'observe',side_effect=changed):
            with self.assertRaisesRegex(CampaignError,'REVISION_CHANGED'):
                d.publish(self.cloud.client(),self.source,self.expected,self.selected,self.state)
    def test_reconcile_unknown_destination_refuses_new_upload(self):
        self.upload();self.state.unlink()
        with self.assertRaisesRegex(CampaignError,'UNRECORDED'):
            d.reconcile(self.cloud.client(),self.source,self.expected,self.selected,self.state)
    def test_offset_outside_last_attempt_is_rejected(self):
        self.cloud.fail='files/upload_session/append_v2'
        with self.assertRaises(CampaignError):self.upload()
        self.cloud.data.extend(b'foreign')
        with self.assertRaisesRegex(CampaignError,'RECONCILIATION'):self.upload()
    def test_public_head_failure_cannot_promote_catalog(self):
        import release_automation as release
        cloud=self.cloud;parent=self
        class Owner:
            def __init__(self):self.calls=[]
            def stage(self,name):
                self.calls.append(name)
                if name=='publication':
                    with patch.object(d,'observe',side_effect=CampaignError('DROPBOX_HEAD_FAILED')):
                        d.publish(cloud.client(),parent.source,parent.expected,parent.selected,parent.state)
                return {'stage':name}
        owner=Owner();result=execute(self.root/'campaign',{'source':'frozen'},owner,emit=lambda _:None)
        self.assertEqual(result['outcome'],'UNCERTAIN')
        self.assertNotIn('operator-promotion',owner.calls)
    def test_automatic_url_flows_into_existing_catalog_projection(self):
        from unittest.mock import patch
        import release_operator_proof as op
        (self.root/'workspace/releases').mkdir(parents=True)
        catalog={'catalogRevision':4,'operator':{'setupBundle':'signed Setup'}}
        target=self.root/'workspace/launcher-catalog.json';target.write_text(json.dumps(catalog))
        expected=dict(self.expected,status='ENGINEERING_CANDIDATE_NOT_QUALIFIED',
                      manifestSha256='b'*64,notarized=False)
        with patch.object(op,'ROOT',self.root),patch.object(op,'descriptor',return_value=expected):
            relative,raw,projected=op.project(SimpleNamespace(config={'version':'1.2.0-rc.3'}),self.publish())
        result=json.loads(projected)
        self.assertEqual(result['operator']['downloadURL'],URL)
        self.assertEqual(result['catalogRevision'],5)
        self.assertEqual(result['operator']['setupBundle'],'signed Setup')
        self.assertIn('dropbox-delivery.json',relative)
        self.assertEqual(json.loads(target.read_text()),catalog)


class ClientSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.credentials=self.root/'credentials.json'
        atomic(self.credentials,dict(schemaVersion=1,appKey='public_app_key',
            refreshToken='never-log-this-refresh-token',accountId=ACCOUNT,scopes=sorted(d.SCOPES)))
    def test_refresh_is_cached_and_no_bearer_in_request_url(self):
        client=d.Client(self.credentials,ACCOUNT)
        with patch.object(d,'token_request',return_value={'access_token':'private_token','expires_in':14400}) as refresh:
            self.assertEqual(client.access_token(),'private_token');self.assertEqual(client.access_token(),'private_token')
            self.assertEqual(refresh.call_count,1)
    def test_expired_access_token_is_renewed_without_login(self):
        client=d.Client(self.credentials,ACCOUNT)
        with patch.object(d,'token_request',side_effect=[{'access_token':'first','expires_in':3600},
                                                       {'access_token':'second','expires_in':3600}]) as refresh:
            client.access_token();client.expires=0
            self.assertEqual(client.access_token(),'second');self.assertEqual(refresh.call_count,2)
    def test_public_credentials_and_unexpected_scopes_are_rejected(self):
        os.chmod(self.credentials,0o644)
        with self.assertRaises(CampaignError):d.Client(self.credentials,ACCOUNT)
        os.chmod(self.credentials,0o600);value=read(self.credentials);value['scopes'].append('files.content.read')
        atomic(self.credentials,value)
        with self.assertRaises(CampaignError):d.Client(self.credentials,ACCOUNT)
    def test_wrong_account_is_rejected(self):
        with self.assertRaises(CampaignError):d.Client(self.credentials,'dbid:foreign_account_123')
    def test_authenticated_redirects_and_unknown_endpoints_are_refused(self):
        client=d.Client(self.credentials,ACCOUNT)
        with self.assertRaisesRegex(CampaignError,'ENDPOINT'):client.call('files/delete_v2',{})
        with self.assertRaisesRegex(CampaignError,'REDIRECT'):
            d.NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_http_errors_never_include_response_secrets(self):
        error=HTTPError('https://api.dropboxapi.com/2/route',409,'private message',{},
                        BytesIO(b'{"error":{".tag":"path","path":{".tag":"not_found"}},"error_summary":"secret"}'))
        opener=SimpleNamespace(open=lambda *a,**kw:(_ for _ in ()).throw(error))
        with self.assertRaises(d.APIError) as result:d.response_json(opener,None)
        self.assertEqual(str(result.exception),'DROPBOX_HTTP_409')
        self.assertNotIn('secret',str(result.exception));self.assertIn('not_found',result.exception.tags)
    def test_preflight_verifies_account_folder_and_quota_before_upload(self):
        client=d.Client(self.credentials,ACCOUNT)
        def response(route,value=None):
            return {'users/get_current_account':{'account_id':ACCOUNT},
                    'users/get_space_usage':{'allocation':{'allocated':100},'used':40}}[route]
        folder={'.tag':'folder','id':'id:approved_folder','path_lower':'/releases'}
        with patch.object(client,'call',side_effect=response),patch.object(client,'metadata',return_value=folder):
            self.assertEqual(client.preflight('/releases',60),'id:approved_folder')
            with self.assertRaisesRegex(CampaignError,'CAPACITY'):client.preflight('/releases',61)
        with patch.object(client,'call',return_value={'account_id':'foreign'}):
            with self.assertRaisesRegex(CampaignError,'ACCOUNT_CHANGED'):client.preflight('/releases',0)
        with patch.object(client,'call',side_effect=response),patch.object(client,'metadata',return_value=None):
            with self.assertRaisesRegex(CampaignError,'FOLDER_UNAVAILABLE'):client.preflight('/releases',0)
    def test_auto_selection_does_not_accept_mixed_manual_locator(self):
        selected=dict(provider='dropbox',credentialFile=str(self.credentials),folderPath='/releases',accountId=ACCOUNT)
        self.assertEqual(d.selection(selected),selected)
        for extra in ({'downloadURL':URL},{'attempt':True},{'folderPath':'/../private'}):
            with self.subTest(extra=extra),self.assertRaises(CampaignError):d.selection(dict(selected,**extra))
    def test_campaign_schema_accepts_automatic_and_legacy_delivery(self):
        value=dict(schemaVersion=1,version='1.2.0-rc.3',workspace=str(self.root),volumeUUID='a'*36,
                   gateway=str(self.root/'gateway'),expectedMain={'integration':'a'*40,'gateway':'b'*40},
                   candidate={'directory':str(self.root/'candidate'),'dmgSha256':'c'*64,'manifestSha256':'d'*64},
                   remoteConfig=str(self.root/'remote'),operatorJourney=str(self.root/'journey'),
                   evidence={'campaign':str(self.root/'campaign'),'closure':str(self.root/'closure'),
                             'browser':str(self.root/'browser'),'sourcePin':'e'*64})
        choices=[dict(provider='dropbox',credentialFile=str(self.credentials),folderPath='/releases',accountId=ACCOUNT),
                 dict(provider='dropbox',downloadURL=URL),dict(folderId='public_folder_123',account='test@example.com')]
        for delivery in choices:
            path=self.root/'config';atomic(path,dict(value,delivery=delivery))
            self.assertEqual(configuration(path)['delivery'],delivery)


if __name__=='__main__':unittest.main()

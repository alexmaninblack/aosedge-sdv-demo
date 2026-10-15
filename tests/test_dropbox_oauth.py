# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs,urlsplit

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reproduction import dropbox_oauth as auth
from release_automation import CampaignError


class OAuthTests(unittest.TestCase):
    def test_offline_pkce_flow_requests_only_publisher_scopes(self):
        url=auth.authorization('public_app_key','random_state','a'*64)
        fields=parse_qs(urlsplit(url).query)
        self.assertEqual(fields['token_access_type'],['offline'])
        self.assertEqual(fields['code_challenge_method'],['S256'])
        self.assertEqual(fields['redirect_uri'],[auth.CALLBACK])
        self.assertEqual(set(fields['scope'][0].split()),auth.SCOPES)
        self.assertNotIn('files.content.read',fields['scope'][0]);self.assertNotIn('client_secret',fields)
        self.assertNotIn('a'*64,url)
    def test_callback_validates_state_path_duplicates_and_error(self):
        self.assertEqual(auth.callback_values('/dropbox/callback?code=private-code&state=expected','expected'),'private-code')
        for target in ('/other?state=expected&code=private-code',
                       '/dropbox/callback?state=foreign&code=private-code',
                       '/dropbox/callback?state=expected&code=one&code=two',
                       '/dropbox/callback?state=expected&error=access_denied'):
            with self.subTest(target=target),self.assertRaises(CampaignError):auth.callback_values(target,'expected')
    def test_credentials_are_private_and_outside_git(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();repo=root/'repo';repo.mkdir();(repo/'.git').mkdir()
            with self.assertRaisesRegex(CampaignError,'OUTSIDE_GIT'):
                auth.credential_target(repo/'private/credentials.json')
            # The scenario deliberately keeps all fixtures in its owned .tmp,
            # inside a checkout; model the outside-Git credential boundary here.
            with patch.object(auth,'in_git_tree',return_value=False):
                target=auth.credential_target(root/'private/credentials.json')
                self.assertEqual(target.parent.stat().st_mode & 0o777,0o700)
                target.write_text('preserve')
                with self.assertRaisesRegex(CampaignError,'ALREADY_CONFIGURED'):auth.credential_target(target)
    def test_folder_setup_reconciles_existing_folder_without_recreating(self):
        from types import SimpleNamespace
        calls=[];meta={'.tag':'folder','path_lower':'/releases'}
        client=SimpleNamespace(metadata=lambda p:meta,call=lambda *a,**k:calls.append(a),preflight=lambda *a:None)
        auth.initialize_folder(client,'/releases');self.assertEqual(calls,[])


if __name__=='__main__':unittest.main()

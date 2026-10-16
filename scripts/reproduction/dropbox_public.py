# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only adoption of an operator-published Dropbox DMG; never upload/login."""
import re
from urllib.parse import parse_qsl, unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


def public_link(url, *, suffix='.dmg'):
    if suffix == '.tar.gz':
        from public_drive import dropbox_link
        return dropbox_link(url)
    if suffix != '.dmg': raise ValueError('DROPBOX_LINK_INVALID')
    if not isinstance(url,str) or len(url)>4096 or re.search(r'\s',url):
        raise ValueError('DROPBOX_LINK_INVALID')
    u=urlsplit(url)
    if (u.scheme!='https' or u.netloc!='www.dropbox.com' or u.fragment or
            not re.fullmatch(r'/scl/(?:fi/[A-Za-z0-9_-]{8,200}|fo/[A-Za-z0-9_-]{8,200}/[A-Za-z0-9_-]{8,200})/[A-Za-z0-9_.%~-]{1,255}\.dmg',u.path)):
        raise ValueError('DROPBOX_LINK_INVALID')
    if re.search(r'%(?![A-Fa-f0-9]{2})',u.path):raise ValueError('DROPBOX_LINK_INVALID')
    filename=unquote(u.path.rsplit('/',1)[-1])
    if re.search(r'[/\\\x00-\x1f\x7f]',filename):raise ValueError('DROPBOX_LINK_INVALID')
    rows=parse_qsl(u.query,keep_blank_values=True,strict_parsing=True)
    fields=dict(rows)
    if (len(rows)!=len(fields) or set(fields)-{'rlkey','dl','st'} or fields.get('dl')!='1' or
            not re.fullmatch(r'[A-Za-z0-9_-]{8,200}',fields.get('rlkey','')) or
            any(not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',v) for v in fields.values())):
        raise ValueError('DROPBOX_LINK_INVALID')
    return url


def cdn_link(url):
    return isinstance(url,str) and re.fullmatch(
        r'https://(?:[a-z0-9-]{1,100}\.)?dl\.dropboxusercontent\.com/cd/0/'
        r'(?:inline|inline2|get|get2|attachment)/[A-Za-z0-9_-]{10,2048}/file\?dl=1',url) is not None


class Redirects(HTTPRedirectHandler):
    max_redirections=3
    max_repeats=1

    def redirect_request(self,request,fp,code,msg,headers,newurl):
        newurl=newurl.removesuffix('#')
        if request.get_method()!='HEAD' or not cdn_link(newurl):
            raise ValueError('DROPBOX_REDIRECT_REFUSED')
        return Request(newurl,method='HEAD')


def observe(url,expected_bytes, *, suffix='.dmg'):
    public_link(url, suffix=suffix)
    if type(expected_bytes) is not int or expected_bytes<=0:raise ValueError('DROPBOX_SIZE_INVALID')
    with build_opener(Redirects()).open(Request(url,method='HEAD'),timeout=15) as response:
        lengths=response.headers.get_all('Content-Length',[])
        if response.status!=200 or not cdn_link(response.url) or lengths!=[str(expected_bytes)]:
            raise ValueError('DROPBOX_PUBLISHED_SIZE_UNCONFIRMED')
        return dict(publicDownloadURL=url,bytes=expected_bytes,anonymousHead=True,
                    payloadDownloaded=False,providerChecksumAvailable=False,
                    consumerChecksumRequired=True)

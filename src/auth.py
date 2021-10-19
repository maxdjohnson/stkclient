import os
from typing import Optional, Mapping, Any
from dataclasses import dataclass, fields
import requests
import urllib.parse
import hashlib
import base64
import lxml.etree

class Auth:
    def __init__(self):
        self._verifier = base64_url_encode(os.urandom(32))

    def get_url(self) -> str:
        challenge = base64_url_encode(sha256(self._verifier))
        q = {
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.ns.oa2': 'http://www.amazon.com/ap/ext/oauth/2',
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.oa2.client_id': 'device:658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d',
            'openid.mode': 'checkid_setup',
            'openid.oa2.scope': 'device_auth_access',
            'openid.oa2.response_type': 'code',
            'openid.oa2.code_challenge': challenge,
            'openid.oa2.code_challenge_method': 'S256',
            'openid.return_to': 'https://www.amazon.com/gp/sendtokindle',
            'openid.ns.pape': 'http://specs.openid.net/extensions/pape/1.0',
            'openid.pape.max_auth_age': '0',
            'accountStatusPolicy': 'P1',
            'openid.assoc_handle': 'amzn_device_na',
            'pageId': 'amzn_device_common_dark',
            'disableLoginPrepopulate': '1',
        }
        return "https://www.amazon.com/ap/signin?" + urllib.parse.urlencode(q)

    def handle_redirect_url(self, redirect_url: str) -> str:
        u = urllib.parse.urlparse(redirect_url)
        q = urllib.parse.parse_qs(u.query)
        code = q['openid.oa2.authorization_code']
        body = {
            'app_name': 'Unknown',
            'client_domain': 'DeviceLegacy',
            'client_id': '658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d',
            'code_algorithm': 'SHA-256',
            'code_verifier': self._verifier,
            'requested_token_type': 'access_token',
            'source_token': code,
            'source_token_type': 'authorization_code'
        }
        r = requests.post("https://api.amazon.com/auth/token", headers={
            'Accept-Language': 'en-US',
            'x-amzn-identity-auth-domain': 'api.amazon.com',
            'User-Agent': 'Mozilla/5.0',
        }, json=body)
        return r.json()["access_token"]


@dataclass(frozen=True)
class DeviceInfo:
    device_private_key: str
    adp_token: str
    device_type: str
    given_name: str
    name: str
    account_pool: str
    user_directed_id: str
    user_device_name: str
    home_region: Optional[str] = None

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> 'DeviceInfo':
        return DeviceInfo(** {k: v for k, v in d.items() if k in {f.name for f in fields(DeviceInfo)}})


def register_device_with_token(access_token: str) -> DeviceInfo:
    '''
   curl -H 'Host: firs-ta-g7g.amazon.com'
   -H 'Content-Type: text/xml'
   -H 'Expect: '
   -H 'Accept-Language: en-US,*'
   -H 'User-Agent: Mozilla/5.0'
   --data-binary "<?xml version='1.0' encoding='UTF-8'?>
<request><parameters><deviceType>A1K6D1WRW0MALS</deviceType><deviceSerialNumber>ZYSQ37GQ5JQDAIKDZ3WYH6I74MJCVEGG</deviceSerialNumber><pid>D21NN3GG</pid><authToken>Atna|EwICIGofwj7mBEYv1EGU1e0aWC09fXjiY2nHlQTMtNwKO5kK91M3cUkv8-VfAWTYmYYL_zBlIldz2brdk5GJaWr-shhaPZzLkstyoqLbIw5FE0BX1RMxueE4JlnoSt3YFDUa4E1DWAVARD8x8Zly1gohpWX0GnH_cRPxXFRfIPv-NpJDeQ</authToken><authTokenType>AccessToken</authTokenType><softwareVersion>253</softwareVersion><os_version>MacOSX_10.14.6_x64</os_version><device_model>Max’s MacBook Pro</device_model></parameters></request>" --compressed
'https://firs-ta-g7g.amazon.com/FirsProxy/registerDeviceWithToken'
    :param access_token:
    :return:
    '''
    q = {
        "device_type": "A1K6D1WRW0MALS",
        "device_serial_number": "ZYSQ37GQ5JQDAIKDZ3WYH6I74MJCVEGG",
        "pid": "D21NN3GG",
        "auth_token": access_token,
        "auth_token_type": "AccessToken",
        "software_version": "253",
        "os_version": "MacOSX_10.14.6_x64",
        "device_model": "Max’s MacBook Pro",
    }
    body = f"""<?xml version='1.0' encoding='UTF-8'?>
<request><parameters><deviceType>{q["device_type"]}</deviceType><deviceSerialNumber>{q["device_serial_number"]}</deviceSerialNumber><pid>{q["pid"]}</pid><authToken>{q["auth_token"]}</authToken><authTokenType>{q["auth_token_type"]}</authTokenType><softwareVersion>{q["software_version"]}</softwareVersion><os_version>{q["os_version"]}</os_version><device_model>{q["device_model"]}</device_model></parameters></request>"""
    r = requests.post('https://firs-ta-g7g.amazon.com/FirsProxy/registerDeviceWithToken', headers={
        'Content-Type': 'text/xml',
        'Expect:': '',
        'Accept-Language': 'en-US,*',
        'User-Agent': 'Mozilla/5.0',
    }, body=body)
    res = safe_xml_fromstring(r.text)
    info = {}
    for el in res:
        info[el.tag] = el.text
    return DeviceInfo.from_dict(info)


def base64_url_encode(s: bytes) -> str:
    return base64.b64encode(s, b'-_').rstrip(b'=').decode('utf8')


def sha256(s: bytes) -> bytes:
    m = hashlib.sha256()
    m.update(s)
    return m.digest()


# resolving of SYSTEM entities is turned off as entities can cause
# reads of local files, for example:
# <!DOCTYPE foo [ <!ENTITY passwd SYSTEM "file:///etc/passwd" >]>


class Resolver(lxml.etree.Resolver):
    def resolve(self, url, id, context):
        return self.resolve_string('', context)


def create_parser(recover, encoding=None):
    parser = lxml.etree.XMLParser(recover=recover, no_network=True, encoding=encoding)
    parser.resolvers.add(Resolver())
    return parser


def safe_xml_fromstring(string_or_bytes, recover=True):
    return lxml.etree.fromstring(string_or_bytes, parser=create_parser(recover))

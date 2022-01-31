"""Send To Kindle Authorization."""

import base64
import hashlib
import os
import urllib.parse
import urllib.request

from stkclient import api
from stkclient.client import Client


class OAuth2:
    """Authenticates an end-user using amazon's OAuth2."""

    def __init__(self):
        """Constructs an OAuth2."""
        self._verifier = _base64_url_encode(os.urandom(32))

    def get_signin_url(self) -> str:
        """Gets the signin URL."""
        challenge = _base64_url_encode(_sha256(self._verifier.encode("utf-8")))
        q = {
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.ns.oa2": "http://www.amazon.com/ap/ext/oauth/2",
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.oa2.client_id": "device:658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d",
            "openid.mode": "checkid_setup",
            "openid.oa2.scope": "device_auth_access",
            "openid.oa2.response_type": "code",
            "openid.oa2.code_challenge": challenge,
            "openid.oa2.code_challenge_method": "S256",
            "openid.return_to": "https://www.amazon.com/gp/sendtokindle",
            "openid.ns.pape": "http://specs.openid.net/extensions/pape/1.0",
            "openid.pape.max_auth_age": "0",
            "accountStatusPolicy": "P1",
            "openid.assoc_handle": "amzn_device_na",
            "pageId": "amzn_device_common_dark",
            "disableLoginPrepopulate": "1",
        }
        return "https://www.amazon.com/ap/signin?" + urllib.parse.urlencode(q)

    def create_client(self, redirect_url: str) -> Client:
        """Creates a client with the authorization code from the redirect url."""
        code = _parse_authorization_code(redirect_url)
        access_token = api.token_exchange(code, self._verifier)
        return Client.from_access_token(access_token)


def _parse_authorization_code(redirect_url: str) -> str:
    u = urllib.parse.urlparse(redirect_url)
    q = urllib.parse.parse_qs(u.query)
    return q["openid.oa2.authorization_code"][0]


def _base64_url_encode(s: bytes) -> str:
    return base64.b64encode(s, b"-_").rstrip(b"=").decode("utf8")


def _sha256(s: bytes) -> bytes:
    m = hashlib.sha256()
    m.update(s)
    return m.digest()

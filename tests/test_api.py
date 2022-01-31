import json
from typing import Any, Dict, Tuple

import httpretty
import pytest

from stkclient import api, auth


@pytest.fixture()
def token_exchange():
    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Dict[str, Any]
    ) -> Tuple[int, Dict[str, Any], bytes]:
        assert dict(request.headers) == {
            "Accept-Encoding": "identity",
            "Content-Length": request.headers.get("Content-Length"),
            "Host": "api.amazon.com",
            "Accept-Language": "en-US",
            "X-Amzn-Identity-Auth-Domain": "api.amazon.com",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Connection": "close",
        }
        body = json.loads(request.body)
        if body.get("code_verifier") == "verifier_bad":
            return [400, response_headers, json.dumps({"error": "unauth"})]
        assert body == {
            "app_name": "Unknown",
            "client_domain": "DeviceLegacy",
            "client_id": "658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d",
            "code_algorithm": "SHA-256",
            "code_verifier": "verifier_good",
            "requested_token_type": "access_token",
            "source_token": "code_good",
            "source_token_type": "authorization_code",
        }
        return [
            200,
            response_headers,
            json.dumps(
                {"access_token": "access_token_good", "token_type": "bearer", "expires_in": 3599}
            ),
        ]

    httpretty.register_uri(
        httpretty.POST, "https://api.amazon.com/auth/token", body=request_callback
    )


def test_token_exchange_good(token_exchange):
    assert api.token_exchange("code_good", "verifier_good") == "access_token_good"


def test_token_exchange_bad(token_exchange):
    with pytest.raises(api.APIError):
        assert api.token_exchange("code_good", "verifier_bad")

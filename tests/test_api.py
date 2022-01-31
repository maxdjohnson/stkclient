import json
from typing import Any, Dict, Tuple

import httpretty
import pytest

from stkclient import api


@pytest.fixture()
def token_exchange():
    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Dict[str, Any]
    ) -> Tuple[int, Dict[str, Any], str]:
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
            return 400, response_headers, json.dumps({"error": "unauth"})
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
        return (
            200,
            response_headers,
            json.dumps(
                {"access_token": "access_token_good", "token_type": "bearer", "expires_in": 3599}
            ),
        )

    httpretty.register_uri(
        httpretty.POST, "https://api.amazon.com/auth/token", body=request_callback
    )


def test_token_exchange_good(token_exchange):
    assert api.token_exchange("code_good", "verifier_good") == "access_token_good"


def test_token_exchange_bad(token_exchange):
    with pytest.raises(api.APIError):
        assert api.token_exchange("code_good", "verifier_bad")


@pytest.fixture()
def register_device_with_token():
    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Dict[str, Any]
    ) -> Tuple[int, Dict[str, Any], str]:
        assert dict(request.headers) == {
            "Accept-Encoding": "identity",
            "Accept-Language": "en-US,*",
            "Connection": "close",
            "Content-Length": request.headers.get("Content-Length"),
            "Content-Type": "text/xml",
            "Expect": "",
            "Host": "firs-ta-g7g.amazon.com",
            "User-Agent": "Mozilla/5.0",
        }
        body = request.body.decode()
        if "access_token_bad" in body:
            return 400, response_headers, json.dumps({"error": "unauth"})
        assert (
            body
            == "<?xml version='1.0' encoding='UTF-8'?>\n<request><parameters><deviceType>A1K6D1WRW0MALS</deviceType><deviceSerialNumber>ZYSQ37GQ5JQDAIKDZ3WYH6I74MJCVEGG</deviceSerialNumber><pid>D21NN3GG</pid><authToken>access_token_good</authToken><authTokenType>AccessToken</authTokenType><softwareVersion>253</softwareVersion><os_version>MacOSX_10.14.6_x64</os_version><device_model>Maxs MacBook Pro</device_model></parameters></request>"
        )
        return (
            200,
            response_headers,
            '<?xml version="1.0" encoding="UTF-8"?>\n<response><device_private_key>mock_key</device_private_key><adp_token>mock_token</adp_token><device_type>mock_device_type</device_type><given_name>Max</given_name><name>Max</name><account_pool>Amazon</account_pool><home_region>NA</home_region><user_directed_id>mock_user_id</user_directed_id><user_device_name>Max\'s 3rd Send to Kindle for Mac</user_device_name></response>',
        )

    httpretty.register_uri(
        httpretty.POST,
        "https://firs-ta-g7g.amazon.com/FirsProxy/registerDeviceWithToken",
        body=request_callback,
    )


def test_register_device_with_token_good(register_device_with_token):
    assert api.register_device_with_token("access_token_good") == api.DeviceInfo(
        device_private_key="mock_key",
        adp_token="mock_token",
        device_type="mock_device_type",
        given_name="Max",
        name="Max",
        account_pool="Amazon",
        user_directed_id="mock_user_id",
        user_device_name="Max's 3rd Send to Kindle for Mac",
        home_region="NA",
    )


def test_register_device_with_token_bad(register_device_with_token):
    with pytest.raises(api.APIError):
        assert api.register_device_with_token("access_token_bad")

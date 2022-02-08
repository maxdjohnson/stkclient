"""Unit tests of stkclient.api using httpretty-based mock."""

import json
from pathlib import Path
from typing import Any, Mapping, Tuple
from unittest.mock import Mock

import httpretty
import pytest

from stkclient import api, model
from stkclient.signer import Signer

ADP_TOKEN_GOOD = "adp_token_good"  # noqa S105
STK_TOKEN_GOOD = "9214b056b98b44238db291b3f2bb786c"  # noqa S105


@pytest.fixture()
def token_exchange() -> None:
    """Fixture providing a mock implementation of https://api.amazon.com/auth/token."""

    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Mapping[str, Any]
    ) -> Tuple[int, Mapping[str, Any], str]:
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


def test_token_exchange_good(token_exchange: None) -> None:
    """Check that token_exchange handles a successful request/response."""
    assert api.token_exchange("code_good", "verifier_good") == "access_token_good"


def test_token_exchange_bad(token_exchange: None) -> None:
    """Check that token_exchange handles an error response."""
    with pytest.raises(api.APIError):
        assert api.token_exchange("code_good", "verifier_bad")


@pytest.fixture()
def register_device_with_token() -> None:
    """Fixture providing a mock implementation of /FirsProxy/registerDeviceWithToken."""

    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Mapping[str, Any]
    ) -> Tuple[int, Mapping[str, Any], str]:
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
            f'<?xml version="1.0" encoding="UTF-8"?>\n<response><device_private_key>mock_key</device_private_key><adp_token>{ADP_TOKEN_GOOD}</adp_token><device_type>mock_device_type</device_type><given_name>Max</given_name><name>Max</name><account_pool>Amazon</account_pool><home_region>NA</home_region><user_directed_id>mock_user_id</user_directed_id><user_device_name>Max\'s 3rd Send to Kindle for Mac</user_device_name></response>',
        )

    httpretty.register_uri(
        httpretty.POST,
        "https://firs-ta-g7g.amazon.com/FirsProxy/registerDeviceWithToken",
        body=request_callback,
    )


def test_register_device_with_token_good(register_device_with_token: None) -> None:
    """Check that register_device_with_token handles a successful request/response."""
    assert api.register_device_with_token("access_token_good") == model.DeviceInfo(
        device_private_key="mock_key",
        adp_token=ADP_TOKEN_GOOD,
        device_type="mock_device_type",
        given_name="Max",
        name="Max",
        account_pool="Amazon",
        user_directed_id="mock_user_id",
        user_device_name="Max's 3rd Send to Kindle for Mac",
        home_region="NA",
    )


def test_register_device_with_token_bad(register_device_with_token: None) -> None:
    """Check that register_device_with_token handles an API error."""
    with pytest.raises(api.APIError):
        assert api.register_device_with_token("access_token_bad")


@pytest.fixture()
def signer() -> Signer:
    """Fixture provides a mock implementation of the Signer class."""
    m = Mock(spec=Signer)
    m.adp_token = "test_adp_token"
    m.digest_header_for_request.return_value = "test_signature"
    return m


def test_get_list_of_owned_devices_good(signer: Mock) -> None:
    """Check that get_list_of_owned_devices returns the expected result."""

    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Mapping[str, Any]
    ) -> Tuple[int, Mapping[str, Any], str]:
        assert dict(request.headers) == {
            "Host": "stkservice.amazon.com",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Adp-Request-Digest": "test_signature",
            "X-Adp-Authentication-Token": "test_adp_token",
            "Content-Length": request.headers.get("Content-Length"),
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,*",
            "User-Agent": "Mozilla/5.0",
        }
        body = json.loads(request.body)
        assert body == {"ClientInfo": api.DEFAULT_CLIENT_INFO}
        res = {
            "ownedDevices": [
                {
                    "deviceCapabilities": {
                        "PDF_CONTENT_ENABLED": True,
                        "WAN_ENABLED": False,
                        "WIFI_CAPABLE": True,
                    },
                    "deviceName": "Max's 5th iPhone",
                    "deviceSerialNumber": "35C6D8B149E345848BF462CC13824AA2",
                },
                {
                    "deviceCapabilities": {
                        "PDF_CONTENT_ENABLED": True,
                        "WAN_ENABLED": False,
                        "WIFI_CAPABLE": True,
                    },
                    "deviceName": "Max's Kindle",
                    "deviceSerialNumber": "G000PP1311850V4X",
                },
            ],
            "statusCode": 0,
        }
        return 200, response_headers, json.dumps(res)

    httpretty.register_uri(
        httpretty.POST, "https://stkservice.amazon.com/GetListOfOwnedDevices", body=request_callback
    )
    res = api.get_list_of_owned_devices(signer)
    data = json.dumps({"ClientInfo": api.DEFAULT_CLIENT_INFO}, indent=4)
    signer.digest_header_for_request.assert_called_with("POST", "/GetListOfOwnedDevices", data)
    assert res == model.GetOwnedDevicesResponse(
        owned_devices=[
            model.OwnedDevice(
                device_capabilities={
                    "PDF_CONTENT_ENABLED": True,
                    "WAN_ENABLED": False,
                    "WIFI_CAPABLE": True,
                },
                device_name="Max's 5th iPhone",
                device_serial_number="35C6D8B149E345848BF462CC13824AA2",
            ),
            model.OwnedDevice(
                device_capabilities={
                    "PDF_CONTENT_ENABLED": True,
                    "WAN_ENABLED": False,
                    "WIFI_CAPABLE": True,
                },
                device_name="Max's Kindle",
                device_serial_number="G000PP1311850V4X",
            ),
        ],
        status_code=0,
    )


def test_get_upload_url_good(signer: Mock) -> None:
    """Check that get_upload_url returns the expected result."""

    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Mapping[str, Any]
    ) -> Tuple[int, Mapping[str, Any], str]:
        assert dict(request.headers) == {
            "Host": "stkservice.amazon.com",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Adp-Request-Digest": "test_signature",
            "X-Adp-Authentication-Token": "test_adp_token",
            "Content-Length": request.headers.get("Content-Length"),
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,*",
            "User-Agent": "Mozilla/5.0",
        }
        body = json.loads(request.body)
        assert body == {"ClientInfo": api.DEFAULT_CLIENT_INFO, "fileSize": 100}
        res = {
            "expiryTime": 3600000,
            "statusCode": 0,
            "stkToken": STK_TOKEN_GOOD,
            "uploadUrl": "https://send-to-kindle-prod.s3.amazonaws.com/RpaDKq?AWSAccessKeyId=AKIAQ5DT6R2IZ7ECREWD&Expires=1633759364&Signature=0Eevh%2B9ew8piKe%2BsgkeegTdTWzM%3D",
        }
        return 200, response_headers, json.dumps(res)

    httpretty.register_uri(
        httpretty.POST, "https://stkservice.amazon.com/GetUploadUrl", body=request_callback
    )
    res = api.get_upload_url(signer, 100)
    data = json.dumps({"ClientInfo": api.DEFAULT_CLIENT_INFO, "fileSize": 100}, indent=4)
    signer.digest_header_for_request.assert_called_with("POST", "/GetUploadUrl", data)
    assert res == model.GetUploadUrlResponse(
        expiry_time=3600000,
        status_code=0,
        stk_token=STK_TOKEN_GOOD,
        upload_url="https://send-to-kindle-prod.s3.amazonaws.com/RpaDKq?AWSAccessKeyId=AKIAQ5DT6R2IZ7ECREWD&Expires=1633759364&Signature=0Eevh%2B9ew8piKe%2BsgkeegTdTWzM%3D",
    )


def test_upload_file_good(tmp_path: Path) -> None:
    """Check that upload_file returns the expected result."""
    url = "https://send-to-kindle-prod.s3.amazonaws.com/RpaDKq?AWSAccessKeyId=AKIAQ5DT6R2IZ7ECREWD&Expires=1633759364&Signature=0Eevh%2B9ew8piKe%2BsgkeegTdTWzM%3D"
    file_path = tmp_path / "test.txt"
    with open(file_path, "w") as fw:
        fw.write("test file contents\n")
    file_size = file_path.stat().st_size

    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Mapping[str, Any]
    ) -> Tuple[int, Mapping[str, Any], str]:
        assert dict(request.headers) == {
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,*",
            "Content-Length": str(file_size),
            "Host": "send-to-kindle-prod.s3.amazonaws.com",
            "User-Agent": "Mozilla/5.0",
        }
        assert request.body == b"test file contents\n"
        return 200, response_headers, ""

    httpretty.register_uri(httpretty.POST, url, body=request_callback)
    with open(file_path, "rb") as fr:
        api.upload_file(url, file_size, fr)
    assert httpretty.last_request() is not None


def test_send_to_kindle_good(signer: Mock) -> None:
    """Check that send_to_kindle returns the expected result."""
    targets = ["A", "B"]
    author, title, format = "test_author", "test_title", "mobi"

    def request_callback(
        request: httpretty.core.HTTPrettyRequest, uri: str, response_headers: Mapping[str, Any]
    ) -> Tuple[int, Mapping[str, Any], str]:
        assert dict(request.headers) == {
            "Host": "stkservice.amazon.com",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Adp-Request-Digest": "test_signature",
            "X-Adp-Authentication-Token": "test_adp_token",
            "Content-Length": request.headers.get("Content-Length"),
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,*",
            "User-Agent": "Mozilla/5.0",
        }
        body = json.loads(request.body)
        assert body == {
            "ClientInfo": api.DEFAULT_CLIENT_INFO,
            "DocumentMetadata": {
                "author": author,
                "crc32": 0,
                "inputFormat": format,
                "title": title,
            },
            "archive": True,
            "deliveryMechanism": "WIFI",
            "outputFormat": "MOBI",
            "stkToken": STK_TOKEN_GOOD,
            "targetDevices": targets,
        }
        res = {"sku": "7B672AF0FA604BECA8143275166EA316", "statusCode": 0}
        return 200, response_headers, json.dumps(res)

    httpretty.register_uri(
        httpretty.POST, "https://stkservice.amazon.com/SendToKindle", body=request_callback
    )
    res = api.send_to_kindle(
        signer, STK_TOKEN_GOOD, targets, author=author, title=title, format=format
    )
    body = {
        "ClientInfo": api.DEFAULT_CLIENT_INFO,
        "DocumentMetadata": {
            "author": author,
            "crc32": 0,
            "inputFormat": format,
            "title": title,
        },
        "archive": True,
        "deliveryMechanism": "WIFI",
        "outputFormat": "MOBI",
        "stkToken": STK_TOKEN_GOOD,
        "targetDevices": targets,
    }
    data = json.dumps(body, indent=4)
    signer.digest_header_for_request.assert_called_with("POST", "/SendToKindle", data)
    assert res == model.SendToKindleResponse(sku="7B672AF0FA604BECA8143275166EA316", status_code=0)


def test_logout_good(signer: Mock) -> None:
    """Check that logout makes the expected call."""
    httpretty.register_uri(
        httpretty.GET,
        "https://firs-ta-g7g.amazon.com/FirsProxy/disownFiona?contentDeleted=false",
        body='<?xml version="1.0" encoding="UTF-8"?>\n<response><status>SUCCESS</status></response>',
    )
    api.logout(signer)
    r = httpretty.last_request()
    assert dict(r.headers) == {
        "Accept-Encoding": "identity",
        "Accept-Language": "en-US,*",
        "Connection": "close",
        "Content-Type": "text/xml",
        "Host": "firs-ta-g7g.amazon.com",
        "User-Agent": "Mozilla/5.0",
        "X-Adp-Request-Digest": "test_signature",
        "X-Adp-Authentication-Token": "test_adp_token",
    }

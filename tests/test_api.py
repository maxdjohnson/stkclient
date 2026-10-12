"""API tests with mocks at the standard-library HTTP boundary."""

import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from stkclient import api, model
from stkclient.signer import Signer

ADP_TOKEN_GOOD = "adp_token_good"
STK_TOKEN_GOOD = "9214b056b98b44238db291b3f2bb786c"
UPLOAD_URL = "https://zme-caps.amazon.com/asset/test/IMPORT_SOURCE?urlMethod=PUT&sig=test_signature"


@pytest.fixture()
def urlopen(mocker: MockerFixture) -> MagicMock:
    """Replace HTTP I/O while retaining real Request objects and response streams."""
    return mocker.patch("stkclient.api.urllib.request.urlopen", autospec=True)


@pytest.fixture()
def signer() -> Mock:
    """Provide deterministic request signatures."""
    result = Mock(spec=Signer)
    result.adp_token = ADP_TOKEN_GOOD
    result.digest_header_for_request.return_value = "test_signature"
    return result


def _request(urlopen: MagicMock, method: str, url: str) -> urllib.request.Request:
    urlopen.assert_called_once()
    request: urllib.request.Request = urlopen.call_args.args[0]
    assert request.get_method() == method
    assert request.full_url == url
    return request


def _assert_signed_request(
    urlopen: MagicMock, signer: Mock, path: str, body: Mapping[str, Any]
) -> None:
    request = _request(urlopen, "POST", "https://kd.amazon.com" + path)
    data = json.dumps({"clientInfo": api.DEFAULT_CLIENT_INFO, **body}, indent=4)
    assert request.data == data.encode("utf-8")
    assert dict(request.header_items()) == {
        "Accept": "application/json",
        "Accept-encoding": "gzip, deflate",
        "Content-type": "application/json",
        "X-adp-request-digest": "test_signature",
        "X-adp-authentication-token": ADP_TOKEN_GOOD,
        "Accept-language": "en-US,*",
        "User-agent": "Mozilla/5.0",
    }
    signer.digest_header_for_request.assert_called_once_with("POST", path, data)


@pytest.mark.parametrize(
    "body, expected",
    [
        (None, "HTTP error"),
        (b'{"error":"unauthorized"}', 'HTTP error {"error": "unauthorized"}'),
        (b'"upstream unavailable"', 'HTTP error "upstream unavailable"'),
        (b"upstream unavailable", 'HTTP error "upstream unavailable"'),
        (b'upstream "unavailable"\n', r'HTTP error "upstream \"unavailable\"\n"'),
        (b"", 'HTTP error ""'),
        (b"\xff", r'HTTP error "\ufffd"'),
    ],
)
def test_api_error(body: bytes | None, expected: str) -> None:
    """JSON-quote error bodies, including non-JSON and invalid UTF-8 responses."""
    error = api.APIError("HTTP error", body)
    assert str(error) == expected
    assert error.args == (expected,)


def test_token_exchange(urlopen: MagicMock) -> None:
    """Exchange the authorization code and verifier using the expected JSON contract."""
    response = BytesIO(b'{"access_token": "access_token_good", "token_type": "bearer"}')
    urlopen.return_value = response
    assert api.token_exchange("code_good", "verifier_good") == "access_token_good"
    request = _request(urlopen, "POST", "https://api.amazon.com/auth/token")
    assert isinstance(request.data, bytes)
    assert json.loads(request.data) == {
        "app_name": "Unknown",
        "client_domain": "DeviceLegacy",
        "client_id": "658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d",
        "code_algorithm": "SHA-256",
        "code_verifier": "verifier_good",
        "requested_token_type": "access_token",
        "source_token": "code_good",
        "source_token_type": "authorization_code",
    }
    assert dict(request.header_items()) == {
        "Accept-language": "en-US",
        "X-amzn-identity-auth-domain": "api.amazon.com",
        "Content-type": "application/json",
        "User-agent": "Mozilla/5.0",
    }
    assert response.closed


def test_register_device_with_token(urlopen: MagicMock) -> None:
    """Register the device with XML and parse the returned credentials."""
    urlopen.return_value = BytesIO(
        b"<response><device_private_key>mock_key</device_private_key>"
        b"<adp_token>adp_token_good</adp_token><device_type>mock_device_type</device_type>"
        b"<given_name>Max</given_name><name>Max</name><account_pool>Amazon</account_pool>"
        b"<home_region>NA</home_region><user_directed_id>mock_user_id</user_directed_id>"
        b"<user_device_name>Test device</user_device_name></response>"
    )
    assert api.register_device_with_token("access_token_good") == model.DeviceInfo(
        device_private_key="mock_key",
        adp_token=ADP_TOKEN_GOOD,
        device_type="mock_device_type",
        given_name="Max",
        name="Max",
        account_pool="Amazon",
        home_region="NA",
        user_directed_id="mock_user_id",
        user_device_name="Test device",
    )
    request = _request(
        urlopen, "POST", "https://firs-ta-g7g.amazon.com/FirsProxy/registerDeviceWithToken"
    )
    assert request.data == (
        b"<?xml version='1.0' encoding='UTF-8'?>\n<request><parameters>"
        b"<deviceType>A1K6D1WRW0MALS</deviceType>"
        b"<deviceSerialNumber>ZYSQ37GQ5JQDAIKDZ3WYH6I74MJCVEGG</deviceSerialNumber>"
        b"<pid>D21NN3GG</pid><authToken>access_token_good</authToken>"
        b"<authTokenType>AccessToken</authTokenType><softwareVersion>253</softwareVersion>"
        b"<os_version>MacOSX_10.14.6_x64</os_version><device_model>Maxs MacBook Pro</device_model>"
        b"</parameters></request>"
    )
    assert dict(request.header_items()) == {
        "Content-type": "text/xml",
        "Expect": "",
        "Accept-language": "en-US,*",
        "User-agent": "Mozilla/5.0",
    }


def test_get_list_of_owned_devices(urlopen: MagicMock, signer: Mock) -> None:
    """List devices and tolerate extra service response fields."""
    urlopen.return_value = BytesIO(
        json.dumps(
            {
                "ownedDevices": [
                    {
                        "accountId": "ignored",
                        "deviceCapabilities": {"WIFI_CAPABLE": True},
                        "deviceName": "Kindle",
                        "deviceSerialNumber": "kindle-serial",
                    },
                    {
                        "deviceCapabilities": {"WIFI_CAPABLE": False},
                        "deviceName": "Phone",
                        "deviceSerialNumber": "phone-serial",
                    },
                ],
                "statusCode": 0,
            }
        ).encode()
    )
    assert api.get_list_of_owned_devices(signer) == model.GetOwnedDevicesResponse(
        [
            model.OwnedDevice({"WIFI_CAPABLE": True}, "Kindle", "kindle-serial"),
            model.OwnedDevice({"WIFI_CAPABLE": False}, "Phone", "phone-serial"),
        ],
        0,
    )
    _assert_signed_request(urlopen, signer, "/import/kindle-doc/get-device-list", {})


def test_get_upload_url(urlopen: MagicMock, signer: Mock) -> None:
    """Request a signed upload URL for the given file size."""
    urlopen.return_value = BytesIO(
        json.dumps(
            {
                "expiryTime": 3600000,
                "statusCode": 0,
                "stkToken": STK_TOKEN_GOOD,
                "uploadUrl": UPLOAD_URL,
            }
        ).encode()
    )
    assert api.get_upload_url(signer, 100) == model.GetUploadUrlResponse(
        3600000, 0, STK_TOKEN_GOOD, UPLOAD_URL
    )
    _assert_signed_request(urlopen, signer, "/import/upload-url", {"fileSize": 100})


@pytest.mark.parametrize("status", [200, 403, 500])
def test_upload_file(mocker: MockerFixture, tmp_path: Path, status: int) -> None:
    """Stream the file with its signed URL and close the connection on success or failure."""
    connection_type = mocker.patch("stkclient.api.http.client.HTTPSConnection", autospec=True)
    connection = connection_type.return_value
    response = connection.getresponse.return_value
    response.status = status
    response.reason = "Test response"
    response.read.return_value = b"upload response"
    path = tmp_path / "document.epub"
    path.write_bytes(b"test file contents")

    with path.open("rb") as stream:
        if status == 200:
            api.upload_file(UPLOAD_URL, path.stat().st_size, stream)
        else:
            with pytest.raises(api.APIError, match=f"HTTP Status Error {status}.*upload response"):
                api.upload_file(UPLOAD_URL, path.stat().st_size, stream)
        connection.request.assert_called_once_with(
            "PUT",
            UPLOAD_URL,
            body=stream,
            headers={
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,*",
                "Content-Length": str(path.stat().st_size),
                "User-Agent": "Mozilla/5.0",
            },
        )
        assert not stream.closed
    connection_type.assert_called_once_with("zme-caps.amazon.com")
    connection.close.assert_called_once_with()


def test_upload_connection_failure(mocker: MockerFixture) -> None:
    """Close an upload connection even when writing fails before a response arrives."""
    connection_type = mocker.patch("stkclient.api.http.client.HTTPSConnection", autospec=True)
    connection = connection_type.return_value
    connection.request.side_effect = OSError("connection lost")
    with pytest.raises(OSError, match="connection lost"):
        api.upload_file(UPLOAD_URL, 4, BytesIO(b"test"))
    connection.close.assert_called_once_with()
    connection.getresponse.assert_not_called()


def test_upload_invalid_url() -> None:
    """Reject an upload URL without a hostname before attempting a connection."""
    with pytest.raises(ValueError, match="Invalid URL"):
        api.upload_file("/no-host", 4, BytesIO(b"test"))


@pytest.mark.parametrize(
    "format, options, expected_force_convert",
    [
        ("mobi", {}, False),
        ("epub", {}, False),
        ("epub", {"force_convert": False}, False),
        ("epub", {"force_convert": True}, True),
        ("pdf", {}, False),
        ("pdf", {"force_convert": False}, False),
        ("pdf", {"force_convert": True}, True),
        ("PDF", {}, False),
        ("PDF", {"force_convert": True}, True),
    ],
)
def test_send_to_kindle(
    urlopen: MagicMock,
    signer: Mock,
    mocker: MockerFixture,
    format: str,
    options: Mapping[str, bool],
    expected_force_convert: bool,
) -> None:
    """Sign and submit document metadata with the requested PDF conversion policy."""
    mocker.patch("stkclient.api.time.time_ns", return_value=1_791_823_616_665_123_456)
    urlopen.return_value = BytesIO(b'{"sku": "document-sku", "statusCode": 0}')
    result = api.send_to_kindle(
        signer,
        STK_TOKEN_GOOD,
        ["A", "B"],
        author="作者",
        title="Café ☕",
        format=format,
        file_size=5688,
        **options,
    )
    assert result == model.SendToKindleResponse("document-sku", 0)
    _assert_signed_request(
        urlopen,
        signer,
        "/import/kindle-doc/send-to-kindle",
        {
            "documentMetadata": {
                "author": "作者",
                "crc32": 0,
                "inputFormat": format,
                "title": "Café ☕",
            },
            "archive": True,
            "fileSize": 5688,
            "forceConvert": expected_force_convert,
            "sendTimeMillis": 1_791_823_616_665,
            "shouldExtractWebContent": False,
            "stkToken": STK_TOKEN_GOOD,
            "targetDevices": ["A", "B"],
        },
    )


@pytest.mark.parametrize("status", [403, 500])
@pytest.mark.parametrize(
    "operation, args, kwargs",
    [
        ("token_exchange", ("code", "verifier"), {}),
        ("register_device_with_token", ("token",), {}),
        ("get_list_of_owned_devices", (), {}),
        ("get_upload_url", (100,), {}),
        (
            "send_to_kindle",
            (STK_TOKEN_GOOD, ["device"]),
            {"author": "Test", "title": "Test", "format": "pdf", "file_size": 100},
        ),
        ("logout", (), {}),
    ],
)
def test_http_error(
    urlopen: MagicMock,
    signer: Mock,
    operation: str,
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
    status: int,
) -> None:
    """Translate HTTP failures from every endpoint into APIError, preserving the cause."""
    error = urllib.error.HTTPError(
        "https://amazon.com/test",
        status,
        "upstream error",
        Message(),
        BytesIO(b'{"message": "upstream error"}'),
    )
    urlopen.side_effect = error
    if operation not in ("token_exchange", "register_device_with_token"):
        args = (signer, *args)
    with pytest.raises(api.APIError, match=f"HTTP Error {status}.*upstream error") as raised:
        getattr(api, operation)(*args, **kwargs)
    assert raised.value.__cause__ is error


def test_logout(urlopen: MagicMock, signer: Mock) -> None:
    """Sign the deauthorization request and close its response."""
    response = BytesIO(b"<response><status>SUCCESS</status></response>")
    urlopen.return_value = response
    api.logout(signer)
    path = "/FirsProxy/disownFiona?contentDeleted=false"
    request = _request(urlopen, "GET", "https://firs-ta-g7g.amazon.com" + path)
    assert request.data is None
    assert dict(request.header_items()) == {
        "Content-type": "text/xml",
        "X-adp-request-digest": "test_signature",
        "X-adp-authentication-token": ADP_TOKEN_GOOD,
        "Accept-language": "en-US,*",
        "User-agent": "Mozilla/5.0",
    }
    signer.digest_header_for_request.assert_called_once_with("GET", path, "")
    assert response.closed

"""Typed wrapper functions for the amazon auth and stk APIs."""

import http.client
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import IO, Any, List, Mapping, Optional

from stkclient.model import (
    DeviceInfo,
    GetOwnedDevicesResponse,
    GetUploadUrlResponse,
    SendToKindleResponse,
)
from stkclient.signer import Signer

DEFAULT_CLIENT_INFO = {
    "appName": "ShellExtension",
    "appVersion": "1.1.1.253",
    "os": "MacOSX_10.14.6_x64",
    "osArchitecture": "x64",
}


class APIError(ValueError):
    """Represents errors returned in HTTP response of the API."""

    def __init__(self, msg: str, body: Optional[bytes]):
        """Construct an APIError with a given message and response body."""
        if body is not None:
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = body
            msg += f" {json.dumps(body)}"
        super().__init__(msg)


def token_exchange(authorization_code: str, code_verifier: str) -> str:
    """Exchange an authorization code obtained from the final oauth redirect for an access token.

    Args:
        authorization_code: The authorization code obtained from the final oauth redirect.
        code_verifier: The code verifier that was originally generated before the auth request.

    Returns:
        The access token as a string.

    Raises:
        APIError: The HTTP request failed.
    """
    body = {
        "app_name": "Unknown",
        "client_domain": "DeviceLegacy",
        "client_id": "658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d",
        "code_algorithm": "SHA-256",
        "code_verifier": code_verifier,
        "requested_token_type": "access_token",
        "source_token": authorization_code,
        "source_token_type": "authorization_code",
    }
    req = urllib.request.Request(
        url="https://api.amazon.com/auth/token",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Accept-Language": "en-US",
            "x-amzn-identity-auth-domain": "api.amazon.com",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:  # noqa S310
            res = json.load(r)
    except urllib.error.HTTPError as e:
        raise APIError(str(e), _text(e)) from e
    access_token: str = res["access_token"]
    return access_token


def register_device_with_token(access_token: str) -> DeviceInfo:
    """Creates a long-lived device capable of interacting with the STK API from an access_token.

    Args:
        access_token: The access token obtained from token exchange

    Returns:
        DeviceInfo instance with the newly created device.

    Raises:
        APIError: The HTTP request failed.
    """
    q = {
        "device_type": "A1K6D1WRW0MALS",
        "device_serial_number": "ZYSQ37GQ5JQDAIKDZ3WYH6I74MJCVEGG",
        "pid": "D21NN3GG",
        "auth_token": access_token,
        "auth_token_type": "AccessToken",
        "software_version": "253",
        "os_version": "MacOSX_10.14.6_x64",
        "device_model": "Maxs MacBook Pro",
    }
    body = f"""<?xml version='1.0' encoding='UTF-8'?>
<request><parameters><deviceType>{q["device_type"]}</deviceType><deviceSerialNumber>{q["device_serial_number"]}</deviceSerialNumber><pid>{q["pid"]}</pid><authToken>{q["auth_token"]}</authToken><authTokenType>{q["auth_token_type"]}</authTokenType><softwareVersion>{q["software_version"]}</softwareVersion><os_version>{q["os_version"]}</os_version><device_model>{q["device_model"]}</device_model></parameters></request>"""
    req = urllib.request.Request(
        url="https://firs-ta-g7g.amazon.com/FirsProxy/registerDeviceWithToken",
        data=body.encode(),
        headers={
            "Content-Type": "text/xml",
            "Expect": "",
            "Accept-Language": "en-US,*",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:  # noqa S310
            return DeviceInfo.from_xml(r.read())
    except urllib.error.HTTPError as e:
        raise APIError(str(e), _text(e)) from e


def get_list_of_owned_devices(signer: Signer) -> GetOwnedDevicesResponse:
    """Gets a list of send-to-kindle target devices.

    Args:
        signer: Signer instance to authenticate the client.

    Returns:
        GetOwnedDevicesResponse containing owned devices.

    Raises:
        APIError: The HTTP request failed.
    """
    try:
        return GetOwnedDevicesResponse.from_dict(_request("/GetListOfOwnedDevices", signer, {}))
    except urllib.error.HTTPError as e:
        raise APIError(str(e), _text(e)) from e


def get_upload_url(signer: Signer, file_size: int) -> GetUploadUrlResponse:
    """Gets a URL where the client can send the file contents via HTTP POST request.

    Args:
        signer: Signer instance to authenticate the client.
        file_size: Size of the file to be uploaded.

    Returns:
        GetUploadUrlResponse containing the upload URL and token.

    Raises:
        APIError: The HTTP request failed.
    """
    try:
        return GetUploadUrlResponse.from_dict(
            _request("/GetUploadUrl", signer, {"fileSize": file_size})
        )
    except urllib.error.HTTPError as e:
        raise APIError(str(e), _text(e)) from e


def upload_file(url: str, file_size: int, fp: IO[Any]) -> None:
    """Perform a streaming upload of a file to the supplied URL via HTTP PUT request.

    Args:
        url: Where to upload the file
        file_size: Size of the file to be uploaded.
        fp: Readable binary file-like object to upload.

    Raises:
        ValueError: The supplied URL is invalid.
        APIError: The HTTP request failed.
    """
    u = urllib.parse.urlparse(url)
    if u.hostname is None:
        raise ValueError("Invalid URL")
    conn = http.client.HTTPSConnection(u.hostname)  # noqa: S309
    try:
        headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,*",
            "Content-Length": str(file_size),
            "User-Agent": "Mozilla/5.0",
        }
        conn.request(
            "PUT",
            url,
            body=fp,
            headers=headers,
        )
        res = conn.getresponse()
        text = res.read()
        if res.status != 200:
            msg = f"HTTP Status Error {res.status} {res.reason}"
            raise APIError(msg, text)
    finally:
        conn.close()


def send_to_kindle(
    signer: Signer,
    stk_token: str,
    target_device_serial_numbers: List[str],
    *,
    author: str,
    title: str,
    format: str,
) -> SendToKindleResponse:
    """Send an uploaded file to the specified kindle devices.

    Args:
        signer: Signer instance to authenticate the client.
        stk_token: The token associated with the upload url.
        target_device_serial_numbers: The devices to receive the file.
        author: The author of the document.
        title: The title of the document.
        format: The format of the document.

    Returns:
        SendToKindleResponse containing metadata about the sent file.

    Raises:
        APIError: The HTTP request failed.
    """
    body = {
        "DocumentMetadata": {
            "author": author,
            "crc32": 0,
            "inputFormat": format,
            "title": title,
        },
        "archive": True,
        "deliveryMechanism": "WIFI",
        "outputFormat": "MOBI",
        "stkToken": stk_token,
        "targetDevices": target_device_serial_numbers,
    }
    try:
        return SendToKindleResponse.from_dict(_request("/SendToKindle", signer, body))
    except urllib.error.HTTPError as e:
        raise APIError(str(e), _text(e)) from e


def logout(signer: Signer) -> None:
    """Logs out a send-to-kindle client.

    Args:
        signer: Signer instance to authenticate the client.

    Raises:
        APIError: The HTTP request failed.
    """
    path = "/FirsProxy/disownFiona?contentDeleted=false"
    req = urllib.request.Request(
        url="https://firs-ta-g7g.amazon.com" + path,
        headers={
            "Content-Type": "text/xml",
            "X-ADP-Request-Digest": signer.digest_header_for_request("GET", path, ""),
            "X-ADP-Authentication-Token": signer.adp_token,
            "Accept-Language": "en-US,*",
            "User-Agent": "Mozilla/5.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req) as r:  # noqa S310
            r.read()  # Read and discard
    except urllib.error.HTTPError as e:
        raise APIError(str(e), _text(e)) from e


def _request(path: str, signer: Signer, body: Mapping[str, Any]) -> Mapping[str, Any]:
    data = json.dumps(
        {
            "ClientInfo": DEFAULT_CLIENT_INFO,
            **body,
        },
        indent=4,
    )
    req = urllib.request.Request(
        url="https://stkservice.amazon.com" + path,
        data=data.encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
            "X-ADP-Request-Digest": signer.digest_header_for_request("POST", path, data),
            "X-ADP-Authentication-Token": signer.adp_token,
            "Accept-Language": "en-US,*",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:  # noqa S310
        val: Mapping[str, Any] = json.load(r)
        return val


def _text(e: urllib.error.HTTPError) -> Optional[bytes]:
    try:
        return e.read()
    except AttributeError:
        return None

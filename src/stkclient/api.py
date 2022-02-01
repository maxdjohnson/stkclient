import http.client
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, List, Mapping, Optional, Protocol

try:
    from defusedxml.ElementTree import fromstring as xml_parse
except ImportError:
    from xml.etree.ElementTree import fromstring as xml_parse


DEFAULT_CLIENT_INFO = {
    "appName": "ShellExtension",
    "appVersion": "1.1.1.253",
    "os": "MacOSX_10.14.6_x64",
    "osArchitecture": "x64",
}


class APIError(ValueError):
    def __init__(self, msg: str, text: Optional[bytes]):
        if text is not None:
            try:
                body = json.loads(text)
            except json.JSONDecodeError:
                body = text
            msg += f" {json.dumps(body)}"
        super().__init__(msg)

    @staticmethod
    def from_httperror(e: urllib.error.HTTPError) -> "APIError":
        msg = str(e)
        try:
            text = e.read()
        except AttributeError:
            text = None
        return APIError(msg, text)


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
    def from_dict(d: Mapping[str, Any]) -> "DeviceInfo":
        fieldnames = {f.name for f in fields(DeviceInfo)}
        return DeviceInfo(**{k: v for k, v in d.items() if k in fieldnames})

    @staticmethod
    def from_xml(s: bytes) -> "DeviceInfo":
        res = xml_parse(s)
        info = {}
        for el in res:
            info[el.tag] = el.text
        return DeviceInfo.from_dict(info)


@dataclass(frozen=True)
class OwnedDevice:
    device_capabilities: Mapping[str, bool]
    device_name: str
    device_serial_number: str

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "OwnedDevice":
        return OwnedDevice(
            device_capabilities=d["deviceCapabilities"],
            device_name=d["deviceName"],
            device_serial_number=d["deviceSerialNumber"],
        )


@dataclass(frozen=True)
class GetOwnedDevicesResponse:
    owned_devices: List[OwnedDevice]
    status_code: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "GetOwnedDevicesResponse":
        return GetOwnedDevicesResponse(
            owned_devices=[OwnedDevice.from_dict(v) for v in d["ownedDevices"]],
            status_code=d["statusCode"],
        )


@dataclass(frozen=True)
class GetUploadUrlResponse:
    expiry_time: int
    status_code: int
    stk_token: str
    upload_url: str

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "GetUploadUrlResponse":
        return GetUploadUrlResponse(
            expiry_time=d["expiryTime"],
            status_code=d["statusCode"],
            stk_token=d["stkToken"],
            upload_url=d["uploadUrl"],
        )


@dataclass(frozen=True)
class SendToKindleResponse:
    sku: str
    status_code: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "SendToKindleResponse":
        return SendToKindleResponse(
            sku=d["sku"],
            status_code=d["statusCode"],
        )


class _Signer(Protocol):
    adp_token: str

    def digest_header_for_request(self, method: str, path: str, data: str) -> str:
        ...


def token_exchange(authorization_code: str, code_verifier: str) -> str:
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
        raise APIError.from_httperror(e)
    return res["access_token"]


def register_device_with_token(access_token: str) -> DeviceInfo:
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
        raise APIError.from_httperror(e)


def get_owned_devices(signer: _Signer) -> GetOwnedDevicesResponse:
    res = _request("/GetListOfOwnedDevices", signer, {})
    return GetOwnedDevicesResponse.from_dict(res)


def get_upload_url(signer: _Signer, file_size: int) -> GetUploadUrlResponse:
    res = _request("/GetUploadUrl", signer, {"fileSize": file_size})
    return GetUploadUrlResponse.from_dict(res)


def upload_file(url: str, file_size: int, file_path: Path) -> None:
    u = urllib.parse.urlparse(url)
    if u.hostname is None:
        raise ValueError("Invalid URL")
    conn = http.client.HTTPSConnection(u.hostname)
    try:
        headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,*",
            "Content-Length": str(file_size),
            "User-Agent": "Mozilla/5.0",
        }
        with open(file_path, "rb") as f:
            conn.request(
                "POST",
                url,
                body=f,
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
    signer: _Signer,
    stk_token: str,
    target_device_serial_numbers: List[str],
    *,
    author: str,
    title: str,
    format: str,
):
    res = _request(
        "/SendToKindle",
        signer,
        {
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
        },
    )
    return SendToKindleResponse.from_dict(res)


def _request(path: str, signer: _Signer, body: Mapping[str, Any]) -> Mapping[str, Any]:
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
            "Content-Type": "application/json",
            "X-ADP-Request-Digest": signer.digest_header_for_request("POST", path, data),
            "X-ADP-Authentication-Token": signer.adp_token,
            "Accept-Language": "en-US,*",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:  # noqa S310
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise APIError.from_httperror(e)

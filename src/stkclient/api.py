import json
import urllib.error
import urllib.request
from dataclasses import dataclass, fields
from typing import Any, Mapping, Optional

try:
    from defusedxml.ElementTree import fromstring as xml_parse
except ImportError:
    from xml.etree.ElementTree import fromstring as xml_parse


class APIError(ValueError):
    def __init__(self, e: urllib.error.HTTPError):
        msg = str(e)
        try:
            text = e.read()
        except AttributeError:
            text = None
        if text is not None:
            try:
                body = json.loads(text)
            except json.JSONDecodeError:
                body = text
            msg += f" {json.dumps(body)}"
        super().__init__(msg)


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
        raise APIError(e)
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
        raise APIError(e)

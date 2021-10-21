from typing import Optional, Any, List, Mapping
import requests
import dataclasses
from .storage import JSONConfig
from .auth import Auth, DeviceInfo, register_device_with_token
from .signer import Signer
import json


@dataclasses.dataclass(frozen=True)
class OwnedDevice:
    device_capabilities: Mapping[str, bool]
    device_name: str
    device_serial_number: str

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> 'OwnedDevice':
        return OwnedDevice(
            device_capabilities=d["deviceCapabilities"],
            device_name=d["deviceName"],
            device_serial_number=d["deviceSerialNumber"],
        )


@dataclasses.dataclass(frozen=True)
class GetOwnedDevicesResponse:
    owned_devices: List[OwnedDevice]
    status_code: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> 'GetOwnedDevicesResponse':
        return GetOwnedDevicesResponse(
            owned_devices=[OwnedDevice.from_dict(v) for v in d["ownedDevices"]],
            status_code=d["statusCode"],
        )


@dataclasses.dataclass(frozen=True)
class GetUploadUrlResponse:
    expiry_time: int
    status_code: int
    stk_token: str
    upload_url: str

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> 'GetUploadUrlResponse':
        return GetUploadUrlResponse(
            expiry_time=d["expiryTime"],
            status_code=d["statusCode"],
            stk_token=d["stkToken"],
            upload_url=d["uploadUrl"],
        )


@dataclasses.dataclass(frozen=True)
class SendToKindleResponse:
    sku: str
    status_code: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> 'GetUploadUrlResponse':
        return GetUploadUrlResponse(
            sku=d["sku"],
            status_code=d["statusCode"],
        )


DEFAULT_CLIENT_INFO = {
    "appName": "ShellExtension",
    "appVersion": "1.1.1.253",
    "os": "MacOSX_10.14.6_x64",
    "osArchitecture": "x64"
}
class STKClient:
    signer: Signer
    info: Mapping[str, Any]

    def __init__(self, signer: Signer, info: Mapping[str, Any] = DEFAULT_CLIENT_INFO):
        self.signer = signer
        self.info = info

    def _request(self, path: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        data = json.dumps({
            "ClientInfo": self.info,
            **body,
        }, indent=4)
        r = requests.post("https://stkservice.amazon.com" + path, headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-ADP-Request-Digest': self.signer.digest_header_for_request('POST', path, data),
            'X-ADP-Authentication-Token': self.signer.adp_token,
            'Accept-Language': 'en-US,*',
            'User-Agent': 'Mozilla/5.0',
        }, data=data, verify=False)
        try:
            r.raise_for_status()
        except:
            print(r.text)
            raise
        return r.json()

    def get_list_of_owned_devices(self) -> GetOwnedDevicesResponse:
        res = self._request("/GetListOfOwnedDevices", {})
        return GetOwnedDevicesResponse.from_dict(res)

    def get_upload_url(self, file_size: int) -> GetUploadUrlResponse:
        res = self._request("/GetUploadUrl", {"fileSize": file_size})
        return GetUploadUrlResponse.from_dict(res)

    def send_to_kindle(self, stk_token: str, target_device_serial_numbers: List[str], *, author: str, title: str, format: str = "mobi") -> SendToKindleResponse:
        res = self._request("/SendToKindle", {
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
            "targetDevices": target_devices,
        })
        return SendToKindleResponse.from_dict(res)

def upload_file(url: str, path: str) -> None:
    with open(path, 'rb') as f:
        r = requests.put(url, headers={
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,*',
            'User-Agent': 'Mozilla/5.0',
        }, data=f)
    try:
        r.raise_for_status()
    except:
        print(r.text)
        raise

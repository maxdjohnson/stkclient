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


def main():
    s = JSONConfig("storage.json", "")
    if s.get("access_token") is None:
        auth = Auth()
        url = auth.get_url()
        print(url)
        redirect_url = input("Enter redirect url: ")
        s["access_token"] = auth.handle_redirect_url(redirect_url)
    print(s["access_token"])
    if s.get("device_info") is None:
        device_info = register_device_with_token(s["access_token"])
        s["device_info"] = dataclasses.asdict(device_info)
    device_info = DeviceInfo.from_dict(s["device_info"])
    print(device_info)
    s = Signer.from_device_info(device_info)
    res = get_list_of_owned_devices(s)
    print(res)


def get_list_of_owned_devices(s: Signer) -> GetOwnedDevicesResponse:
    path = "/GetListOfOwnedDevices"
    data = json.dumps({
        "ClientInfo": {
            "appName": "ShellExtension",
            "appVersion": "1.1.1.253",
            "os": "MacOSX_10.14.6_x64",
            "osArchitecture": "x64"
        }
    }, indent=4)
    r = requests.post("https://stkservice.amazon.com" + path, headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-ADP-Request-Digest': s.digest_header_for_request('POST', path, data),
        'X-ADP-Authentication-Token': s.adp_token,
        'Accept-Language': 'en-US,*',
        'User-Agent': 'Mozilla/5.0',
    }, data=data, verify=False)
    try:
        r.raise_for_status()
    except:
        print(r.text)
        raise
    return GetOwnedDevicesResponse.from_dict(r.json())

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

def get_upload_url(s: Signer, file_size: number) -> GetUploadUrlResponse:
    path = "/GetUploadUrl"
    data = json.dumps({
        "ClientInfo": {
            "appName": "ShellExtension",
            "appVersion": "1.1.1.253",
            "os": "MacOSX_10.14.6_x64",
            "osArchitecture": "x64"
        },
        "fileSize": file_size,
    }, indent=4)
    r = requests.post("https://stkservice.amazon.com" + path, headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-ADP-Request-Digest': s.digest_header_for_request('POST', path, data),
        'X-ADP-Authentication-Token': s.adp_token,
        'Accept-Language': 'en-US,*',
        'User-Agent': 'Mozilla/5.0',
    }, data=data, verify=False)
    try:
        r.raise_for_status()
    except:
        print(r.text)
        raise
    return GetUploadUrlResponse.from_dict(r.json())

def upload_file(url: string, path: string) -> None:
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

def send_to_kindle(s: Signer, stk_token: str, target_device_serial_numbers: List[str], *, author: str, title: str, format: str = "mobi") -> SendToKindleResponse:
    path = "/SendToKindle"
    data = json.dumps({
        "ClientInfo": {
            "appName": "ShellExtension",
            "appVersion": "1.1.1.253",
            "os": "MacOSX_10.14.6_x64",
            "osArchitecture": "x64"
        },
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
    }, indent=4)
    r = requests.post("https://stkservice.amazon.com" + path, headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-ADP-Request-Digest': s.digest_header_for_request('POST', path, data),
        'X-ADP-Authentication-Token': s.adp_token,
        'Accept-Language': 'en-US,*',
        'User-Agent': 'Mozilla/5.0',
    }, data=data, verify=False)
    try:
        r.raise_for_status()
    except:
        print(r.text)
        raise
    return SendToKindleResponse.from_dict(r.json())


if __name__ == "__main__":
    main()

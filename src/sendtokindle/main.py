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
class OwnedDevicesResponse:
    owned_devices: List[OwnedDevice]
    status_code: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> 'OwnedDevicesResponse':
        return OwnedDevicesResponse(
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


def get_list_of_owned_devices(s: Signer) -> OwnedDevicesResponse:
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
    return OwnedDevicesResponse.from_dict(r.json())


if __name__ == "__main__":
    main()

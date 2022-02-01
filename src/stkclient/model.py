from dataclasses import dataclass, fields
from typing import Any, List, Mapping, Optional

try:
    from defusedxml.ElementTree import fromstring as xml_parse
except ImportError:
    from xml.etree.ElementTree import fromstring as xml_parse


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

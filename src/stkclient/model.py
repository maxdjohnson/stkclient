"""Send to Kindle API response and domain objects."""

from dataclasses import dataclass, field, fields
from typing import Any, List, Mapping, Optional

try:
    from defusedxml.ElementTree import fromstring as xml_parse
except ImportError:
    from xml.etree.ElementTree import fromstring as xml_parse  # noqa: S405


@dataclass(frozen=True)
class DeviceInfo:
    """Contains authentication information for the client as well as user metadata.

    Attributes:
        device_private_key: The private key used to generate the X-ADP-Request-Digest header.
        adp_token: The value to be included in the X-ADP-Authentication-Token header.
        device_type: An opaque identifier.
        given_name: The end-user's given name.
        name: The end-user's full name.
        account_pool: "Amazon"
        user_directed_id: An opaque identifier.
        user_device_name: The end-user's name for their device.
        home_region: "NA"
    """

    device_private_key: str = field(repr=False)
    adp_token: str = field(repr=False)
    device_type: str
    given_name: str
    name: str
    account_pool: str
    user_directed_id: str
    user_device_name: str
    home_region: Optional[str] = None

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "DeviceInfo":
        """Constructs a DeviceInfo from a dictionary of attributes, ignoring unknown fields."""
        fieldnames = {f.name for f in fields(DeviceInfo)}
        return DeviceInfo(**{k: v for k, v in d.items() if k in fieldnames})

    @staticmethod
    def from_xml(xml: bytes) -> "DeviceInfo":
        """Constructs a DeviceInfo from an XML string."""
        res = xml_parse(xml)  # noqa S314
        info = {}
        for el in res:
            info[el.tag] = el.text
        return DeviceInfo.from_dict(info)


@dataclass(frozen=True)
class OwnedDevice:
    """Represents a user device supported by send-to-kindle.

    Attributes:
        device_capabilities: Mapping of capability name to boolean
        device_name: Human readable device name specified by the end user.
        device_serial_number: Unique ID of this device.
    """

    device_capabilities: Mapping[str, bool]
    device_name: str
    device_serial_number: str

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "OwnedDevice":
        """Constructs an OwnedDevice from a dictionary of attributes, ignoring unknown fields."""
        return OwnedDevice(
            device_capabilities=d["deviceCapabilities"],
            device_name=d["deviceName"],
            device_serial_number=d["deviceSerialNumber"],
        )


@dataclass(frozen=True)
class GetOwnedDevicesResponse:
    """Response from get_list_of_owned_devices.

    Attributes:
        owned_devices: List of owned devices.
        status_code: 0.
    """

    owned_devices: List[OwnedDevice]
    status_code: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "GetOwnedDevicesResponse":
        """Constructs a GetOwnedDevicesResponse from a dictionary of attributes."""
        return GetOwnedDevicesResponse(
            owned_devices=[OwnedDevice.from_dict(v) for v in d["ownedDevices"]],
            status_code=d["statusCode"],
        )


@dataclass(frozen=True)
class GetUploadUrlResponse:
    """Response from get_upload_url.

    Attributes:
        expiry_time: When this URL expires.
        status_code: 0
        stk_token: Unique identifier for this url.
        upload_url: The upload URL.
    """

    expiry_time: int
    status_code: int
    stk_token: str
    upload_url: str

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "GetUploadUrlResponse":
        """Constructs a GetUploadUrlResponse from a dictionary of attributes."""
        return GetUploadUrlResponse(
            expiry_time=d["expiryTime"],
            status_code=d["statusCode"],
            stk_token=d["stkToken"],
            upload_url=d["uploadUrl"],
        )


@dataclass(frozen=True)
class SendToKindleResponse:
    """Response from send_to_kindle.

    Attributes:
        sku: Opaque ID
        status_code: 0
    """

    sku: str
    status_code: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "SendToKindleResponse":
        """Constructs a SendToKindleResponse from a dictionary of attributes."""
        return SendToKindleResponse(
            sku=d["sku"],
            status_code=d["statusCode"],
        )

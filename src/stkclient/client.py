"""Send To Kindle Client."""

import dataclasses
from pathlib import Path
from typing import IO, List, Mapping

from stkclient import api


@dataclasses.dataclass(frozen=True)
class OwnedDevice:
    """Contains details about a kindle reader device owned by the end user."""

    device_capabilities: Mapping[str, bool]
    device_name: str
    device_serial_number: str


class Client:
    """Supports listing devices and sending files to specific devices."""

    _device_info: api.DeviceInfo

    def __init__(self, device_info: api.DeviceInfo):
        """Constructs a client instance.

        Not meant to be called directly - use stkclient.OAuth2().create_client instead."""
        self._device_info = device_info

    @staticmethod
    def load(f: IO) -> "Client":
        """Deserializes a client from a file-like object."""
        pass

    @staticmethod
    def loads(s: str) -> "Client":
        """Deserializes a client from a string."""
        pass

    @staticmethod
    def from_access_token(access_token: str) -> "Client":
        device_info = api.register_device_with_token(access_token)
        return Client(device_info)

    def dump(self, f: IO) -> None:
        """Serializes the client into a file-like object."""
        pass

    def dumps(self) -> str:
        """Serializes the client into a string."""
        pass

    def get_owned_devices(self) -> List[OwnedDevice]:
        """Returns a list of kindle devices owned by the end-user."""
        pass

    def send_file(
        self,
        filepath: Path,
        target_device_serial_numbers: List[str],
        *,
        author: str,
        title: str,
        format: str,
    ) -> None:
        """Sends a file to the specified kindle devices."""
        pass

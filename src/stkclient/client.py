"""Send To Kindle Client."""

import dataclasses
import json
from pathlib import Path
from typing import Any, BinaryIO, List, Mapping, TextIO, Union

from stkclient import api, model, signer


class Client:
    """Supports listing devices and sending files to specific devices."""

    _device_info: model.DeviceInfo

    def __init__(self, device_info: model.DeviceInfo):
        """Constructs a client instance.

        Not meant to be called directly - use stkclient.OAuth2().create_client instead.
        """
        self._device_info = device_info
        self._signer = signer.Signer.from_device_info(device_info)

    @staticmethod
    def load(fp: Union[TextIO, BinaryIO]) -> "Client":
        """Deserializes a client from a file-like object."""
        return Client._from_dict(json.load(fp))

    @staticmethod
    def loads(s: str) -> "Client":
        """Deserializes a client from a string."""
        return Client._from_dict(json.loads(s))

    @staticmethod
    def _from_dict(s: Mapping[str, Any]) -> "Client":
        if s.get("version") != 1:
            raise ValueError("Invalid version")
        return Client(model.DeviceInfo.from_dict(s.get("device_info", {})))

    @staticmethod
    def from_access_token(access_token: str) -> "Client":
        """Construct a Client object from an access token.

        Args:
            access_token: The access token obtained from token exchange

        Returns:
            Client instance.
        """
        device_info = api.register_device_with_token(access_token)
        return Client(device_info)

    def dump(self, fp: TextIO) -> None:
        """Serializes the client into a file-like object."""
        return json.dump(self._to_dict(), fp)

    def dumps(self) -> str:
        """Serializes the client into a string."""
        return json.dumps(self._to_dict())

    def _to_dict(self) -> Mapping[str, Any]:
        return {"version": 1, "device_info": dataclasses.asdict(self._device_info)}

    def get_owned_devices(self) -> List[model.OwnedDevice]:
        """Returns a list of kindle devices owned by the end-user.

        Returns:
            GetOwnedDevicesResponse containing owned devices.
        """
        return api.get_list_of_owned_devices(self._signer).owned_devices

    def send_file(
        self,
        file_path: Path,
        target_device_serial_numbers: List[str],
        *,
        author: str,
        title: str,
        format: str,
    ) -> None:
        """Sends a file to the specified kindle devices.

        Args:
            file_path: The file to send
            target_device_serial_numbers: The devices to receive the file.
            author: The author of the document.
            title: The title of the document.
            format: The format of the document.
        """
        file_size = file_path.stat().st_size
        upload = api.get_upload_url(self._signer, file_size)
        with open(file_path, "rb") as f:
            api.upload_file(upload.upload_url, file_size, f)
        api.send_to_kindle(
            self._signer,
            upload.stk_token,
            target_device_serial_numbers,
            author=author,
            title=title,
            format=format,
        )

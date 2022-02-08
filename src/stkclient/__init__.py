"""Send To Kindle."""

import base64
import dataclasses
import hashlib
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, BinaryIO, List, Mapping, TextIO, Union

from stkclient import api, model, signer

OwnedDevice = model.OwnedDevice


@dataclasses.dataclass()
class Client:
    """Supports listing devices and sending files to specific devices."""

    _device_info: model.DeviceInfo
    _signer: signer.Signer = dataclasses.field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize _signer."""
        self._signer = signer.Signer.from_device_info(self._device_info)

    def get_owned_devices(self) -> List[OwnedDevice]:
        """Returns a list of kindle devices owned by the end-user.

        Returns:
            List of OwnedDevice instances.
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
    ) -> str:
        """Sends a file to the specified kindle devices.

        Args:
            file_path: The file to send
            target_device_serial_numbers: The devices to receive the file.
            author: The author of the document.
            title: The title of the document.
            format: The format of the document.

        Returns:
            sku identifier assigned by amazon.
        """
        file_size = file_path.stat().st_size
        upload = api.get_upload_url(self._signer, file_size)
        with open(file_path, "rb") as f:
            api.upload_file(upload.upload_url, file_size, f)
        ret = api.send_to_kindle(
            self._signer,
            upload.stk_token,
            target_device_serial_numbers,
            author=author,
            title=title,
            format=format,
        )
        return ret.sku

    def logout(self) -> None:
        """Logs out the client."""
        api.logout(self._signer)

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

    def dump(self, fp: TextIO) -> None:
        """Serializes the client into a file-like object."""
        return json.dump(self._to_dict(), fp)

    def dumps(self) -> str:
        """Serializes the client into a string."""
        return json.dumps(self._to_dict())

    def _to_dict(self) -> Mapping[str, Any]:
        return {"version": 1, "device_info": dataclasses.asdict(self._device_info)}


class OAuth2:
    """Authenticates an end-user using amazon's OAuth2."""

    def __init__(self) -> None:
        """Constructs an OAuth2."""
        self._verifier = _base64_url_encode(os.urandom(32))

    def get_signin_url(self) -> str:
        """Gets the signin URL. Open in a web browser to start authentication."""
        challenge = _base64_url_encode(_sha256(self._verifier.encode("utf-8")))
        q = {
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.ns.oa2": "http://www.amazon.com/ap/ext/oauth/2",
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.oa2.client_id": "device:658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d",
            "openid.mode": "checkid_setup",
            "openid.oa2.scope": "device_auth_access",
            "openid.oa2.response_type": "code",
            "openid.oa2.code_challenge": challenge,
            "openid.oa2.code_challenge_method": "S256",
            "openid.return_to": "https://www.amazon.com/gp/sendtokindle",
            "openid.ns.pape": "http://specs.openid.net/extensions/pape/1.0",
            "openid.pape.max_auth_age": "0",
            "accountStatusPolicy": "P1",
            "openid.assoc_handle": "amzn_device_na",
            "pageId": "amzn_device_common_dark",
            "disableLoginPrepopulate": "1",
        }
        return "https://www.amazon.com/ap/signin?" + urllib.parse.urlencode(q)

    def create_client(self, redirect_url: str) -> Client:
        """Creates a client with the authorization code from the redirect URL.

        Args:
            redirect_url: The final oauth redirect URL.

        Returns:
            Client instance.
        """
        code = _parse_authorization_code(redirect_url)
        access_token = api.token_exchange(code, self._verifier)
        device_info = api.register_device_with_token(access_token)
        return Client(device_info)


def _parse_authorization_code(redirect_url: str) -> str:
    """Parse authorization_code from an OAuth2 redirect URL.

    Example:
        >>> from stkclient import _parse_authorization_code
        >>> _parse_authorization_code('https://www.amazon.com/gp/sendtokindle?openid.assoc_handle=amzn_device_na&openid.oa2.authorization_code=ANTMNkABICRQwomAuQbjuZMn&')
        'ANTMNkABICRQwomAuQbjuZMn'
    """
    u = urllib.parse.urlparse(redirect_url)
    q = urllib.parse.parse_qs(u.query)
    return q["openid.oa2.authorization_code"][0]


def _base64_url_encode(s: bytes) -> str:
    """Base64 encode.

    Example:
        >>> from stkclient import _base64_url_encode
        >>> _base64_url_encode(b'foo')
        'Zm9v'
    """
    return base64.b64encode(s, b"-_").rstrip(b"=").decode("utf8")


def _sha256(s: bytes) -> bytes:
    m = hashlib.sha256()
    m.update(s)
    return m.digest()


__all__ = ["OAuth2", "OwnedDevice", "Client"]

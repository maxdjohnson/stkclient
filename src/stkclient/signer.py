"""Implements RSA request signing for amazon APIs."""

import base64
import datetime
import hashlib
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils

from .model import DeviceInfo


@dataclass(frozen=True, repr=False)
class Signer:
    """Implements RSA request signing for amazon APIs.

    Attributes:
        device_private_key: The private key used to generate the X-ADP-Request-Digest header.
        adp_token: The value to be included in the X-ADP-Authentication-Token header.
    """

    device_private_key: rsa.RSAPrivateKey
    adp_token: str

    @staticmethod
    def from_device_info(d: DeviceInfo) -> "Signer":
        """Constructs a Signer instance from a DeviceInfo object."""
        k = serialization.load_pem_private_key(d.device_private_key.encode("utf-8"), password=None)
        if not isinstance(k, rsa.RSAPrivateKey):
            raise ValueError("Device private key must be an RSA private key")
        return Signer(
            device_private_key=k,
            adp_token=d.adp_token,
        )

    def digest_header_for_request(
        self, method: str, path: str, post_data: str, signing_date: str | None = None
    ) -> str:
        """Computes the request digest to be included in the X-ADP-Request-Digest header.

        Args:
            method: The HTTP method of the request
            path: The path portion of the URL being requested (starting with /).
            post_data: The HTTP request body if present, or an empty string
            signing_date: The date included in the signature. If null, the current date is used.

        Returns:
            The request digest to be included in the X-ADP-Request-Digest header.
        """
        if signing_date is None:
            signing_date = _get_signing_date()
        sig_data = self._make_digest_data_for_request(method, path, post_data, signing_date)
        digest = _sha256(sig_data)
        # Amazon ADP signs the raw SHA-256 digest with PKCS#1 v1.5 block padding,
        # without the ASN.1 DigestInfo wrapper. SHA256() or Prehashed(SHA256())
        # would include that wrapper and break Amazon's signature format.
        signature = self.device_private_key.sign(digest, padding.PKCS1v15(), utils.NoDigestInfo())
        bytes64 = base64.b64encode(signature).decode("utf-8")
        return f"{bytes64}:{signing_date}"

    def _make_digest_data_for_request(
        self, method: str, path: str, post_data: str, signing_date: str | None = None
    ) -> bytes:
        if signing_date is None:
            signing_date = _get_signing_date()
        sig_data = "\n".join([method, path, signing_date, post_data, self.adp_token])
        return sig_data.encode("utf-8")


# 2021-10-09T05:02:38Z
def _get_signing_date() -> str:
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256(s: bytes) -> bytes:
    m = hashlib.sha256()
    m.update(s)
    return m.digest()

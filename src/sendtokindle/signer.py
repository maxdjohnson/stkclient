import datetime
import hashlib
import rsa
import base64
from typing import Optional, Mapping, Any, cast
from dataclasses import dataclass
from .auth import DeviceInfo


@dataclass(frozen=True)
class Signer:
    device_private_key: rsa.PrivateKey
    adp_token: str

    @staticmethod
    def from_device_info(d: DeviceInfo) -> 'Signer':
        return Signer(
            device_private_key=rsa.PrivateKey.load_pkcs1(d.device_private_key.encode('utf-8')),
            adp_token=d.adp_token,
        )

    def digest_header_for_request(self, method: str, url: str, post_data: str, signing_date: Optional[str] = None) -> str:
        if signing_date is None:
            signing_date = get_signing_date()
        sig_data = self.make_digest_data_for_request(
            method,
            url,
            post_data,
            signing_date
        )
        digest = sha256(sig_data)
        encrypted_bytes = rsa.encrypt(digest, cast(rsa.PublicKey, self.device_private_key))
        bytes64 = base64.b64encode(encrypted_bytes).decode('utf-8')
        return f"{bytes64}:{signing_date}"

    def make_digest_data_for_request(self, method: str, url: str, post_data: str, signing_date: Optional[str] = None) -> bytes:
        if signing_date is None:
            signing_date = get_signing_date()
        sig_data = "\n".join([method, url, signing_date, post_data, self.adp_token])
        return sig_data.encode("utf-8")


# 2021-10-09T05:02:38Z
def get_signing_date():
    return datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


def sha256(s: bytes) -> bytes:
    m = hashlib.sha256()
    m.update(s)
    return m.digest()

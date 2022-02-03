"""Unit tests of stkclient.signer."""

from stkclient.model import DeviceInfo
from stkclient.signer import Signer

EXPECTED_SIG = "czUzgbTkzXs2/esqFMcbGuIAdVkRPBzYJFsOnHNep0sW/xyW5hCtOgphRAqZGnUP4jXVvHTf+dRsRg5wdSzcp8CG5POxXZ6Qi+0KeKWiraMNmdRP7+L1RLXJ5cgd/HLbrBqGYAK5+VEpNDRitNXBm4KJOysPWyvf5mU6tu0KoHCfEm0biNNjTEn54J+FaQlB0xYIb8WHct/vqTQGmKoKhZGsPe1L5HwzTZfg5Wdld9SjujgaW8uQmWJ7QpDJ0dw5Fv1W0x6fK+pM/rM/rPQ5XrbPYIeXSSPL6KKoqeIPpbwNrVHdgpeZAU/1BMIF7+zXQKv4L8IjFizgf+L2tqa6Yg==:2020-04-10T14:21:40Z"


def test_signer(device_info: DeviceInfo) -> None:
    """Check that signer returns the expected digest value with a known key."""
    date = "2020-04-10T14:21:40Z"
    request_path = "/FirsProxy/getStoreCredentials"
    signer = Signer.from_device_info(device_info)
    sig = signer.digest_header_for_request("GET", request_path, "", date)
    assert sig == EXPECTED_SIG

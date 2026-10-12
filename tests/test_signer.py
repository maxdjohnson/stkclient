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


def test_signer_post_data(device_info: DeviceInfo) -> None:
    """Preserve the legacy signature for a non-empty UTF-8 request body."""
    signer = Signer.from_device_info(device_info)
    # Captured from the python-rsa implementation before migration.
    expected = "NqES9jLMrb6/yi6zeeQVTZHHbPDbbnTJzA2vXL6xDThpF/qUXlxzCbHfGLJntF+PEW5hkfl3YlvqgOYeYQF4ZxgCOU5NAOOkdAYngSycF5/DGLCdR3kRzG81qIvOjzYHX2pEyXxcBEkloegiTHkOyHQ1XKqcySYhYH+KCey6Nimn3e7zFSRvayw8gupg2VDQkxMBdVSCKpBwH7PRWzMBbBqpWdRD6hO+75kCo+ghtdZsr0Ci71GUxYmFSH8GexykvYQKIAL0LCspAx/g+8Svp/m6v8MdrZv9FRlzeKfH1SSJlfJgqn8J1Dt3O+AoEnzkCs8xWKHPXPkPM/JMejhOvg==:2020-04-10T14:21:40Z"
    sig = signer.digest_header_for_request(
        "POST", "/SendToKindle", '{"title": "Café ☕", "author": "作者"}\n', "2020-04-10T14:21:40Z"
    )
    assert sig == expected

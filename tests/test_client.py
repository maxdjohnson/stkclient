"""Tests for the stkclient module."""
from pathlib import Path
from typing import IO, Any

from pytest_mock import MockerFixture

from stkclient import Client, OAuth2, model


def test_oauth2(mocker: MockerFixture, device_info: model.DeviceInfo) -> None:
    """Test the OAuth2 class."""
    # Test get_signin_url
    randbytes = bytes.fromhex("1f39b9ec92e8b3252dd5f710ecbb13d4d64f157ac3247201360a046415bbbbdd")
    urandom = mocker.patch("os.urandom", return_value=randbytes)
    auth = OAuth2()
    signin_url = auth.get_signin_url()
    assert "openid.oa2.code_challenge=THxYauRERZoUf-pEd8iLGDkqHKdGCk-VQqWafikyBSM" in signin_url
    urandom.assert_called_once_with(32)

    # Test creating a client from a redirect url
    token_exchange = mocker.patch("stkclient.api.token_exchange", return_value="access_token_good")
    register_device = mocker.patch(
        "stkclient.api.register_device_with_token", return_value=device_info
    )
    redirect_url = "https://www.amazon.com/gp/sendtokindle?openid.assoc_handle=amzn_device_na&openid.oa2.authorization_code=authorization_code_good&"
    client = auth.create_client(redirect_url)
    assert client._device_info == device_info
    token_exchange.assert_called_once_with(
        "authorization_code_good", "Hzm57JLosyUt1fcQ7LsT1NZPFXrDJHIBNgoEZBW7u90"
    )
    register_device.assert_called_once_with("access_token_good")


def test_client_get_owned_devices(mocker: MockerFixture, device_info: model.DeviceInfo) -> None:
    """Test client.get_owned_devices."""
    devices = [
        model.OwnedDevice(
            device_capabilities={
                "PDF_CONTENT_ENABLED": True,
                "WAN_ENABLED": False,
                "WIFI_CAPABLE": True,
            },
            device_name="Max's 5th iPhone",
            device_serial_number="35C6D8B149E345848BF462CC13824AA2",
        ),
        model.OwnedDevice(
            device_capabilities={
                "PDF_CONTENT_ENABLED": True,
                "WAN_ENABLED": False,
                "WIFI_CAPABLE": True,
            },
            device_name="Max's Kindle",
            device_serial_number="G000PP1311850V4X",
        ),
    ]
    get_list_of_owned_devices = mocker.patch(
        "stkclient.api.get_list_of_owned_devices",
        return_value=model.GetOwnedDevicesResponse(devices, 0),
    )
    c = Client(device_info)
    assert c.get_owned_devices() == devices
    get_list_of_owned_devices.assert_called_once_with(c._signer)


def test_client_send_file(
    mocker: MockerFixture, tmp_path: Path, device_info: model.DeviceInfo
) -> None:
    """Test client.send_file."""
    test_upload_url = "test_upload_url"
    test_device_id = "test_device_id"
    test_file_contents = "test_file_contents"
    test_stk_token = "test_stk_token"  # noqa S105
    test_file_path = tmp_path / "test_file.txt"
    test_sku = "test_sku"
    test_author = "test_author"
    test_title = "test_title"
    with open(test_file_path, "w") as f:
        f.write(test_file_contents)

    # Mock api.get_upload_url
    get_upload_url = mocker.patch(
        "stkclient.api.get_upload_url",
        return_value=model.GetUploadUrlResponse(0, 0, test_stk_token, test_upload_url),
    )

    # Mock api.upload_file. Use a custom implementation so we can read out the file.
    def handle_upload(url: str, file_size: int, fp: IO[Any]) -> None:
        d = fp.read()
        assert len(d) == file_size
        assert d == test_file_contents.encode()
        assert url == test_upload_url

    upload_file = mocker.patch("stkclient.api.upload_file", side_effect=handle_upload)

    # Mock api.send_to_kindle
    send_to_kindle = mocker.patch(
        "stkclient.api.send_to_kindle", return_value=model.SendToKindleResponse(test_sku, 0)
    )

    # Call send_file and check calls to mocks
    c = Client(device_info)
    sku = c.send_file(
        test_file_path, [test_device_id], author=test_author, title=test_title, format="mobi"
    )
    assert sku == test_sku
    get_upload_url.assert_called_once_with(c._signer, len(test_file_contents))
    upload_file.assert_called_once()  # assertions done in the implementation
    send_to_kindle.assert_called_once_with(
        c._signer,
        test_stk_token,
        [test_device_id],
        author=test_author,
        title=test_title,
        format="mobi",
    )


def test_client_serde_str(device_info: model.DeviceInfo) -> None:
    """Test client string serialization / deserialization."""
    c1 = Client(device_info)
    s = c1.dumps()
    c2 = Client.loads(s)
    assert c1 == c2


def test_client_serde_file(tmp_path: Path, device_info: model.DeviceInfo) -> None:
    """Test client file serialization / deserialization."""
    f = tmp_path / "client.json"
    c1 = Client(device_info)
    with open(f, "w") as fw:
        c1.dump(fw)
    with open(f) as fr:
        c2 = Client.load(fr)
    assert c1 == c2


def test_client_repr(device_info: model.DeviceInfo) -> None:
    """Test that the repr of client objects doesn't include credentials."""
    c = Client(device_info)
    s = repr(c)
    assert "RSA PRIVATE KEY" not in s
    assert device_info.adp_token not in s
    assert "adp_token" not in s
    assert "adp_token" not in s

"""Tests for the command-line interface."""

from dataclasses import replace
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

import stkclient
from stkclient.__main__ import main
from stkclient.model import DeviceInfo


def test_login(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture, device_info: DeviceInfo
) -> None:
    """Save credentials at the default location and replace them only with explicit consent."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    client_path = tmp_path / "pystkclient" / "client.json"
    mock_client = stkclient.Client(device_info)
    mocker.patch("builtins.input", return_value="test_input")
    authenticate = mocker.patch.object(stkclient.OAuth2, "create_client", return_value=mock_client)

    # First call results in a client file
    main(["login"])
    with open(client_path) as f:
        assert stkclient.Client.load(f) == mock_client

    replacement = stkclient.Client(
        replace(device_info, adp_token=f"{device_info.adp_token}-replacement")
    )
    authenticate.return_value = replacement
    original = client_path.read_bytes()
    # Refuse a second login before authenticating or overwriting saved credentials.
    with pytest.raises(SystemExit):
        main(["login"])
    assert client_path.read_bytes() == original
    authenticate.assert_called_once()

    # Unless passing -f
    main(["login", "-f"])
    with client_path.open() as f:
        assert stkclient.Client.load(f) == replacement


@pytest.fixture()
def client_path(tmp_path: Path, device_info: DeviceInfo) -> Path:
    """Persist a real client so commands exercise loading as well as argument parsing."""
    path = tmp_path / "client.json"
    path.write_text(stkclient.Client(device_info).dumps(), encoding="utf-8")
    return path


@pytest.fixture()
def owned_devices() -> list[stkclient.OwnedDevice]:
    """Provide two destinations for listing and sending."""
    return [
        stkclient.OwnedDevice({}, "Kindle", "kindle-serial"),
        stkclient.OwnedDevice({}, "Phone", "phone-serial"),
    ]


@pytest.mark.parametrize(
    "targets, force_convert",
    [(["kindle-serial", "phone-serial"], False), (["all"], True)],
)
def test_send(
    client_path: Path,
    owned_devices: list[stkclient.OwnedDevice],
    tmp_path: Path,
    mocker: MockerFixture,
    targets: list[str],
    force_convert: bool,
) -> None:
    """Send to explicit targets or all devices with the requested conversion options."""
    get_devices = mocker.patch.object(
        stkclient.Client, "get_owned_devices", return_value=owned_devices
    )
    send_file = mocker.patch.object(stkclient.Client, "send_file", return_value="document-sku")
    document = tmp_path / "document.pdf"
    document.write_bytes(b"test document")
    args = [
        "send",
        "--client",
        str(client_path),
        "--author",
        "Author",
        "--title",
        "Title",
        "--format",
        "pdf",
    ]
    if force_convert:
        args.append("--force-convert")
    main([*args, str(document), *targets])
    if targets == ["all"]:
        get_devices.assert_called_once_with()
        targets = [device.device_serial_number for device in owned_devices]
    else:
        get_devices.assert_not_called()
    send_file.assert_called_once_with(
        document,
        targets,
        author="Author",
        title="Title",
        format="pdf",
        force_convert=force_convert,
    )


def test_logout(client_path: Path, mocker: MockerFixture) -> None:
    """Deauthorize the loaded client before deleting the credential file."""

    def deauthorize() -> None:
        assert client_path.exists()

    logout = mocker.patch.object(stkclient.Client, "logout", side_effect=deauthorize)
    main(["logout", "--client", str(client_path)])
    logout.assert_called_once_with()
    assert not client_path.exists()


def test_logout_failure(client_path: Path, mocker: MockerFixture) -> None:
    """Keep credentials available for retry if remote deauthorization fails."""
    original = client_path.read_bytes()
    mocker.patch.object(
        stkclient.Client, "logout", side_effect=stkclient.api.APIError("unavailable")
    )
    with pytest.raises(stkclient.api.APIError, match="unavailable"):
        main(["logout", "--client", str(client_path)])
    assert client_path.read_bytes() == original


def test_login_failure(client_path: Path, mocker: MockerFixture) -> None:
    """A failed forced login must leave existing credentials intact."""
    original = client_path.read_bytes()
    mocker.patch("builtins.input", return_value="redirect-url")
    mocker.patch.object(
        stkclient.OAuth2, "create_client", side_effect=stkclient.api.APIError("unauthorized")
    )
    with pytest.raises(stkclient.api.APIError, match="unauthorized"):
        main(["login", "--force", "--client", str(client_path)])
    assert client_path.read_bytes() == original

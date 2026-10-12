"""Tests for the command-line interface."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

import stkclient
from stkclient.__main__ import main
from stkclient.model import DeviceInfo


def test_login(tmp_path: Path, mocker: MockerFixture, device_info: DeviceInfo) -> None:
    """Test the login command."""
    client_path = tmp_path / "client.json"
    mock_client = stkclient.Client(device_info)
    mocker.patch("builtins.input", return_value="test_input")
    mocker.patch.object(stkclient.OAuth2, "create_client", return_value=mock_client)

    # First call results in a client file
    main(["login", "--client", str(client_path)])
    assert client_path.exists()
    with open(client_path) as f:
        assert stkclient.Client.load(f) == mock_client

    # Calling again raises an error as the file exists
    with pytest.raises(SystemExit):
        main(["login", "--client", str(client_path)])

    # Unless passing -f
    main(["login", "--client", str(client_path), "-f"])


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


def test_devices(
    client_path: Path,
    owned_devices: list[stkclient.OwnedDevice],
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Print each device's serial number and display name."""
    get_devices = mocker.patch.object(
        stkclient.Client, "get_owned_devices", return_value=owned_devices
    )
    main(["devices", "--client", str(client_path)])
    get_devices.assert_called_once_with()
    assert capsys.readouterr().out == "kindle-serial: Kindle\nphone-serial: Phone\n"


@pytest.mark.parametrize("targets", [["kindle-serial"], ["kindle-serial", "phone-serial"], ["all"]])
@pytest.mark.parametrize("force_convert", [False, True])
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


@pytest.mark.parametrize(
    "args",
    [
        ["devices"],
        ["logout"],
        ["send", "--title", "Title", "--author", "Author", "--format", "pdf", "file.pdf", "all"],
    ],
)
def test_missing_client(
    args: list[str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report missing credentials consistently for commands that need a client."""
    path = tmp_path / "missing.json"
    with pytest.raises(SystemExit) as raised:
        main([*args, "--client", str(path)])
    assert raised.value.code == 1
    assert capsys.readouterr().err == f"{path} does not exist\n"


def test_login_default_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    device_info: DeviceInfo,
) -> None:
    """Create the default credential directory under XDG_DATA_HOME."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    mocker.patch("builtins.input", return_value="redirect-url")
    mocker.patch.object(
        stkclient.OAuth2, "create_client", return_value=stkclient.Client(device_info)
    )
    main(["login"])
    saved = tmp_path / "pystkclient" / "client.json"
    assert stkclient.Client.loads(saved.read_text()) == stkclient.Client(device_info)


def test_login_missing_parent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Explain a nonexistent custom credential directory before asking for authentication."""
    path = tmp_path / "missing" / "client.json"
    with pytest.raises(SystemExit) as raised:
        main(["login", "--client", str(path)])
    assert raised.value.code == 1
    assert capsys.readouterr().err == f"{path.parent} is not a directory\n"
    assert not path.exists()


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


def test_no_command(capsys: pytest.CaptureFixture[str]) -> None:
    """Display usage and fail when invoked without a subcommand."""
    with pytest.raises(SystemExit) as raised:
        main([])
    assert raised.value.code == 1
    assert "usage: stkclient" in capsys.readouterr().out

"""Test cases for the __main__ module."""
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

"""Command-line interface."""
import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import stkclient

# Try to import the readline module for improved input() behavior. Without this, pasting a line
# longer than 1024 chars causes the process to hang on my machine.
try:
    import readline  # noqa
except ModuleNotFoundError:
    pass  # not available on windows

DEFAULT_CLIENT_PATH = os.path.join("$XDG_DATA_HOME", "pystkclient", "client.json")


def arg_parser() -> argparse.ArgumentParser:
    """Constructs an ArgumentParser for the stkclient script."""
    # create the top-level parser
    parser = argparse.ArgumentParser(
        prog="stkclient", description="Command-line interface for Amazon's Send-to-Kindle service"
    )
    subparsers = parser.add_subparsers()

    # create the parser for the "login" command
    parser_login = subparsers.add_parser("login", help=login.__doc__)
    parser_login.add_argument(
        "--client",
        type=str,
        default=DEFAULT_CLIENT_PATH,
        help="path to write the client details",
    )
    parser_login.add_argument(
        "-f", "--force", action="store_true", help="overwrite the existing client, if there is one"
    )
    parser_login.set_defaults(func=login)

    # create the parser for the "devices" command
    parser_devices = subparsers.add_parser("devices", help=devices.__doc__)
    parser_devices.add_argument(
        "--client",
        type=str,
        default=DEFAULT_CLIENT_PATH,
        help="path to the client details",
    )
    parser_devices.set_defaults(func=devices)

    # create the parser for the "send" command
    parser_send = subparsers.add_parser("send", help=send.__doc__)
    parser_send.add_argument(
        "--client",
        type=str,
        default=DEFAULT_CLIENT_PATH,
        help="path to the client details",
    )
    parser_send.add_argument(
        "--title", type=str, required=True, help="title of the work (required)"
    )
    parser_send.add_argument(
        "--author", type=str, required=True, help="author of the work (required)"
    )
    parser_send.add_argument(
        "--format", type=str, required=True, help='file format, for example "mobi" (required)'
    )
    parser_send.add_argument("file", type=Path, help="file to send")
    parser_send.add_argument(
        "target",
        type=str,
        nargs="+",
        help='device serial numbers to send the file to, or "all" to send to all devices',
    )
    parser_send.set_defaults(func=send)

    # create the parser for the "logout" command
    parser_logout = subparsers.add_parser("logout", help=logout.__doc__)
    parser_logout.add_argument(
        "--client",
        type=str,
        default=DEFAULT_CLIENT_PATH,
        help="path to the client details - will be deleted",
    )
    parser_logout.set_defaults(func=logout)

    # TODO verbosity
    return parser


def main(args: Optional[List[str]] = None) -> None:
    """Send To Kindle."""
    parser = arg_parser()
    parsed = parser.parse_args(args)
    if not hasattr(parsed, "func"):
        parser.print_usage()
        exit(1)
    parsed.func(parsed)


def login(args: argparse.Namespace) -> None:
    """Create a client by authenticating with OAuth2."""
    client_path = _get_client_path(args)
    if client_path.exists() and not args.force:
        print(f"{client_path} already exists", file=sys.stderr)
        exit(1)
    if args.client == DEFAULT_CLIENT_PATH:
        client_path.parent.mkdir(parents=True, exist_ok=True)
    elif not client_path.parent.is_dir():
        print(f"{client_path.parent} is not a directory", file=sys.stderr)
        exit(1)
    auth = stkclient.OAuth2()
    signin_url = auth.get_signin_url()
    print(signin_url)
    redirect_url = input("Enter redirect url: ")
    client = auth.create_client(redirect_url)
    with open(client_path, "w") as f:
        client.dump(f)


def devices(args: argparse.Namespace) -> None:
    """List available kindle reader devices."""
    client_path = _get_client_path(args)
    if not client_path.exists():
        print(f"{client_path} does not exist", file=sys.stderr)
        exit(1)
    with open(client_path) as f:
        client = stkclient.Client.load(f)
    devices = client.get_owned_devices()
    for device in devices:
        print(f"{device.device_serial_number}: {device.device_name}")


def send(args: argparse.Namespace) -> None:
    """Send a file to one or more devices."""
    client_path = _get_client_path(args)
    if not client_path.exists():
        print(f"{client_path} does not exist", file=sys.stderr)
        exit(1)
    with open(client_path) as f:
        client = stkclient.Client.load(f)
    target: List[str] = args.target
    if any(t == "all" for t in args.target):
        target = [d.device_serial_number for d in client.get_owned_devices()]
    client.send_file(args.file, target, author=args.author, title=args.title, format=args.format)


def logout(args: argparse.Namespace) -> None:
    """Deauthorize and delete a client."""
    client_path = _get_client_path(args)
    if not client_path.exists():
        print(f"{client_path} does not exist", file=sys.stderr)
        exit(1)
    with open(client_path) as f:
        c = stkclient.Client.load(f)
    c.logout()
    client_path.unlink()


def _get_client_path(args: argparse.Namespace) -> Path:
    client_path: str = args.client
    data_home = os.environ.get("XDG_DATA_HOME", os.path.join("~", ".local", "share"))
    return Path(client_path.replace("$XDG_DATA_HOME", data_home)).expanduser()


if __name__ == "__main__":
    main()  # pragma: no cover

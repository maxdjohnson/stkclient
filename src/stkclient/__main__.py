"""Command-line interface."""
import argparse
import os
import sys
from pathlib import Path
from typing import List

import stkclient


def main() -> None:
    """Send To Kindle."""
    # create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # create the parser for the "auth" command
    parser_auth = subparsers.add_parser("auth", help=auth.__doc__)
    parser_auth.add_argument(
        "--client",
        type=Path,
        default=_default_client_path(),
        help="path to write the client details",
    )
    parser_auth.add_argument(
        "-f", "--force", action="store_true", help="overwrite the existing client, if there is one"
    )
    parser_auth.set_defaults(func=auth)

    # create the parser for the "devices" command
    parser_devices = subparsers.add_parser("devices", help=devices.__doc__)
    parser_devices.add_argument(
        "--client",
        type=Path,
        default=_default_client_path(),
        help="path to load the client details (defaults to $XDG_DATA_HOME/pystkclient/client.json)",
    )
    parser_devices.set_defaults(func=devices)

    # create the parser for the "send" command
    parser_send = subparsers.add_parser("send", help=send.__doc__)
    parser_send.add_argument(
        "--client",
        type=Path,
        default=_default_client_path(),
        help="path to load the client details (defaults to $XDG_DATA_HOME/pystkclient/client.json)",
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

    # parse the args and call whatever function was selected
    args = parser.parse_args()
    args.func(args)


def auth(args: argparse.Namespace) -> None:
    """Create a client by authenticating with OAuth2."""
    outpath: Path = args.client
    if outpath.exists() and not args.force:
        print(f"{outpath} already exists", file=sys.stderr)
        exit(1)
    if outpath == _default_client_path():
        outpath.parent.mkdir(parents=True, exist_ok=True)
    elif not outpath.parent.is_dir():
        print(f"{outpath.parent} is not a directory", file=sys.stderr)
        exit(1)
    # TODO
    auth = stkclient.OAuth2()
    signin_url = auth.get_signin_url()
    print(signin_url)
    redirect_url = input("Enter redirect url: ")
    client = auth.create_client(redirect_url)
    with open(outpath, "w") as f:
        client.dump(f)


def devices(args: argparse.Namespace) -> None:
    """List available kindle reader devices."""
    clientpath: Path = args.client
    if not clientpath.exists():
        print(f"{clientpath} does not exist", file=sys.stderr)
        exit(1)
    with open(clientpath) as f:
        client = stkclient.Client.load(f)
    devices = client.get_owned_devices()
    for device in devices:
        print(device)


def send(args: argparse.Namespace) -> None:
    """Send a file to one or more devices."""
    clientpath: Path = args.client
    if not clientpath.exists():
        print(f"{clientpath} does not exist", file=sys.stderr)
        exit(1)
    with open(clientpath) as f:
        client = stkclient.Client.load(f)
    target: List[str] = args.target
    for dst in target:
        if dst == "all":
            target = [d.device_serial_number for d in client.get_owned_devices()]
            break
    client.send_file(args.file, target, author=args.author, title=args.title, format=args.format)


def _default_client_path() -> Path:
    return _data_home() / "pystkclient" / "client.json"


def _data_home() -> Path:
    value = os.environ.get("XDG_DATA_HOME")
    if value and os.path.isabs(value):
        return Path(value)
    return Path.home() / ".local" / "share"


if __name__ == "__main__":
    main()  # pragma: no cover
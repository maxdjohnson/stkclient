"""Send To Kindle Client."""

import dataclasses
from pathlib import Path
from typing import IO, List, Mapping

import lxml.etree  # noqa: S410


@dataclasses.dataclass(frozen=True)
class OwnedDevice:
    """Contains details about a kindle reader device owned by the end user."""

    device_capabilities: Mapping[str, bool]
    device_name: str
    device_serial_number: str


class Client:
    """Supports listing devices and sending files to specific devices."""

    @staticmethod
    def load(f: IO) -> "Client":
        """Deserializes a client from a file-like object."""
        pass

    @staticmethod
    def loads(s: str) -> "Client":
        """Deserializes a client from a string."""
        pass

    def dump(self, f: IO) -> None:
        """Serializes the client into a file-like object."""
        pass

    def dumps(self) -> str:
        """Serializes the client into a string."""
        pass

    def get_owned_devices(self) -> List[OwnedDevice]:
        """Returns a list of kindle devices owned by the end-user."""
        pass

    def send_file(
        self,
        filepath: Path,
        target_device_serial_numbers: List[str],
        *,
        author: str,
        title: str,
        format: str,
    ) -> None:
        """Sends a file to the specified kindle devices."""
        pass


class Resolver(lxml.etree.Resolver):
    """Resolving of SYSTEM entities is turned off as entities can cause reads of local files.

    For example: <!DOCTYPE foo [ <!ENTITY passwd SYSTEM "file:///etc/passwd" >]>"""

    def resolve(self, url: str, id: str, context: Any) -> Any:
        return self.resolve_string("", context)


def create_parser(recover: bool, encoding: Optional[str] = None) -> lxml.etree.XMLParser:
    """Creates a parser with custom resolver."""
    parser = lxml.etree.XMLParser(recover=recover, no_network=True, encoding=encoding)
    parser.resolvers.add(Resolver())
    return parser


def safe_xml_fromstring(b: bytes, recover=True) -> lxml.etree.Element:
    """Parses untrusted XML."""
    return lxml.etree.fromstring(b, parser=create_parser(recover))

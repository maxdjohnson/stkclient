from typing import Any, Optional
import lxml.etree

# resolving of SYSTEM entities is turned off as entities can cause
# reads of local files, for example:
# <!DOCTYPE foo [ <!ENTITY passwd SYSTEM "file:///etc/passwd" >]>


class Resolver(lxml.etree.Resolver):
    def resolve(self, url: str, id: str, context: Any) -> Any:
        return self.resolve_string('', context)


def create_parser(recover: bool, encoding: Optional[str] = None) -> lxml.etree.XMLParser:
    parser = lxml.etree.XMLParser(recover=recover, no_network=True, encoding=encoding)
    parser.resolvers.add(Resolver())
    return parser


def safe_xml_fromstring(b: bytes, recover=True) -> lxml.etree.Element:
    return lxml.etree.fromstring(b, parser=create_parser(recover))

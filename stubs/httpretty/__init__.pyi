from typing import Any, Callable, Mapping, Tuple, Union

from .core import HTTPrettyRequest

POST = 'POST'
GET = 'GET'
CONNECT = 'CONNECT'
DELETE = 'DELETE'
HEAD = 'HEAD'
OPTIONS = 'OPTIONS'
PATCH = 'PATCH'
PUT = 'PUT'

Callback = Callable[[HTTPrettyRequest, str, Mapping[str, Any]], Tuple[int, Mapping[str, Any], str]]


def enable(verbose: bool = False, allow_net_connect: bool = True) -> None: ...
def disable() -> None: ...
def reset() -> None: ...
def register_uri(method: str, url: str, body: Union[str, Callback]) -> None: ...
def last_request() -> HTTPrettyRequest: ...

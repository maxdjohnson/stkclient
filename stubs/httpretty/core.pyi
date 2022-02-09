from http.server import BaseHTTPRequestHandler
from typing import Any


class HTTPrettyRequest(BaseHTTPRequestHandler):
    created_at: Any
    raw_headers: Any
    connection: Any
    rfile: Any
    wfile: Any
    raw_requestline: Any
    error_code: Any
    error_message: Any
    path: Any
    querystring: Any
    parsed_body: Any
    def __init__(self, headers: str, body: str = ..., sock: Any | None = ..., path_encoding: str = ...): ...
    @property
    def method(self) -> str: ...
    @property
    def protocol(self) -> str: ...
    @property
    def body(self) -> bytes: ...
    @body.setter
    def body(self, value: str) -> None: ...
    @property
    def url(self) -> str: ...
    @property
    def host(self) -> str: ...

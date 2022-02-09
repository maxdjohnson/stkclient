from typing import Any

class HTTPrettyError(Exception): ...

class UnmockedError(HTTPrettyError):
    request: Any
    def __init__(self, message: str = ..., request: Any | None = ..., address: Any | None = ...) -> None: ...

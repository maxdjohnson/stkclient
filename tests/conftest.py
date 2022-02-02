"""Shared fixtures."""

from typing import Generator

import httpretty
import pytest


@pytest.fixture(autouse=True)
def disable_network_calls() -> Generator[None, None, None]:
    """Mocks network using httpretty."""
    httpretty.enable(verbose=True, allow_net_connect=False)
    yield
    httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
    httpretty.reset()  # reset HTTPretty state (clean up registered urls and request history)

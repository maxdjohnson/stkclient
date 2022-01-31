import httpretty
import pytest
import requests


@pytest.fixture(autouse=True)
def disable_network_calls():
    httpretty.enable(verbose=True, allow_net_connect=False)
    yield
    httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
    httpretty.reset()  # reset HTTPretty state (clean up registered urls and request history)

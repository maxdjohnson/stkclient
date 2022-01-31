import json
import urllib.error
import urllib.request


class APIError(ValueError):
    pass


def token_exchange(authorization_code: str, code_verifier: str) -> str:
    body = {
        "app_name": "Unknown",
        "client_domain": "DeviceLegacy",
        "client_id": "658490dfb190e494030082836775981fa23be0c2425441860352ba0f55915b43002d",
        "code_algorithm": "SHA-256",
        "code_verifier": code_verifier,
        "requested_token_type": "access_token",
        "source_token": authorization_code,
        "source_token_type": "authorization_code",
    }
    req = urllib.request.Request(
        url="https://api.amazon.com/auth/token",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Accept-Language": "en-US",
            "x-amzn-identity-auth-domain": "api.amazon.com",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:  # noqa S310
            res = json.load(r)
    except urllib.error.HTTPError as e:
        msg = str(e)
        try:
            text = e.read()
        except AttributeError:
            text = None
        if text is not None:
            try:
                body = json.loads(text)
            except json.JSONDecodeError:
                body = text
            msg += f" {json.dumps(body)}"
        raise APIError(msg)
    return res["access_token"]

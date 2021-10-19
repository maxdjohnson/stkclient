import dataclasses
from .storage import JSONConfig
from .auth import Auth, DeviceInfo, register_device_with_token


def main():
    s = JSONConfig("storage.json", ".")
    if s.get("access_token") is None:
        auth = Auth()
        url = auth.get_url()
        print(url)
        redirect_url = input("Enter redirect url: ")
        s["access_token"] = auth.handle_redirect_url(redirect_url)
    print(s["access_token"])
    if s.get("device_info") is None:
        device_info = register_device_with_token(s["access_token"])
        s["device_info"] = dataclasses.asdict(device_info)
    device_info = DeviceInfo.from_dict(s["device_info"])
    print(device_info)


if __name__ == "__main__":
    main()
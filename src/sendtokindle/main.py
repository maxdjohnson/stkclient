from typing import Optional, Any, List, Mapping
import sys
import os.path
import requests
import dataclasses
from .storage import JSONConfig
from .auth import Auth, DeviceInfo, register_device_with_token
from .signer import Signer
from .api import STKClient, upload_file
import json


def main(file_path):
    file_size = os.path.getsize(file_path)
    author="calibre"
    title="Hacker Newsletter"
    s = JSONConfig("storage.json", "")
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
    c = STKClient(Signer.from_device_info(device_info))
    devices = c.get_list_of_owned_devices()
    remote = c.get_upload_url(file_size)
    upload_file(remote.upload_url, file_path)
    c.send_to_kindle(remote.stk_token, [d.device_serial_number for d in devices.owned_devices], author=author, title=title)

if __name__ == "__main__":
    main(sys.argv[1])

from .auth import DeviceInfo
from .signer import Signer

DEVICE_INFO_XML = '''
<?xml version="1.0" encoding="UTF-8"?>
<response><store_authentication_cookie>1Rq6uKVNO3yS+f5PtthBMV1NUrU5iMa9csg/OHU4/VamaYEGmYzMU2Vzt6UsOZh3idhqBZUi7aYUnjlbs9G+MqArtsWTQheQPfOF2L1mpwEBPeOyWSlgdvwxqdlFcxRIqbRf7Wid0ou8RUCGOLtWpxtYuZGe7v4Hsjwbt54fvCLT2FaQj9oqbQ1P4aZiIMyO</store_authentication_cookie><device_private_key>MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC8cC1MYP95b7PY4Dj6DrPAZs4zZJEBriPZPSIu8Zd+j7lw1Jgwvpl1j4lyjoQUdIODHNH171tzJCssJL8wuF/yEppowAn7tMWz3fvxOrX4pxm2wOKBTXf3U7MIuZe2OiIbgn/08z0ouhkiJ9KxkdAunPhKOZGQGaO1UfHP7Lb98zYZRFoPNMZaBEUP4afktrOaO7n7OmpBjKX+sDCblolj8I3m+xD4a1dbnXzbGU+btxk2gIJ8NoXLmEHiGYwqTMMfrjb1xNLaek7D0zc24ALK9jRyLkCK8j72YytKqlS3M+Y5ezVGfuHp005foVYwgssamg3YEcokk6pKixbo7Vu1AgMBAAECggEBALPMRSyPkLQKBQx2RWczCAgZD76xwjpcMhBh6G/qTKaR9FrYPq6j7kDhyD/qA9SQp7s+kIec7yEZ7aedGGAgTEvpvDMeqWflwI4yzOYLIv4yUrKxsG23wTPYRQeaLkvNhCXDitvqCv0FNF4GqV6MxprzY2VPMLjR/gZQPe4q6x+6fsaePdbs2u1k4I5O02eE4IsiciK4qoLYpqTFV9SoRLzHexEmzJLCD3rc9pI5keMdv+iVzrxaVJPRKIKCBl4CpzsODjrF7l8EGQfWOTKcO0UmBOqMba9rg8AxOCsnIlNcEfGEksfhFL0MGqHKclbudzZkH4aKGnE4Gh1uYZeYOQECgYEA9RjzSwtGB3wmEnO5d8fQbcUBFx95rw62BRaXDBZwj78wS7h1i5gJrdRyYENhRXw3USdwmL3mDesgJ6qfXKVfngt8W4URvwkSkrg0/RuR5IV7eW1LAgSuGMKQEF1Ok9rXsgL7yuS3ax9D7Aq138C2q82phi7zGbFLa7DSM49UwRECgYEAxNIEw0X7Fc/eG5sHk7uHaJkq3Hq7dAg7gzprIgXYCbQo2adRHKoX/tuIpLGXgDA8jBTvGV8JYL7kXDpqHhhvB/jwwkR8FVp5ssseGZTObgw5mKT0LPhunVYUFQfKoGkVGH+z6iBTjg1iskUMIaeNkzQiG4FSCgcYL1DVExOqMGUCgYEA3taFdOhWDj4Y21Pt/3JjFTo1SJGsb7XfVfb489t/EaKRRXb7ICTmP+5U4yK/0I4kORuzqpuVC3iH7qiZZYFR0v68XPU6ckbMZSsnuiwT1AJshbURqk8Y/pf+pXJAG/uvekBuL0UNYk610WjXfQzYyJEfHUmYavagDNRh+NDLDRECgYB6pcEQCmDPk8v9edr75WUY+jFqWRTM1oB3YwT1m5ynV1wJXak+6oOvbhA1SPF2kRh51mW0crN+VRYqnsAX5vPxjOBCvrhv+gRSNR6ZpFAK5ZVSmKAMEfekFcrH3CYZVcIulQ2BPQm0QIUbP8mygx3G+Dq01x5PX2JjwcQ1chCgvQKBgFNG9++kP91RFH4LvV7eb2U72nhSOur53Dx6AwilEDTFmparRS7gipe1OvCKzynoYP816rCcjanezhW7hcS7r7VAJb/dVjOsuLJCSVgTc8qjrZMWs7aJx9pNzhZGJ6TMS9xru98dmHJX0zzrZg9QedEYPlxSbvgGQmzp977QqDWi</device_private_key><adp_token>{enc:RO6CkSjmVSIZJZNJv17YI1nhA0W5QrW3DiJ0SJtNelUX/XXu8VN5KBcMe61E3EaY6YHUJFE8GYjRQSd2npAhRLox5Thq480f7opOHGlXhxvgPUiNiOIjLhJvV4yWby2nS8yrBK2fM2e7koVQTgRhgO+Q8kS2S/Vwew00E/BtnbQadRJRXzf9nzaeoqlU5L+renYnpNn1zrnOWpK9iYlNaAfIavVTy+Msy9bm12ttk6conNnvEhZWqNj1GcCL0BkuSwgQepwHgIc+qlsQtMKmRjXEczZ3ly3S0VuXhMeymJ1K+ctxhHRN4FgUynUAG85l8VF3AXzGgel+0i/E5MeJsqu0j4vGD/scTHv9NVYWzk8XQYAL0A9KbUHfCM3yixLLr1eJ8NCrw6Xaz3hthgpB/A6BZwEzu3V+RjYHDL+MIi1X8+0V5Dha/QLvoWWjooZr7WO447O3SQBgPGYQnKmq4jnyixzTtEN7HSduFy6p00od0pmdxCrR0op65CQT5OJvgdjgPLLBmDvWvxrh1OjYgUXLbCGc8TtNI6+I6h3crz7K9IEytztwNfSDKYOvTP3pZN2MknRMIZpcR4xNIN1992aw/kpE2TQl8gG08bXf5boJToJrs+e85IdsSX4u8/I/7GnRb2+lsvmOOVXzIiTWI/fONqUWmHHzuQcdQtLbowsvAp76gJlajjsRHG9O19/97fO4QG79BQTJMeF5dPqtGpCnsOOyYzvvz7BvaFG5zWBAkzUV1XH2kAJXJ9ePPsbbhhH13IeBItmWsZKUOyDe6MPVCz6czzZxIDVCSVmUESNP4f5Q9vup4DE8sUWnAvlLlrna4VfyUWdBgym4qIOuCJfTUipVj/yCIs2cX6BG638Gf+56WXRXMjFHLw0M4nkRI/iyopEWUi8oz8HLgmk80GUTsOCWDe+UZSfY2xM7AOdA4jGwFmGAWvJayYJIIak3AZhK7K1PWhGhBrbGhmI37Us3VPdrzWIrVfNqATwXYg9rhrobQvl0nO/HoUc6yQLRp/H2f/RXdpFiE2U5YmcwtwoajcJcaP+LrKN0nEizXS+wDJA4hEP764DSBz5TzIDP}{key:hfc6hJP0yu+K4rUrBDNHxEMnJ4caIap/DxaJhSv4a6Oy/l1WKYd6lfhjvAFG5+8Xce0tfYLFKBZzHE1GWz1BE3VARCiSI03Fkt4F9ZDcSohe/XNWokC/kuAw1L3JRAN/kZ8hk+wt7LKAmWS35eIemKQ1Fh7AvlPc0i+rd/JTY1eKMbQvwxiwDAtnX56boOI4e+cpmAYdwYR1aLRypkEEVfUaQnGqQ8mdsrBveWTNeoPBr7oY/oXdGa3X4ceZqTEQCUyWkUjA6iN/g07oTaJ0RtbkINieIxD+yfDTdY/qlyX2LNJfVtuKhVFOjC3eogiYu6NF/IphIXmC+UM40hwVbQ==}{iv:rB7gMOt3y40wwbJanaHILQ==}{name:QURQVG9rZW5FbmNyeXB0aW9uS2V5}{serial:Mg==}</adp_token><device_type>A3VNNDO1I14V03</device_type><given_name>Patrick</given_name><name>Patrick Browne</name><account_pool>Amazon</account_pool><country_of_residence>FR<source_of_cor>CUSTOMER_ADDRESS</source_of_cor></country_of_residence><preferred_marketplace>A13V1IB3VIYZZH</preferred_marketplace><user_directed_id>amzn1.account.AGR5QVVM3IR5IXV2CDLYSNSOC7FA</user_directed_id><user_device_name>Patrick's 2nd Android Phone</user_device_name></response>
'''
EXPECTED_SIG = 'czUzgbTkzXs2/esqFMcbGuIAdVkRPBzYJFsOnHNep0sW/xyW5hCtOgphRAqZGnUP4jXVvHTf+dRsRg5wdSzcp8CG5POxXZ6Qi+0KeKWiraMNmdRP7+L1RLXJ5cgd/HLbrBqGYAK5+VEpNDRitNXBm4KJOysPWyvf5mU6tu0KoHCfEm0biNNjTEn54J+FaQlB0xYIb8WHct/vqTQGmKoKhZGsPe1L5HwzTZfg5Wdld9SjujgaW8uQmWJ7QpDJ0dw5Fv1W0x6fK+pM/rM/rPQ5XrbPYIeXSSPL6KKoqeIPpbwNrVHdgpeZAU/1BMIF7+zXQKv4L8IjFizgf+L2tqa6Yg==:2020-04-10T14:21:40Z'


def test_signer():
    date = '2020-04-10T14:21:40Z'
    request_path = '/FirsProxy/getStoreCredentials'
    device_info = DeviceInfo.from_xml(DEVICE_INFO_XML)
    signer = Signer.from_device_info(device_info)
    sig = signer.digest_header_for_request('GET', request_path, '', date)
    assert sig == EXPECTED_SIG

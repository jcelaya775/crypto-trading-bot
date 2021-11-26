import json
import hmac
import hashlib
import time
import requests
from requests.auth import AuthBase

secret_key = "Ro7rWGjNa2SFV2HCps7dI2dcmA7p9oxtM4Fni/klXXgwtjPMKvSSFtwPIMzDThjl+khvLBm0gvzqUa6P2b0UWA=="
api_key = "1ef5ed9b29f60de6ceb2205b0fbeb066"
api_pass = "wkxu5p46vkh"
api_url =

r = requests.post(api_url + 'accounts/primary/transactions',
                  json=tx, auth=auth)

timestamp = str(int(time.time()))
message = timestamp + request.method + request.path_url + (request.body or '')
signature = hmac.new(secret_key, message,
                     hashlib.sha256).hexdigest()

# Requires python-requests. Install with pip:
#
#   pip install requests
#
# or, with easy-install:
#
#   easy_install requests

import json
import hmac
import hashlib
import time
import requests
from requests.auth import AuthBase

# Before implementation, set environmental variables with the names API_KEY and API_SECRET
# API_KEY = ''
# API_SECRET = ''

# Create custom authentication for Coinbase API


class CoinbaseWalletAuth(AuthBase):
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    def __call__(self, request):
        timestamp = str(int(time.time()))
        message = timestamp + request.method + \
            request.path_url + (request.body or '')
        signature = hmac.new(self.secret_key, message,
                             hashlib.sha256).hexdigest()

        request.headers.update({
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
        })
        return request


auth = CoinbaseWalletAuth(API_KEY, API_SECRET)

# Get current user
r = requests.get(
    'https://api-public.sandbox.pro.coinbase.com/v2/user', auth=auth)
print(r.json())
# {u'data': {u'username': None, u'resource': u'user', u'name': u'User'...

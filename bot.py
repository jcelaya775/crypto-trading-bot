import cbpro
from requests.auth import AuthBase
import pandas as pd
import hmac
import json
import os
from dotenv import load_dotenv
import hashlib
import time


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


# get authentication variables
load_dotenv("auth_credentials.env")
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
api_pass = os.getenv("API_PASS")

auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

# data = pd.DataFrame(public_client.get_products())
# print(data.tail(6).T)

cb_access_time = auth_client.get_time()

api_secret = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

accounts = auth_client.get_accounts()
for account in accounts:
    if float(account["balance"]) != 0:
        print(json.dumps(account, indent=2))

# account_holds = auth_client.get_account_holds()
# print(json.dumps(account_holds, indent=2))

# print(json.dumps(auth_client.get_currencies(), indent=4))

# 1. Loop through each of our specified currencies
# 2. Calculate the lookback length based on the volatility(higher volatility, higher lookback length)
# 3. The highest price in the history of the lookback is the breakout level
# 4. If in breakout range and not in position -> buy
# 5. else if not in breakout range -> do nothing
# 6. For each position, set a trailing stop-loss order with a specified percentage of loss (i.e. 10 % )
# 7. Track price of currency
# 8. Compare current price with last stored price
# 9. If price goes up -> hodl and update stored price
# 10. else if price goes down, then check percentage loss
# 11. if percentage loss >= stop-loss -> sell
# else hodl!!
# 12. Rinse and repeat

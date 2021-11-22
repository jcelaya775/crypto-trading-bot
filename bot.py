import os
import cbpro
import json
from dotenv import load_dotenv
import pandas as pd
from coinbase.wallet.client import Client

load_dotenv("auth_credentials.env")
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
api_pass = os.getenv("API_PASS")

print(api_key)
print(api_secret)
print(api_pass)
auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

# data = pd.DataFrame(public_client.get_products())
# print(data.tail(6).T)

cb_access_time = auth_client.get_time()

accounts = auth_client.get_accounts()
for account in accounts:
    if float(account["balance"]) != 0:
        print(json.dumps(account, indent=2))

# account_holds = auth_client.get_account_holds()
# print(json.dumps(account_holds, indent=2))

# print(json.dumps(auth_client.get_currencies(), indent=4))

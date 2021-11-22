import cbpro
import json
import pandas as pd
from coinbase.wallet.client import Client

auth_client = cbpro.AuthenticatedClient(
    "384297671372c0a0c6301bcb7913ac8c", "rXEJogcEz5k+hIPLHdigM1mjuYuv4EkRku6mHUeh6fYip02dpxcaHvcEeQ7VxEr7EugGO4Dl+WGz57pLmt7bCg==", "a71nvq6710v")

# data = pd.DataFrame(public_client.get_products())
# print(data.tail(6).T)

cb_access_time = auth_client.get_time()

accounts = auth_client.get_accounts()
for account in accounts:
    if float(account["balance"]) != 0:
        print(json.dumps(account, indent=2))

account_holds = auth_client.get_account_holds(before=2)
print(json.dumps(account_holds, indent=2))

# print(json.dumps(auth_client.get_currencies(), indent=4))

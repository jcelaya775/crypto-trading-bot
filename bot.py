import cbpro, pandas as pd, hmac, json, os, hashlib, time
from requests.auth import AuthBase
from dotenv import load_dotenv


class CoinbaseWallet(AuthBase):
    def __init__(self, api_key, api_secret, api_pass):
        self.auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)
        self.positions = []
        stable_coins = []
        
    def __call__ (self):
        print(json.dumps(self.auth_client.get_product_ticker("BTC-USD"), indent=2))
        
    def getPositions(self):
        accounts = self.auth_client.get_accounts()
        
        for account in accounts:
            if float(account["balance"]) != 0:
                self.positions.append(account)

        print(json.dumps(self.positions, indent=2))
    
    def getStableCoins(self):
        currencies = self.auth_client.get_products()
        
        for currency in currencies:
            if currency["fx_stablecoin"] and currency["quote_currency"] == "USD":
                print(json.dumps(currency, indent=2))


def main():
    # get authentication variables
    load_dotenv("auth_credentials.env")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_pass = os.getenv("API_PASS")
    
    account = CoinbaseWallet(api_key, api_secret, api_pass)
    account.getStableCoins()
    account()

    
    # data = pd.DataFrame(public_client.get_products())
    # print(data.tail(6).T)

    # account_holds = auth_client.get_account_holds()
    # print(json.dumps(account_holds, indent=2))

    # print(json.dumps(auth_client.get_currencies(), indent=4))
    
main()

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

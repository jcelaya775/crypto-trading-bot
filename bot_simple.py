import cbpro
from cbpro.websocket_client import WebsocketClient
import pandas as pd
import numpy as np
import math
import hmac
import json
import os
import hashlib
import time
import datetime
from requests.auth import AuthBase
from dotenv import load_dotenv


class CoinbaseWallet(AuthBase):
    stablecoins = []

    def __init__(self, api_key, api_secret, api_pass, api_url):
        self.auth = cbpro.AuthenticatedClient(
            api_key, api_secret, api_pass, api_url)  # initialize client
        self.usdbalance = 0
        self.btcbalance = 0
        self.initialStopRisk = 0.96
        self.trailingStopRisk = 0.9
        self.ticker = 'BTC-USD'
        self.price = 0  # price of bitcoin
        self.initialStopPrice = 0
        self.adjustedStopPrice = 0
        self.buyPrice = 0
        self.high = 0  # highest price once in position
        self.invested = False
        self.lastOrder = None

        # self.update()
        # print(self.usdbalance)
        # print(self.auth.place_market_order(
        #         product_id=self.ticker, side='buy', funds=self.usdbalance))

        # orders = list(self.auth.get_fills(product_id=self.ticker))[0]
        # print(f'last order:\n{json.dumps(orders, indent=2)}')

    def round_decimals_down(self, number: float, decimals: int = 2):
        """
        Returns a value rounded down to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)

        factor = 10 ** decimals
        return math.floor(number * factor) / factor

    def updateBalances(self):
        for account in self.auth.get_accounts():
            if account['currency'] == 'USD':
                self.usdbalance = self.round_decimals_down(
                    float(account['available']), 2)
            if account['currency'] == 'BTC':
                self.btcbalance = self.round_decimals_down(
                    float(account['available']), 8)

    def update(self):
        self.lastOrder = list(self.auth.get_fills(product_id=self.ticker))[0]
        self.invested = True if self.lastOrder['side'] == 'buy' else False
        self.updateBalances()
        self.price = self.round_decimals_down(
            float(self.auth.get_product_ticker(self.ticker)['price']), 2)

    def runMarket(self):
        self.update()  # update fields

        stats24h = self.auth.get_product_24hr_stats(self.ticker)
        openPrice = float(stats24h['open'])

        delta = (self.price - openPrice) / openPrice

        print(
            f'Total account balance = ${round(self.usdbalance + (self.btcbalance * self.price), 2)}')
        print()
        print(f'USD balance = ${self.usdbalance}')
        print(f'BTC balance = ${self.btcbalance}')
        print()
        print(f'Current price is ${self.price}')
        print(f'24h gain/loss(%) = {"{:.2f}".format(delta*100)}%')

        # if not in position and 24h price drops at least 5%
        if not self.invested and delta < -0.05:
            # buy btc
            self.auth.place_market_order(
                product_id=self.ticker, side='buy', funds=(self.usdbalance-1))
            print(
                f'\nBought {(self.usdbalance - 1) / self.price} BTC at ${self.price}!')
            self.invested = True

        # if in position and 24h price increases at least 5%
        if self.invested and delta >= 0.05:
            # sell btc
            self.auth.place_market_order(
                product_id=self.ticker, side='sell', size=self.btcbalance)
            print(f'\nSold {self.btcbalance} at ${self.price}')

        print('\n-----------------------------------\n')

    def launch(self):
        while True:
            self.runMarket()
            time.sleep(3)


def main():
    # get authentication variables
    load_dotenv('auth_credentials.env')
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    api_pass = os.getenv('API_PASS')
    api_url = 'https://api-public.sandbox.pro.coinbase.com'

    # initialize authenticated client
    client = CoinbaseWallet(api_key, api_secret, api_pass, api_url)
    print('Starting bot...')
    client.launch()


main()

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
        # print(self.auth.place_limit_order(
        #     product_id=self.ticker, side='sell', price=60000, size=self.btcbalance))

        # # self.auth.cancel_all()
        # self.openOrders = list(self.auth.get_orders())
        # print(json.dumps(self.openOrders, indent=2))

        orders = list(self.auth.get_fills(product_id=self.ticker))[0]
        print(f'last order:\n{json.dumps(orders, indent=2)}')

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
        self.openOrders = list(self.auth.get_orders())
        # print(json.dumps(self.openOrders, indent=2))

        self.lastOrder = list(self.auth.get_fills(product_id=self.ticker))[0]

        if self.lastOrder['side'] == 'buy':
            self.invested = True
        if self.lastOrder['side'] == 'sell':  # update position after selling
            sellPrice = self.round_decimals_down(
                float(self.lastOrder['price']), 2)
            print(f'Sold {self.btcbalance} BTC at ${sellPrice}!')
            self.invested = False

        self.updateBalances()
        self.price = self.round_decimals_down(
            float(self.auth.get_product_ticker(self.ticker)['price']), 2)

    def runMarket(self):
        self.update()  # update fields

        # step 1: calculate standard deviation of data from past 24 hours
        start_date = (datetime.datetime.now() -
                      datetime.timedelta(hours=24)).isoformat()  # date from 24 hour ago
        end_date = datetime.datetime.now().isoformat()  # today's date
        historic_rates = self.auth.get_product_historic_rates(
            self.ticker, start=start_date, end=end_date, granularity=300)  # prices from past 24 hours
        df = pd.DataFrame(historic_rates, columns=[
            'time', 'low', 'high', 'open', 'close', 'volume'])

        stats24h = self.auth.get_product_24hr_stats(self.ticker)
        openPrice = float(stats24h['open'])

        delta = (self.price - openPrice) / openPrice

        print(
            f'Account balance = ${self.usdbalance + (self.btcbalance * self.price)}')
        print(f'Current price is ${self.price}')
        print(f'24h gain/loss(%) = {"{:.2f}".format(delta*100)}%')

        # if not in position and price drops at least 5%
        if not self.invested and delta < 0:
            # execute a buy order
            order_size = self.round_decimals_down(
                ((self.usdbalance - 1) / self.price), 8)

            print(self.auth.place_market_order(
                product_id=self.ticker, side='buy', funds=self.usdbalance))

            self.invested = True

            formattedPrice = '{:.2f}'.format(self.price)
            print(f'Bought {order_size} BTC for ${formattedPrice}!')

            # set initial stop limit order
            self.initialStopPrice = self.round_decimals_down(
                self.price * self.initialStopRisk, 2)
            self.auth.place_limit_order(product_id=self.ticker,
                                        side='sell',
                                        price=self.initialStopPrice,
                                        size=self.btcbalance)
            print(
                f'Placed new limit sell order with risk of ${self.initialStopPrice * self.btcbalance}.')

        # if price continues to move beyond initial buy price -> update highest price and push trailing stop price higher
        if self.invested and self.price > self.high and self.price * self.trailingStopRisk > self.initialStopPrice:
            # update variables
            self.high = self.price
            self.adjustedStopPrice = self.high * self.trailingStopRisk
            print(f'adjusted stop price = ${self.adjustedStopPrice}')

            # update order
            self.auth.cancel_all()
            self.auth.place_limit_order(
                product_id=self.ticker, side='sell', price=self.adjustedStopPrice, size=self.btcbalance)
            print('Price increased: Updated stop loss.')

        print(f'invested = {self.invested}\n')

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
    # client.launch()


main()

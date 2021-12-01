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
        self.lookback = 5  # lookback length
        self.ceiling, self.floor = 10, 1  # upper and lower lookback limits
        self.initialStopRisk = 0.98
        self.trailingStopRisk = 0.9
        self.ticker = 'BTC-USD'
        self.price = 0  # price of bitcoin
        self.high = 0  # highest price once in position
        self.invested = False
        self.orders = []  # open orders

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

    def getBalances(self):
        for account in self.auth.get_accounts():
            if account['currency'] == 'USD':
                self.usdbalance = self.round_decimals_down(
                    float(account['available']), 2)
            if account['currency'] == 'BTC':
                self.btcbalance = self.round_decimals_down(
                    float(account['available']), 8)

    def update(self):
        # consider updating self.high
        self.orders = list(self.auth.get_orders())
        # if was in buying position and no longer in position -> sell order executed
        if self.invested == True and len(self.orders) == 0:
            sellPrice = '{:.2f}'.format(float(list(self.auth.get_fills(
                product_id=self.ticker))[-1]['price']))
            print(f'Sold BTC at ${sellPrice}!')
            self.invested = False
        self.getBalances()
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

        print(f'Current price is ${self.price}.')
        print(f'24h gain/loss(%) = {"{:.2f}".format(delta*100)}%')

        # if not in position and price drops at least 5%
        if not self.invested and delta < -.05:
            # execute a buy order
            order_size = self.round_decimals_down(
                ((self.usdbalance - 1) / self.price), 8)

            self.auth.place_market_order(
                product_id=self.ticker, side='buy', funds=order_size)

            self.buyPrice = self.price
            self.invested = True

            formattedPrice = '{:.2f}'.format(self.price)
            print(f'Bought {self.btcbalance} BTC for ${formattedPrice}!')

        if self.invested:
            order_size = self.btcbalance

            # if no open sell orders -> place new limit sell order
            if len(self.orders) == 0:
                self.initialStopPrice = self.buyPrice * self.initialStopRisk
                self.auth.place_limit_order(product_id=self.ticker,
                                            side='sell',
                                            price=self.initialStopPrice,
                                            size=order_size)
                print(
                    f'Place new limit sell order with intial risk of ${self.initialStopPrice}.')

            # if price continues to move beyond initial buy price -> update highest price and push trailing stop price higher
            if self.price > self.high and self.price * self.trailingStopRisk > self.initialStopPrice:
                # update variables
                self.high = self.price
                self.adjustedStopPrice = self.high * self.trailingStopRisk

                # update order
                self.auth.cancel_all()
                self.auth.place_limit_order(
                    product_id=self.ticker, side='sell', price=self.adjustedStopPrice, size=order_size)
                print('Price increased: Updated stop loss.')

        print()

    def launch(self):
        while True:
            self.runMarket()
            time.sleep(5)


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

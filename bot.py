import cbpro
from cbpro.websocket_client import WebsocketClient
import pandas as pd
import numpy as np
import hmac
import json
import os
import hashlib
import time
import datetime
from requests.auth import AuthBase
from dotenv import load_dotenv


# class TextWebSocketClient(cbpro.WebsocketClient):
#     def on_open(self):
#         self.url = 'wss://ws-feed.pro.coinbase.com/'
#         self.message_count = 0
#         print('hello world')

#     def on_message(self, msg):
#         self.message_count += 1
#         msg_type = msg.get('type', None)
#         if msg_type == 'ticker':
#             time_val = msg.get('time', ('-' * 27))
#             price_val = msg.get('price', None)
#             prive_val = float(
#                 price_val) if price_val is not None else 'None'
#             product_id = msg.get('product_id', None)
#         print(
#             f'{time_val:30} {price_val:.3f} {product_id}\tchannel type: {msg_type}')

#     def on_close(self):
#         print(
#             f'<---Websocket connection closed--->\n\tTotal messages: {self.message_count}')


class CoinbaseWallet(AuthBase):
    stablecoins = []

    def __init__(self, api_key, api_secret, api_pass, api_url):
        self.auth = cbpro.AuthenticatedClient(
            api_key, api_secret, api_pass, api_url)  # initialize client
        self.balance = self.getBalance()
        self.lookback = 20
        self.ceiling, self.floor = 30, 10  # upper and lower lookback limits
        self.initialStopRisk = 0.98
        self.trailingStopRisk = 0.9
        self.ticker = 'BTC-USD'
        self.security = self.auth.get_product_ticker(self.ticker)
        self.invested = False
        self.orders = []

    def getBalance(self):
        usd = None
        for account in self.auth.get_accounts():
            if account['currency'] == 'USD':
                usd = account

        return usd['balance']

    def update(self):
        self.orders = list(self.auth.get_orders())
        if len(self.orders) == 0:
            self.invested = False
        self.balance = self.getBalance()

    def buy(self):
        self.auth.place_market_order(product_id='BTC-USD',
                                     side='buy',
                                     funds='1000.00')

    def onMarketOpen(self):
        self.update()  # update fields

        # step 1: calculate standard deviation of data from past 31 days
        start_date = (datetime.datetime.now() -
                      datetime.timedelta(31)).isoformat()  # date from 31 days ago
        end_date = datetime.datetime.now().isoformat()  # todays' date
        historic_rates = self.auth.get_product_historic_rates(
            self.security, start=start_date, end=end_date, granularity=21600)  # prices from past 31 days
        df = pd.DataFrame(historic_rates, columns=[
            'time', 'low', 'high', 'open', 'close', 'volume'])

        today_vol = df['close'][1:31].std()  # today's volatility
        yesterday_vol = df['close'][0:30].std()  # yestereday's volatility
        delta_vol = (today_vol - yesterday_vol) / \
            today_vol  # difference in volatility
        # adjusted lookback length

        self.lookback = round(self.lookback * (1 + delta_vol))

        # ensure that lookback is within upper and lower bounds
        if self.lookback > self.ceiling:
            self.lookback = self.ceiling
        if self.lookback < self.floor:
            self.lookback = self.floor
        self.high = df['high']

        # if not in position and entered breakout level
        if not self.invested and self.security['close'] >= max(self.high[:-1]):
            # execute a limit buy order
            order_size = self.balance / self.security['close']
            self.auth.place_limit_order(
                product_id=self.ticker, side='buy', price=self.security['close'], size=order_size)
            self.breakoutlvl = max(self.high[:-1])
            self.invested = True

        if self.invested:
            # if no open sell orders -> place limit sell order
            if self.security and len(self.orders) == 0:
                self.initialStopPrice = self.breakoutlvl * self.initialStopRisk
                order_size = self.balance / self.initialStopPrice
                self.auth.place_limit_order(
                    product_id=self.ticker, side='sell', price=self.intitalStopPrice, size=order_size)

            # if price continues to move beyond initial buy price -> update highest price and trailing stop price
            if self.security['close'] > self.high and self.initialStopPrice < self.security['close'] * self.trailingStopRisk:
                # update variables
                self.high = self.security['close']
                self.adjustedStopPrice = self.high * self.trailingStopRisk
                order_size = self.balance / self.adjustedStopPrice

                # update order
                self.auth.cancel_all()
                self.auth.place_limit_order(
                    product_id=self.ticker, side='sell', price=self.adjustedStopPrice, size=order_size)

    def launch(self):
        while True:
            self.onMarketOpen()
            time.sleep(10)


def main():
    # get authentication variables
    load_dotenv('auth_credentials.env')
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    api_pass = os.getenv('API_PASS')
    api_url = 'https://api-public.sandbox.pro.coinbase.com'

    # initialize authenticated client
    client = CoinbaseWallet(api_key, api_secret, api_pass, api_url)
    client.launch()


main()

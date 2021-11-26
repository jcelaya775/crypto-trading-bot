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


class TextWebSocketClient(cbpro.WebsocketClient):
    def on_open(self):
        self.url = 'wss://ws-feed.pro.coinbase.com/'
        self.message_count = 0
        print('hello world')

    def on_message(self, msg):
        self.message_count += 1
        msg_type = msg.get('type', None)
        if msg_type == 'ticker':
            time_val = msg.get('time', ('-' * 27))
            price_val = msg.get('price', None)
            prive_val = float(
                price_val) if price_val is not None else 'None'
            product_id = msg.get('product_id', None)
        print(
            f'{time_val:30} {price_val:.3f} {product_id}\tchannel type: {msg_type}')

    def on_close(self):
        print(
            f'<---Websocket connection closed--->\n\tTotal messages: {self.message_count}')


class CoinbaseWallet(AuthBase):
    stablecoins = []

    def __init__(self, api_key, api_secret, api_pass, api_url):
        self.auth = cbpro.AuthenticatedClient(
            api_key, api_secret, api_pass, api_url)  # initialize client
        # self.balance =  # current account balance
        self.lookback = 20
        self.ceiling, self.floor = 30, 10  # upper and lower lookback limits
        self.initialStopRisk = 0.98
        self.trailingStopRisk = 0.9
        self.securities = self.getSecurities()
        self.positions = []

        print(json.dumps(self.auth.get_product_ticker('BTC-USD'), indent=2))
        # add an infinite loop that runs onMarketOpen continuously

    def __call__(self):
        print(json.dumps(self.auth.get_product_ticker('BTC-USD'), indent=2))

    def getSecurities(self):
        securities = ['BTC-USD', 'LINK-USD']
        rv = []

        for security in securities:
            rv.append(self.auth.get_product_ticker(security))

        return rv

    def onMarketOpen(self):
        # step 1: calculate standard deviation of data from past 31 days
        start_date = (datetime.datetime.now() -
                      datetime.timedelta(31)).isoformat()  # date from 31 days ago
        end_date = datetime.datetime.now().isoformat()  # todays' date

        for security in self.securities:
            historic_rates = self.auth.get_product_historic_rates(
                security, start=start_date, end=end_date, granularity=21600)  # prices from past 31 days
            df = pd.DataFrame(historic_rates, columns=[
                'time', 'low', 'high', 'open', 'close', 'volume'])

            today_vol = df['close'][1:31].std()  # today's volatility
            yesterday_vol = df['close'][0:30].std()  # yestereday's volatility
            print(today_vol, yesterday_vol)
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
            # if security not in self.positions and security['close'] >= max(self.high[:-1]):
            #     print('buy')


def main():
    # get authentication variables
    load_dotenv('auth_credentials.env')
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    api_pass = os.getenv('API_PASS')
    api_url = 'https://api-public.sandbox.pro.coinbase.com'

    client = CoinbaseWallet(api_key, api_secret, api_pass, api_url)

    client.onMarketOpen()

    # data = pd.DataFrame(public_client.get_products())
    # print(data.tail(6).T)


main()

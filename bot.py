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
        self.__auth_client = cbpro.AuthenticatedClient(
            api_key, api_secret, api_pass, api_url)  # initialize client
        self.balance = 10000
        self.lookback = 20
        self.ceiling, self.floor = 30, 10
        self.initialStopRisk = 0.98
        self.trailingStopRisk = 0.9
        self.positions = ['BTC-USD', 'LINK-USD']

    def __call__(self):
        print(json.dumps(self.__auth_client.get_product_ticker('BTC-USD'), indent=2))

    def getPositions(self):
        accounts = self.__auth_client.get_accounts()

        for account in accounts:
            self.positions.append(account)

        print(json.dumps(self.positions, indent=2))

    def onMarketOpen(self):
        # step 1: calculate standard deviation of data from past 31 days
        start_date = (datetime.datetime.now() -
                      datetime.timedelta(31)).isoformat()  # date from 31 days ago
        end_date = datetime.datetime.now().isoformat()  # todays' date
        historic_rates = self.__auth_client.get_product_historic_rates(
            'BTC-USD', start=start_date, end=end_date, granularity=21600)  # prices from past 31 days

        df = pd.DataFrame(historic_rates, columns=[
                          'time', 'low', 'high', 'open', 'close', 'volume'])
        today_vol = df['close'][1:31].std()  # today's volatility
        yesterday_vol = df['close'][0:30].std()  # yestereday's volatility
        # normalized difference in volatility
        delta_vol = (today_vol - yesterday_vol) / today_vol
        self.lookback = round(self.lookback * (1 + delta_vol))

    # def getHistory(self):
    #     accounts = self.__auth_client.get_accounts()

    #     for acc in accounts:
    #         currency = acc.get('currency')
    #         if currency == 'BTC':
    #             acc_id = acc.get('id')

    #     acc_history = self.__auth_client.get_account_history(acc_id)
    #     for hist in acc_history:
    #         print(json.dumps(hist, indent=2))


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

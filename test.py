import requests
import json
import pandas as pd

trades = pd.DataFrame(requests.get(
    'https://api.pro.coinbase.com/products/ETH-USD/trades').json())
print(trades.tail())

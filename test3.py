import requests

url = "https://api.exchange.coinbase.com/accounts"

headers = {
    "Accept": "application/json",
    "cb-access-key": "384297671372c0a0c6301bcb7913ac8c",
    "cb-access-passphrase": "a71nvq6710v",
    "cb-access-sign": "Jorge Celaya"
}

response = requests.request("GET", url, headers=headers)

print(response.text)

import json
import hmac
import hashlib
import time
import requests
from requests.auth import AuthBase


signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
print(str(int(time.time())))

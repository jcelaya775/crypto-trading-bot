import cbpro
import pandas as pd

cb = cbpro.PublicClient()

data = pd.DataFrame(cb.get_products())
print(data.tail(6).T)

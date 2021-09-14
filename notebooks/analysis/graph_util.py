import requests
import json
import pandas as pd

def fetch_safes(url):

    query = '''
    query {{
        safes(first: 1000, skip:{}) {{
            id
            collateral
            debt
        }}
    }}'''

    n = 0
    safes = []
    while True:
        r = requests.post(url, json = {'query':query.format(n*1000)})
        s = json.loads(r.content)['data']['safes']
        safes.extend(s)
        n += 1
        if len(s) < 1000:
            break
    safes = pd.DataFrame(safes)
    safes['collateral'] = safes['collateral'].astype(float)
    safes['debt'] = safes['debt'].astype(float)

    return safes

def fetch_rp(url):

    query =  '''
    query {
        systemState(id:"current") {
        currentRedemptionPrice {
            value }
        }
    }'''
    r = requests.post(url, json = {'query':query})
    s = json.loads(r.content)['data']['systemState']['currentRedemptionPrice']['value']

    return float(s)
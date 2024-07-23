import requests
import random
import os
from dotenv import load_dotenv, dotenv_values

config = dotenv_values(".env")

def load_proxies(file_path):
    with open(file_path, 'r') as file:
        proxies = file.readlines()
    proxies = [proxy.strip() for proxy in proxies]
    return proxies

proxies = load_proxies(os.path.join(os.getcwd(), 'tested_proxies.txt'))

def fetchTx(tx_id, proxy=None):
    if config['SOURCE'] == 'BLOCKCYPHER':
        base_url = 'https://api.blockcypher.com/v1/btc/main/txs/'
        url = f'{base_url}{tx_id}?limit=24385'
        try:
            # Send the GET request
            response = requests.get(url, proxies=proxy, timeout=int(config['MAX_TIMEOUT']), verify=False)
            if response.status_code == 200:
                json_data = response.json()
                return json_data
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None


def fetchAddrHist(addr, proxy=None):
    if config['SOURCE'] == 'BLOCKCYPHER':
        load_dotenv()
        base_url = 'https://api.blockcypher.com/v1/btc/main/addrs/'
        url = f'{base_url}{addr}'
        try:
            response = requests.get(url, proxies=proxy,timeout=int(config['MAX_TIMEOUT']), verify=False)
            if response.status_code == 200:
                json_data = response.json()
                return json_data
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None
    
def randomized_tx_fetch(tx_hash):
    source = config['SOURCE']
    tries = 0
    while True:
        if tries > int(config['MAX_TRIES']):
            return {}
        if proxies:
            proxy = random.choice(proxies)
            proxy_dict = {
                'https': f'socks5://{proxy}',
            }
        else:
            proxy = None
            proxy_dict = None
        try:
            if source == 'BLOCKCYPHER':
                res_json = fetchTx(tx_hash, proxy_dict)
            if res_json:
                print(f"Request success using proxy: {proxy}")
                return res_json
            else:
                tries += 1
        except requests.exceptions.RequestException as e:
            tries += 1

def randomized_addr_fetch(addr):
    source = config['SOURCE']
    tries = 0
    while True:
        if tries > int(config['MAX_TRIES']):
            return {}
        if proxies:
            proxy = random.choice(proxies)
            proxy_dict = {
                'https': f'socks5://{proxy}',
            }
        else:
            proxy = None
            proxy_dict = None
        try:
            if source == 'BLOCKCYPHER':
                res_json = fetchAddrHist(addr, proxy_dict)
            if res_json:
                print(f"Request success using proxy: {proxy}")
                return res_json
            else:
                tries += 1
        except requests.exceptions.RequestException as e:
            tries += 1

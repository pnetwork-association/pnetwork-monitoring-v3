import aiohttp
import asyncio
import json
import logging
import os
import requests
import statistics
import time

from checks_mapping import CHECKS_MAPPING
from config import RPC_ENDPOINTS, SUBPUB_CONFIG
from constants import CHAIN_DECIMALS, COINGECKO_MAPPING, CONST, FACTORY_ADDRS_DICT
from web3 import Web3


log = logging.getLogger()

class StdErrFilter(logging.Filter):
    def filter(self, rec):
        """
        Logger stderr filter

        Args:
            rec: record to log (or filter out)
        """
        return rec.levelno == logging.ERROR

class StdOutFilter(logging.Filter):
    def filter(self, rec):
        """
        Logger stderr filter

        Args:
            rec: record to log (or filter out)
        """
        return rec.levelno == logging.INFO

def is_value_missing_in_config():
    """
    Look for missing values in the config file

    Returns:
        missing_values_list (list) if missing fields, empty list if none
    """
    config_merged_dict = {**RPC_ENDPOINTS, **SUBPUB_CONFIG}
    missing_values_list = []
    for key, val in config_merged_dict.items():
        if not val and val != 0:
            missing_values_list.append(key)
    if missing_values_list:
        return missing_values_list
    else:
        return []

def is_check_in_mapping(check):
    """
    Check if the monitoring checks the user requested are enabled on the CHECKS_MAPPING dict

    Args:
        check (str): name or number of the requested check

    Returns:
        (bool): True if check is enabled, False if it is not
    """
    try:
        if check.isdigit():
            if int(check) not in CHECKS_MAPPING.keys():
                return False
        else:
            if check not in CHECKS_MAPPING.values():
                return False
        return True
    except Exception as e:
        log.error(f'[!] Error while checking on mapping: {e}')

def is_blocks_per_day_file_older_than_a_day():
    """
    Check if the `blocks_per_day.json` file is older than a day

    Returns: (bool) True if older, False if not
    """
    try:
        if int(os.path.getctime('blocks_per_day.json')) > 86400:
            return True
        return False
    except FileNotFoundError:
        return True

async def get_block_by_number_async(block_num, endpoint, session, ret_block_num=False):
    """
    Call `eth_getBlockByNum` for a given hex block number

    Args:
        block_num (str): hex block number (or `latest`)
        session (ClientSession): aiohttp session
        endpoint (str): endpoint for the given chain
        ret_block_num (bool): if True, return the block number along with the timestamp

    Returns:
        block timestamp (int) and block number if `ret_block_num` is True
    """
    data = {
        'method': 'eth_getBlockByNumber',
        'params': [block_num, False],
        'id': 1,
        'jsonrpc': '2.0'
    }
    try:
        async with session.post(endpoint, json=data) as resp:
            req = await resp.json()
        if ret_block_num:
            return int(req['result']['timestamp'], 16), int(req['result']['number'], 16)
        else:
            return int(req['result']['timestamp'], 16)
    except Exception as e:
        log.error(f'[!] Error while getting block by number: {e}')

async def dump_blocks_per_day_on_file():
    """
    Get blocks per day for all the enabled chains and dump on file
    """
    blocks_per_day_dict = dict()
    for chain, endpoint in RPC_ENDPOINTS.items():
        try:
            async with aiohttp.ClientSession() as session:
                latest_ts, latest_block = await get_block_by_number_async('latest', endpoint,
                                                                          session, ret_block_num=True)
                tasks = []
                for n in range(100, 2000, 100):
                    tasks.append(asyncio.ensure_future(get_block_by_number_async(hex(latest_block - n),
                                                                                 endpoint, session)))
                r1 = await asyncio.gather(*tasks)
                diff_list = [(r1[i] - r1[i + 1]) / 100 for i in range(len(r1) - 1)]
                median = round(statistics.median(diff_list), 2)
                blocks_per_day = int(86400 / median)
                blocks_per_day_dict[chain] = blocks_per_day
        except Exception as e:
            log.error(f'[!] Error while calculating blocks per day for {chain}: {e}')
            continue
    with open('blocks_per_day.json', 'w+') as f_blocks_per_day:
        json.dump(blocks_per_day_dict, f_blocks_per_day)
    return

def get_abi_from_addr(chain, addr):
    """
    Load the relative abi in `abi/` by the format `abi/<chain>_<addr>_abi.json`.
    If it's missing, throw an error and return empty list

    Args:
        chain (str): chain name
        addr (str): contract address

    Returns:
        abi (list): contract abi, [] if abi json missing
    """
    try:
        if not os.path.exists(CONST['abi_path'].format(chain, addr)):
            log.error(f'[!] Missing abi for {addr} on {chain}')
            return []
        else:
            with open(CONST['abi_path'].format(chain, addr), 'r') as f_abi_r:
                abi = json.load(f_abi_r)
            return abi
    except Exception as e:
        log.error(f'[!] Error while downloading abi for {chain}: {e}')

def get_proxy_contract_impl_addr(contract_addr, endpoint):
    """
    Get the implementation address for a given contract address using the `implementation_slot`

    Args:
        contract_addr (str): proxy contract address
        endpoint (str): endpoint for the given contract's chain

    Returns:
        impl_addr (str): implementation address
    """
    try:
        w3 = Web3(Web3.HTTPProvider(endpoint))
        impl_addr_unf = Web3.to_hex(w3.eth.get_storage_at(Web3.to_checksum_address(contract_addr),
                                                          CONST['implementation_slot']))
        impl_addr = f'0x{impl_addr_unf[2:].lstrip("0")}'
        return impl_addr
    except Exception as e:
        log.error(f'[!] Error while getting proxy impl addr for {contract_addr} via {endpoint}: {e}')

def call_contract_method(addr_unf, chain, endpoint, method,
                         abi_addr_unf=None, method_args=None):
    """
    Call a given function (from `contract.functions`) passing the given args (if any)
    and return the results

    Args:
        addr_unf (str): unformatted contract address
        chain (str): chain name
        endpoint (str): endpoint of the given chain
        method (str): method to call
        abi_addr_unf (opt) (str): unformatted abi address
        method_args (opt) (list): list of args to pass

    Returns:
        method_res (any): call results
    """
    try:
        addr = Web3.to_checksum_address(addr_unf)
        if abi_addr_unf:
            abi_addr = Web3.to_checksum_address(abi_addr_unf)
        else:
            abi_addr = addr
        abi = get_abi_from_addr(chain, abi_addr)
        w3 = Web3(Web3.HTTPProvider(endpoint))
        contract = w3.eth.contract(address=addr, abi=abi)
        if method_args:
            call = getattr(contract.functions, method)(*method_args)
        else:
            call = getattr(contract.functions, method)()
        method_res = call.call()
        return method_res
    except Exception as e:
        log.error(f'[!] Error while calling {method}({method_args}) on {chain}: {e}')

def get_hub_addr_from_factory_list():
    """
    Loop the endpoint list and extract hub contract address from factory
    address calling the `hub` method

    Returns:
        hub_addr_list (list): list of hub addresses
    """
    hub_addr_list = list()
    for chain, endpoint in RPC_ENDPOINTS.items():
        try:
            w3 = Web3(Web3.HTTPProvider(endpoint))
            factory_addr_unf = FACTORY_ADDRS_DICT[chain]
            factory_addr = Web3.to_checksum_address(factory_addr_unf)
            abi = get_abi_from_addr(chain, factory_addr)
            contract = w3.eth.contract(address=factory_addr, abi=abi)
            call_hub_addr = contract.functions.hub()
            hub_addr = call_hub_addr.call()
            hub_addr_list.append({'chain': chain,
                                  'addr': hub_addr})
        except Exception as e:
            log.error(f'[!] Error while getting hub address for {chain}: {e}')
            continue
    return hub_addr_list

def get_latest_block_by_chain(endpoint):
    """
    Get latest block of a given chain via its endpoint

    Args:
        endpoint (str): endpoint of the given chain

    Returns:
        block_num (int): latest block number of the given chain
    """
    try:
        payload = json.dumps({
            'method': 'eth_getBlockByNumber',
            'params': ['latest', False],
            'id': 1,
            'jsonrpc': '2.0'
        })
        res = requests.post(endpoint, data=payload).json()
        block_num = int(res['result']['number'], 16)
        return block_num
    except Exception as e:
        log.error(f'[!] Error while getting latest block on {endpoint}: {e}')

def get_blocks_range_by_ts(chain, nr_of_days):
    """
    Get blocks numbers for a given range (from, to) of days in the past

    Args:
        chain (str): chain name
        nr_of_days (int): number of days in the past

    Returns:
        _from (int): start block (past)
        to (int): latest block (now)
    """
    try:
        with open('blocks_per_day.json') as f_blocks_per_day:
            blocks_per_day_dict = json.load(f_blocks_per_day)
        breakpoint()
        nr_of_blocks_in_the_past = blocks_per_day_dict[chain] * nr_of_days
        to = get_latest_block_by_chain(RPC_ENDPOINTS[chain])
        _from = to - nr_of_blocks_in_the_past
        return int(_from), int(to)
    except Exception as e:
        log.error(f'[!] Error while getting block by timestamp for {chain}: {e}')

def get_block_ts_by_number_sync(block, chain):
    """
    Get block's timestamp given its value (in hex) and its chain

    Args:
        block (hex): block number
        chain (str): chain name

    Returns: block's timestamp (int)
    """
    try:
        url = RPC_ENDPOINTS[chain]
        payload = json.dumps({
            'method': 'eth_getBlockByNumber',
            'params': [block, False],
            'id': 1,
            'jsonrpc': '2.0'
        })
        res = requests.post(url, data=payload).json()
        return int(res['result']['timestamp'], 16)
    except Exception as e:
        log.error(f'[!] Error while getting block timestamp for {block}: {e}')

def call_get_logs(addr, chain, url, topic):
    """
    Call `eth_getLogs` method and search for a given topic0 and return the results

    Args:
        addr (str): hub address
        chain (str): chain name
        url (str): endpoint url
        topic (str): event's topic to search for

    Returns:
        logs (list): list of dict containing the results of the call, [] if none found
    """
    try:
        logs = []
        _from, to = get_blocks_range_by_ts(chain, CONST['get_logs_past_days'])
        _to = _from
        nr_of_calls = 1
        if to - _from > CONST['quicknode_max_block_range_getlogs']:
            nr_of_calls = int((to - _from) / CONST['quicknode_max_block_range_getlogs'])
        for _ in range(nr_of_calls + 1):
            if (to - _to) > CONST['quicknode_max_block_range_getlogs']:
                _to += CONST['quicknode_max_block_range_getlogs']
            else:
                _to = to
            payload = json.dumps({
                'method': 'eth_getLogs',
                'params': [{
                    'address': addr,
                    'topics': topic,
                    'fromBlock': hex(_from),
                    'toBlock': hex(_to)
                }],
                'id': 1,
                'jsonrpc': '2.0'
            })
            res = requests.post(url, data=payload).json()
            if 'result' in res and len(res['result']) > 0:
                for tx in res['result']:
                    logs.append(tx)
            _from += CONST['quicknode_max_block_range_getlogs']
            time.sleep(1)
        if logs:
            return logs
        else:
            return []
    except Exception as e:
        log.error(f'[!] Error while calling getLogs for {url}: {e}')

def get_balance_by_chain_and_addr(addr, chain, endpoint):
    """
    Get balance for a given address, on a given chain

    Args:
        addr (str): address to check the balance of
        chain (str): chain where to check the balance on
        endpoint (str): endpoint of the given chain

    Returns:
        balance (float)
    """
    try:
        payload = json.dumps({
            'method': 'eth_getBalance',
            'params': [addr, 'latest'],
            'id': 1,
            'jsonrpc': '2.0'
        })
        res = requests.post(endpoint, data=payload).json()
        balance_wei = int(res['result'], 16)
        if balance_wei > 0:
            return int(res['result'], 16) / float(f'1e{CHAIN_DECIMALS[chain]}')
        else:
            return 0
    except Exception as e:
        log.error(f'[!] Error while getting balance for {addr} on {chain}: {e}')

def get_enabled_tokens_usd_price():
    """
    Get USD price of all the enabled tokens

    Returns:
        prices_dict (dict): token:value dict, token/chain name and relative USD price
    """
    try:
        headers = {'accept': 'application/json'}
        params = {
            'ids': 'ethereum,matic-network,binancecoin',
            'vs_currencies': 'usd'
        }
        prices_req = requests.get(CONST['coingecko_prices_url'], params=params,
                                  headers=headers).json()
        keys = prices_req.keys()
        values = [round(val, 2) for price in list(prices_req.values()) for key, val in price.items()]
        prices_dict = dict(zip([COINGECKO_MAPPING[key] for key in keys], values))
        return prices_dict
    except Exception as e:
        log.error(f'[!] Error while getting USD prices: {e}')

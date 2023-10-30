import json
import logging
import os
import requests
import time

from checks_mapping import CHECKS_MAPPING
from config import EXPLORERS_APIKEY, RPC_ENDPOINTS
from constants import CHAIN_DECIMALS, CONST, EXPLORERS_ENDPOINTS, FACTORY_ADDRS_DICT
from datetime import datetime, timedelta
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

def get_abi_from_addr(chain, addr):
	"""
	First look for the abi in `abi/` by the format `abi/<chain>_<addr>_abi.json`,
	if it's present, load it, otherwise download it from the relative explorer and return it as json
	(plus cache it in `abi/`)

	Args:
		chain (str): chain name
		addr (str): contract address

	Returns:
		abi (dict): contract abi
	"""
	try:
		if not os.path.exists(CONST['abi_path'].format(chain, addr)):
			abi_url = CONST['get_abi_addr_url'].format(EXPLORERS_ENDPOINTS[chain], addr,
														EXPLORERS_APIKEY[chain])
			abi_req = requests.get(abi_url).json()
			abi = abi_req['result']
			with open(CONST['abi_path'].format(chain, addr), 'w+') as f_abi_w:
				json.dump({'chain': chain,
						   'address': addr,
						   'abi': json.loads(abi)},
						  f_abi_w)
			return json.loads(abi)
		else:
			with open(CONST['abi_path'].format(chain, addr), 'r') as f_abi_r:
				abi_dict = json.load(f_abi_r)
			return abi_dict['abi']
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
		start_ts = int(datetime.timestamp((datetime.now() - timedelta(days=nr_of_days)).replace(hour=0,
																					            minute=0,
												        									    second=1,
																					            microsecond=0)))
		end_ts = int(datetime.timestamp(datetime.now()))
		url_from = CONST['get_block_nr_by_ts_url'].format(EXPLORERS_ENDPOINTS[chain], start_ts,
														   EXPLORERS_APIKEY[chain])
		_from = requests.get(url_from).json()['result']
		url_to = CONST['get_block_nr_by_ts_url'].format(EXPLORERS_ENDPOINTS[chain], end_ts,
														 EXPLORERS_APIKEY[chain])
		to = requests.post(url_to).json()['result']
		return int(_from), int(to)
	except Exception as e:
		log.error(f'[!] Error while getting block by timestamp for {chain}: {e}')

def get_block_ts_by_number(block, chain):
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
		_from, to = get_blocks_range_by_ts(chain, CONST['operation_cancelled_getlogs_days'])
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

def get_usd_price_of_token(chain):
	"""
	Get USD price of a given token (via the chain name)

	Args:
		chain (str): chain name

	Returns:
		price (float): USD price of the given token
	"""
	try:
		match chain:
			case 'bsc':
				chain_sym = 'bnb'
				sym = 'eth'
				url = CONST['token_price_url'].format(EXPLORERS_ENDPOINTS[chain], chain_sym,
													   EXPLORERS_APIKEY[chain])
				price_req = requests.get(url).json()
				price = round(float(price_req['result'][f'{sym}usd']), 2)
			case 'goerli':
				chain_sym = sym = 'eth'
				url = CONST['token_price_url'].format(EXPLORERS_ENDPOINTS[chain], chain_sym,
													   EXPLORERS_APIKEY[chain])
				price_req = requests.get(url).json()
				price = round(float(price_req['result'][f'{sym}usd']), 2)
			case 'polygon':
				chain_sym = sym = 'matic'
				url = CONST['token_price_url'].format(EXPLORERS_ENDPOINTS[chain], chain_sym,
													   EXPLORERS_APIKEY[chain])
				price_req = requests.get(url).json()
				price = round(float(price_req['result'][f'{sym}usd']), 2)
		return price
	except Exception as e:
		log.error(f'[!] Error while getting USD price for {chain}: {e}')

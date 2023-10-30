import json
import logging
import time

from . import utils
from config import RPC_ENDPOINTS
from web3 import Web3


log = logging.getLogger()

def nr_of_ops_in_queue():
	"""
	Loop endpoints list, call each factory contract
	and get results from `numberOfOperationsInQueue` method
	"""
	hub_addr_list = utils.get_hub_addr_from_factory_list()
	for chain, endpoint in RPC_ENDPOINTS.items():
		try:
			hub_addr_unf = [addr for addr in hub_addr_list if addr['chain'] == chain][0]['addr']
			hub_addr = Web3.to_checksum_address(hub_addr_unf)
			nr_of_ops_in_queue = utils.call_contract_method(hub_addr, chain, endpoint,
															'numberOfOperationsInQueue')
			log.info(json.dumps({
				'title': 'nr_of_ops_in_queue',
				'timestamp': int(time.time()),
				'chain': chain,
				'nr_of_ops_in_queue': nr_of_ops_in_queue,
			}, indent=4))
		except Exception as e:
			log.error(f'[!] Error while checking nr of operations in queue: {e}')
			log.info(json.dumps({
				'title': 'nr_of_ops_in_queue',
				'timestamp': int(time.time()),
				'chain': chain,
				'error': str(e)
			}, indent=4))
			continue

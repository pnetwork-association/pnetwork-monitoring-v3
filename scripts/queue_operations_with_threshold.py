import json
import eth_abi
import eth_utils
import logging
import time

from . import utils
from config import RPC_ENDPOINTS
from constants import CHAIN_ID, CONST, TOPICS


log = logging.getLogger()

def queue_operations_with_threshold():
    """
    Loop endpoints list, get the relative hub address and search for
    the OperationQueue method, within the time range set in the config
    """
    hub_addr_list = utils.get_hub_addr_from_factory_list()
    prices_dict = utils.get_enabled_tokens_usd_price()
    for chain, endpoint in RPC_ENDPOINTS.items():
        try:
            hub_addr = [addr for addr in hub_addr_list if addr['chain'] == chain][0]['addr']
            hub_logs = utils.call_get_logs(hub_addr, chain, endpoint,
                                           [TOPICS['operation_queued']])
            if hub_logs:
                for log in hub_logs:
                    data_res_b = eth_abi.abi.decode(['(bytes32,bytes32,bytes32,uint256,uint256,'
                                                     'uint256,uint256,uint256,uint256,address,'
                                                     'bytes4,bytes4,bytes4,bytes4,string,string,'
                                                     'string,string,bytes,bool)'],
                                                    eth_utils.decode_hex(log['data'][2:]))
                    tx_hash = eth_utils.encode_hex(data_res_b[0][1])
                    asset_amount_token = data_res_b[0][5]
                    chain_id_hex = eth_utils.encode_hex(data_res_b[0][11])
                    asset_amount_usd = prices_dict[chain]
                    threshold = False
                    if asset_amount_usd > CONST['queued_operation_amount_threshold']:
                        threshold = True
                    log.info(json.dumps({
                        'title': 'queue_operation_with_threshold',
                        'timestamp': int(time.time()),
                        'chain': chain,
                        'tx_hash': tx_hash,
                        'asset_amount_token': asset_amount_token,
                        'asset_amount_usd': asset_amount_usd,
                        'dest_chain_id_hex': chain_id_hex,
                        'dest_chain': CHAIN_ID[chain_id_hex],
                        'threshold': threshold
                    }, indent=4))
        except Exception as e:
            log.error(f'[!] Error while getting operationQueued events: {e}')
            log.info(json.dumps({
                'title': 'queue_operation_with_threshold',
                'timestamp': int(time.time()),
                'chain': chain,
                'error': str(e)
            }, indent=4))

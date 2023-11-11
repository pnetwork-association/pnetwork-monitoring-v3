import json
import logging
import time

from . import utils
from config import RPC_ENDPOINTS
from constants import TOPICS


log = logging.getLogger()

def operation_cancelled():
    """
    Loop endpoints list, get the relative hub address and search for
    the OperationCancelled method, within the time range set in the config
    """
    hub_addr_list = utils.get_hub_addr_from_factory_list()
    for chain, endpoint in RPC_ENDPOINTS.items():
        try:
            hub_addr = [addr for addr in hub_addr_list if addr['chain'] == chain][0]['addr']
            hub_logs = utils.call_get_logs(hub_addr, chain, endpoint,
                                           [TOPICS['operation_cancelled']])
            if hub_logs:
                for log in hub_logs:
                    block_ts = utils.get_block_ts_by_number_sync(log['blockNumber'], chain)
                    log.info(json.dumps({
                        'title': 'operation_cancelled',
                        'timestamp': int(time.time()),
                        'chain': chain,
                        'tx_hash': log['transactionHash'],
                        'block': int(log['blockNumber'], 16),
                        'block_ts': block_ts
                    }, indent=4))
        except Exception as e:
            log.error(f'[!] Error while getting operationCancelled events: {e}')
            log.info(json.dumps({
                'title': 'operation_cancelled',
                'timestamp': int(time.time()),
                'chain': chain,
                'error': str(e)
            }, indent=4))

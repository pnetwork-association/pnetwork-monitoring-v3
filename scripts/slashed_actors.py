import json
import logging
import time

from . import utils
from config import RPC_ENDPOINTS
from constants import CONST, TOPICS

log = logging.getLogger()

def slashed_actors():
    """
    Loop endpoints list, get the relative hub address and search for
    the ActorSlashed method, within the time range set in the config
    """
    hub_addr_list = utils.get_hub_addr_from_factory_list()
    for chain, endpoint in RPC_ENDPOINTS.items():
        try:
            hub_addr = [addr for addr in hub_addr_list if addr['chain'] == chain][0]['addr']
            hub_logs = utils.call_get_logs(hub_addr, chain, endpoint,
                                           [TOPICS['actor_slashed']],
                                           nr_of_days=CONST['get_logs_past_days_slashed_actors'])
            if hub_logs:
                for logs in hub_logs:
                    actor_addr_unf = logs['topics'][2]
                    actor_addr = f'0x{actor_addr_unf[2:].lstrip("0")}'
                    slash_epoch = int(logs['topics'][1], 16)
                    log.info(json.dumps({
                        'title': 'slashed_actors',
                        'timestamp': int(time.time()),
                        'chain': chain,
                        'actor_address': actor_addr,
                        'epoch': slash_epoch
                    }, indent=4))
        except Exception as e:
            log.error(f'[!] Error while getting ActorSlashed events: {e}')
            log.info(json.dumps({
                'title': 'slashed_actors',
                'timestamp': int(time.time()),
                'chain': chain,
                'error': str(e)
            }, indent=4))

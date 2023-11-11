import json
import logging
import time

from . import utils
from config import RPC_ENDPOINTS
from constants import COMPONENTS_MAPS, CONST


log = logging.getLogger()

def inactive_actors_by_epoch():
    """
    Get active and inactive actors (by type) for the current epoch
    """
    hub_addr_list = utils.get_hub_addr_from_factory_list()
    try:
        endpoint = RPC_ENDPOINTS[CONST['dao_chain']]
        hub_addr = [entry['addr'] for entry in hub_addr_list if entry['chain'] == CONST['dao_chain']][0]
        epoch_manager_addr = utils.call_contract_method(hub_addr, CONST['dao_chain'], endpoint, 'epochsManager')
        impl_addr = utils.get_proxy_contract_impl_addr(epoch_manager_addr, endpoint)
        current_epoch = utils.call_contract_method(epoch_manager_addr, CONST['dao_chain'], endpoint, 'currentEpoch',
                                                   abi_addr_unf=impl_addr)
        for actor_type in range(list(COMPONENTS_MAPS.keys())[-1] + 1):
            tot_active_actors = utils.call_contract_method(hub_addr, CONST['dao_chain'], endpoint,
                                                           'getTotalNumberOfActorsByEpochAndType',
                                                           method_args=[int(current_epoch), int(actor_type)])
            tot_inactive_actors = utils.call_contract_method(hub_addr, CONST['dao_chain'], endpoint,
                                                             'getTotalNumberOfInactiveActorsByEpochAndType',
                                                             method_args=[int(current_epoch), int(actor_type)])
            log.info(json.dumps({
                'title': 'inactive_actors_by_epoch',
                'timestamp': int(time.time()),
                'chain': CONST['dao_chain'],
                'epoch': current_epoch,
                'actors':
                    {
                        'actor_type': COMPONENTS_MAPS[actor_type],
                        'active_actors': tot_active_actors,
                        'inactive_actors': tot_inactive_actors
                    }
            }, indent=4))
    except Exception as e:
        log.error(f'[!] Error while getting inactive actors: {e}')
        log.info(json.dumps({
            'title': 'inactive_actors_by_epoch',
            'timestamp': int(time.time()),
            'chain': CONST['dao_chain'],
            'error': str(e)
        }, indent=4))

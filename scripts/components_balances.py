import json
import eth_abi
import eth_utils
import logging
import time

from . import utils
from config import RPC_ENDPOINTS
from constants import COMPONENTS_MAPS, CONST, RELAYERS, TOPICS


log = logging.getLogger()

def components_balances():
    """
    Get all the GovernanceMessageEmitter addresses (factory -> slasher -> reg_manager -> gov_msg_emitter)
    from the latest event (ActorsPropagated) on the DAO chain and then get the relative balances
    on each supported chain.
    """
    hub_addr_list = utils.get_hub_addr_from_factory_list()
    try:
        endpoint = RPC_ENDPOINTS[CONST['dao_chain']]
        hub_addr = [entry['addr'] for entry in hub_addr_list if entry['chain'] == CONST['dao_chain']][0]
        slasher_addr = utils.call_contract_method(hub_addr, CONST['dao_chain'], endpoint, 'slasher')
        reg_manager_addr = utils.call_contract_method(slasher_addr, CONST['dao_chain'], endpoint,
                                                      'registrationManager')
        impl_addr = utils.get_proxy_contract_impl_addr(reg_manager_addr, endpoint)
        gov_msg_emitter_addr = utils.call_contract_method(reg_manager_addr, CONST['dao_chain'], endpoint,
                                                          'governanceMessageEmitter',
                                                          abi_addr_unf=impl_addr)
        gov_msg_emitter_logs = utils.call_get_logs(gov_msg_emitter_addr, CONST['dao_chain'], endpoint,
                                                   [TOPICS['actors_propagated']],
                                                   nr_of_days=CONST['get_logs_past_days_components_balances'])
        if gov_msg_emitter_logs:
            event = gov_msg_emitter_logs[-1]
            actors_res = eth_abi.abi.decode(['address[]', 'address[]'],
                                            eth_utils.decode_hex(event['data'][2:]))
            actors_addr_list = list(actors_res[0])
            actors_type_list = [COMPONENTS_MAPS[int(actor, 16)] for actor in actors_res[1]]
            actors_tuple_list = list(zip(actors_addr_list, actors_type_list))
            if len(RELAYERS) > 0:
                actors_tuple_list += [(relayer_addr, 'relayer') for relayer_addr in RELAYERS]
            for chain, endpoint in RPC_ENDPOINTS.items():
                for actor in actors_tuple_list:
                    balance = utils.get_balance_by_chain_and_addr(actor[0], chain, endpoint)
                    log.info(json.dumps({
                        'title': 'components_balance',
                        'timestamp': int(time.time()),
                        'chain': chain,
                        'actor_addr': actor[0],
                        'actor_type': actor[1],
                        'balance': balance
                    }, indent=4))
    except Exception as e:
        log.error(f'[!] Error while getting components balances: {e}')
        log.info(json.dumps({
            'title': 'components_balance',
            'timestamp': int(time.time()),
            'chain': chain,
            'error': str(e)
        }, indent=4))

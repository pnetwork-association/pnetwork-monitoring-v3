CHAIN_DECIMALS = {
    'bsc': 18,
    'goerli': 18,
    'polygon': 18,
}

CHAIN_ID = {
    '0x5aca268b': 'bsc',
    '0xb9286154': 'goerli',
    '0xf9b459a1': 'polygon'
}

COINGECKO_MAPPING = {
    'binancecoin': 'bsc',
    'ethereum': 'goerli',
    'matic-network': 'polygon'
}

COMPONENTS_MAPS = {
    0: 'governance',
    1: 'guardian',
    2: 'sentinel'
}

CONST = {
    'abi_path': 'abi/{}_{}.json',
    'coingecko_prices_url': 'https://api.coingecko.com/api/v3/simple/price',
    'dao_chain': 'polygon',
    'get_logs_past_days_components_balances': 2,
    'get_logs_past_days_operation_cancelled': 2,
    'get_logs_past_days_queue_op_after_user_op': 2,
    'get_logs_past_days_queue_operations_with_threshold': 2,
    'get_logs_past_days_slashed_actors': 3,
    'get_logs_past_days_user_op': 2,
    'implementation_slot': '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc',
    'ipfs_pubsub_url': 'http://{}:{}/api/v0/pubsub/sub?arg={}',
    'jsonrpc_max_block_range_getlogs': 9999,
    'queued_operation_amount_threshold': 1,
}

FACTORY_ADDRS_DICT = {
    'bsc': '0xAc8C50d68480838da599781738d83cfBe1Bd43c0',
    'goerli': '0x204a1A1d79Fe5EcF86d5281FA9c6C4CCce80e384',
    'polygon': '0x4650787da4A497496e514EcCFd6F888B7804ebBe'
}

RELAYERS = []  # A list of relayers can be added here

TOPICS = {
    'actors_propagated': '0x7d394dea630b3e42246f284e4e4b75cff4f959869b3d753639ba8ae6120c67c3',
    'actor_slashed': '0x3d78448e3086a8762725bddb010d91cb9ab2ae6f79981de8abc8dc36aff2fd09',
    'operation_cancelled': '0x33fe909c76b8ce2d80c623608e768bdb2c69f1d53f55d56d0e562a6e9c567288',
    'operation_queued': '0xe7bf22971bde3dd8a6a3bf8434e8b7a7c7554dad8328f741da1484d67b445c19',
    'user_operation': '0x71d1a48fb10648c4ca31c3abd9a916f0f6545176b2387214ed134a71c924e79f'
}

import requests
import multibase
import json
import logging
import sys
import threading
import time

from config import SUBPUB_CONFIG
from constants import CHAIN_ID, CONST


log = logging.getLogger()

def subscribe(topic, callback, subs, timeout):
	"""
	Subscription function. Once called, it creates a thread for the listener using the given topic

	Args:
		topic (str): topic name
		callback (function): callback function
		subs (dict): subscriptions dictionary
		timeout: could be `infinite` (stay in listen) or an integer value
	"""
	try:
		if topic not in subs.keys():
			subs[topic] = [[], True]
		subs[topic][1] = True
		thread = threading.Thread(target=subscribe_thread,
								  args=(topic, callback, subs,))
		if timeout == 0:
			log.info(f'\n[!] Listening for messages ...\n')
			thread.start()
		elif timeout > 0:
			log.info(f'\n[!] Listening for messages for the next {CONST["pubsub_timeout"]} seconds ...\n')
			thread.daemon = True
			thread.start()
			time.sleep(timeout)
			sys.exit()
		else:
			log.error(f'[!] Timeout error while subscribing to {topic}')
	except Exception as e:
		log.error(f'[!] Error while subscribing to {topic}: {e}')

def subscribe_thread(topic, callback, subs):
	"""
	Subscription thread
	Get ipfs node's ip and port from config and open the listener
	Once a message is found, call the callback passing the needed field

	Args:
		topic (str): topic name
		callback (function): callback function
		subs (dict): subscriptions dictionary
	"""
	try:
		ip = SUBPUB_CONFIG['ipfs_url']
		port = SUBPUB_CONFIG['ipfs_port']
		with requests.post(CONST['ipfs_pubsub_url'].format(ip, port,
															multibase.encode('base64url',
																			 topic).decode('utf8')),
						   stream=True) as req:
			subs[topic][0].append(req)
			while True:
				for res in req.iter_lines():
					res_json = json.loads(res.decode('utf8'))
					res_json['data'] = multibase.decode(res_json['data'])
					callback(res_json['data'],
							 res_json['from'])
				if topic not in subs.keys() or subs[topic][0] is False:
					return
	except Exception as e:
		log.error(f'[!] Error while listening for the ipfs topic {topic}: {e}')

def on_event(data, cid):
	"""
	Called on event, when a message is found
	Get the details of the message and format the output

	Args:
		data (bytes): message from the ipfs pubsub
		cid (str): ipfs content identifier
	"""
	try:
		sync_state = list()
		event_dict = json.loads(data.decode('utf8'))
		sync_state_tmp = event_dict['syncState']
		for key, value in sync_state_tmp.items():
			chain_id = CHAIN_ID[key]
			latest_block = value['latestBlockNumber']
			latest_block_ts = value['latestBlockTimestamp']
			sync_state.append({
				'chain_id': chain_id,
				'latest_block': latest_block,
				'latest_block_ts': latest_block_ts
			})
		log.info(json.dumps({
			'title': 'ipfs_subpub_pnetwork_topics',
			'timestamp': int(time.time()),
			'message_timestamp': event_dict['timestamp'],
			'cid': cid,
			'actor': event_dict['actorType'],
			'versions': {
				'listener': event_dict['softwareVersions']['listener'],
				'processor': event_dict['softwareVersions']['processor']
			},
			'sync_state': sync_state
		}, indent=4))
	except Exception as e:
		log.error(f'[!] Error while formatting pubsub message {cid}: {e}')

def ipfs_subpub_pnetwork_topics():
	"""
	Subscribe to the given topic and open the listener
	"""
	subs = {}
	timeout = SUBPUB_CONFIG['pubsub_timeout']
	subscribe(SUBPUB_CONFIG['pubsub_topic'], on_event, subs, timeout)

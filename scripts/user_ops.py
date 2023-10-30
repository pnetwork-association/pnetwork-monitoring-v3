import logging
import requests
import time


log = logging.getLogger()

def user_ops():
	"""
	Loop chains list, call `eth_getLogs` and look for userops
	"""
	print('tbi')

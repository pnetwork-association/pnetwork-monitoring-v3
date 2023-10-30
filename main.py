import argparse
import importlib
import logging.config
import os
import sys

from checks_mapping import CHECKS_MAPPING
from scripts import *

# Logger instance
log = logging.getLogger()
log.setLevel(logging.INFO)
# Define and add stdout handler
formatter_stdout = logging.Formatter('')
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter_stdout)
# Apply stdout filter
stdout_handler.addFilter(utils.StdOutFilter())
log.addHandler(stdout_handler)
# Define and add stderr handler
formatter_stderr = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.ERROR)
stderr_handler.setFormatter(formatter_stderr)
# Apply stderr filter
stderr_handler.addFilter(utils.StdErrFilter())
log.addHandler(stderr_handler)

def load_modules(path):
	"""
	Dynamically load modules from a given path

	Args:
		path (str): absolute module's path
	"""
	try:
		files = os.listdir(path)
		modules = []
		for i in range(len(files)):
			module = files[i].split('.')
			if len(module) > 1:
				if module[0] != '__init__' and module[1] == 'py':
					module = module[0]
					modules.append(module)
		with open(f'{path}__init__.py', 'w') as f_mod:
			f_mod.write(f'__all__ = {str(modules)}')
	except Exception as e:
		log.error(f'[!] Error while loading modules: {e}')

def main():
	"""
	Load all the needed modules, parse user args and check if the requested monitoring checks are
	enabled, if so they will be called one by one
	"""
	try:
		load_modules('scripts/')
		help_epilog = ',\n'.join([f'  {k}: {v}' for k, v in CHECKS_MAPPING.items()])
		parser = argparse.ArgumentParser(description='Pnetwork Monitoring v3',
										 epilog=f'Possible checks are:\n{help_epilog}',
										 formatter_class=argparse.RawTextHelpFormatter)
		group = parser.add_mutually_exclusive_group()
		group.add_argument('-c', '--checks', nargs='+', help='choose the check/s to run')
		group.add_argument('-a', '--all', action='store_true', help='run all checks')
		parser.add_argument('-v', '--verbose', action='store_true', help='print check\'s labels')
		args = parser.parse_args()
		if args.all:
			list_of_checks = [str(k) for k, _ in CHECKS_MAPPING.items()]
			if args.verbose:
				verbose = True
			else:
				verbose = False
		elif not args.all:
			list_of_checks = args.checks
			if args.verbose:
				verbose = True
			else:
				verbose = False
		for check in list_of_checks:
			if not utils.is_check_in_mapping(check):
				log.error(f'[!] Error: check {check} does not exist')
				sys.exit(1)
			if check.isdigit():
				check_name = CHECKS_MAPPING[int(check)]
				if verbose:
					print(f'\n[+] Check `{check_name}` ({check}):\n')
			else:
				check_name = check
				print(f'\n[+] Check `{check_name}`:')
			mod = importlib.import_module(f'scripts.{check_name}')
			func = getattr(mod, check_name)
			func()
			if verbose:
				print('\n ##########################################\n')
	except Exception as e:
		log.error(f'[!] Error in main: {e}')

if __name__ == '__main__':
	main()

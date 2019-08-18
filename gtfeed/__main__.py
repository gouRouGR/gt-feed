import random
import re
import threading
import time
import yaml
import logging
import os
import argparse
import pystray
from os.path import abspath
from gtfeed import config
from peewee import SqliteDatabase
from pathlib import Path
from shutil import copyfile
from PIL import Image

log = logging.getLogger("GT")


class Tray:
	icon = pystray.Icon("name", Image.open(Path(os.path.dirname(os.path.abspath(__file__))) / "rss.png"))

	@staticmethod
	def run():
		Tray._setup()
		Tray.icon.run()

	@staticmethod
	def _setup():
		menu = (
			pystray.MenuItem('Run', Tray._action_run), pystray.MenuItem('Open Config', Tray._action_oconfig),
			pystray.MenuItem('Exit', Tray._action_exit))
		Tray.icon.menu = menu
		Tray.icon.update_menu()
		Tray.icon.visible = True

	@staticmethod
	def _action_run():
		print("action_run")
		main()

	@staticmethod
	def _action_oconfig():
		print("action_OConfig")
		os.system(str(Path.home() / ".gtfeed" / "config.yml"))

	@staticmethod
	def _action_exit():
		print("exit")
		Tray.icon.stop()
		os._exit(0)


def config_default(cfg: dict):
	return cfg['general']['username'] == 'username' and cfg['general']['password'] == 'password'


def setup_logging(logfile, level):
	lv = {"debug": logging.DEBUG,
	      "critical": logging.CRITICAL,
	      "error": logging.CRITICAL,
	      "warning": logging.CRITICAL,
	      "info": logging.CRITICAL
	      }
	if level not in lv.keys():
		log.error("loglevel should be one of \"%s\". Exiting..." % ",".join(lv.keys()))
		exit(0)
	log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
	file_handler = logging.FileHandler(logfile)
	file_handler.setFormatter(log_formatter)
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(log_formatter)
	root_logger = logging.getLogger()
	root_logger.addHandler(console_handler)
	root_logger.addHandler(file_handler)
	root_logger.setLevel(lv[level])


def parse_config():
	try:
		with open(str(cfg), 'r') as ymlfile:
			config.cfg = yaml.load(ymlfile, Loader=yaml.Loader)
			if config_default(config.cfg):
				log.error("You have to change the default credentials in the configuration file. "
				          "Config file in use: \"%s\"" % str(cfg))
				exit(0)
			config.db = SqliteDatabase(str(work_dir / Path(config.cfg['general']['db_path'])))

	except FileNotFoundError as e:
		log.error("Config file \"%s\" not found. Exiting..." % str(cfg))
		exit(0)


def init():
	global args
	global cfg
	global work_dir
	logging.getLogger().setLevel(logging.DEBUG)
	default_gt_dir = Path.home() / ".gtfeed"
	cur_dir = Path(os.path.dirname(os.path.abspath(__file__)))
	default_cfg_path = str(default_gt_dir / "config.yml")

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("-c", "--config", type=str, default=default_cfg_path,
	                    help="Path to the gtfeed config file. If it does not exist a default config will be generated at that location if the --generate-config flag is set")
	parser.add_argument("-g", "--generate-config", default=False, action="store_true",
	                    help="If set and the specified configuration file does not exist, it will be generated")
	parser.add_argument("--once", default=False, action="store_true",
	                    help="If specified, then gtfeed runs only once, by default it runs periodically.")
	args = parser.parse_args()

	cfg = Path(args.config)
	work_dir = cfg.parent
	if args.generate_config:
		p = abspath(str(cur_dir / "config.yml"))
		if not os.path.exists(str(work_dir)):
			os.makedirs(str(work_dir))
		if not os.path.exists(str(cfg)):
			copyfile(p, str(cfg))
			print("Default config file generated at " + str(cfg))
		else:
			print("Config file at %s already exists" % str(cfg))
		exit(0)

	parse_config()

	logfile = str(work_dir / Path(config.cfg['logging']['logfile']))
	level = config.cfg['logging']['loglevel']
	setup_logging(logfile, level)


def exec():
	from gtfeed.gtfeed import GT, \
		TorrentModel  # this needs to be called after the config initialization # TODO do this better, without having to import here

	filters = config.cfg['filtering']['filters']

	gt = GT(config.cfg['general']['username'], config.cfg['general']['password'])
	if not gt.login():
		log.error("Could not log in")
	else:
		torrent_list = gt.check_shoutbox(
			[re.compile(f, re.IGNORECASE) if config.cfg['filtering']['ignore_case'] else re.compile(f) for f in
			 filters])
		for t in torrent_list:
			if GT.downloaded(t):
				log.debug("Torrent %s with id %d has already been downloaded, skipping..." % (t.name, t.torrent_id))
			else:
				if gt.download_torrent(t, config.cfg['general']['download_folder']):
					TorrentModel.create(torrent_id=t.torrent_id, name=t.name, uploaded_by=t.uploaded_by)
	gt.close_db()
	log.info("Finish:  %s" % time.ctime())


def exec_thread():
	while True:
		exec()
		fluc = int(config.cfg['general']['fluctuation'])
		time.sleep(int(config.cfg['general']['delay']) + random.randint(-fluc, fluc))
		parse_config()


def main():
	init()

	if args.once:
		exec()
	else:
		threading.Thread(target=exec_thread).start()
		Tray.run()


if __name__ == "__main__":
	main()

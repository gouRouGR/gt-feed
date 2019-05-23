import re
import yaml
import logging
import os
import argparse
from os.path import abspath
from gtfeed import config
from peewee import SqliteDatabase
from pathlib import Path
from shutil import copyfile

log = logging.getLogger("GT")


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


def main():
	logging.getLogger().setLevel(logging.DEBUG)
	default_gt_dir = Path.home() / ".gtfeed"
	cur_dir = Path(os.path.dirname(os.path.abspath(__file__)))
	default_cfg_path = str(default_gt_dir / "config.yml")

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("-c", "--config", type=str, default=default_cfg_path,
	                    help="Path to the gtfeed config file. If it does not exists a default config will be generated at that location if the --generate-config flag is set")
	parser.add_argument("-g", "--generate-config", default=False, action="store_true",
	                    help="If set and the specified configuration file does not exist, it will be generated")
	args = parser.parse_args()

	cfg = Path(args.config)
	work_dir = cfg.parent
	if args.generate_config:
		p = abspath(str(cur_dir / ".." / "config.yml"))
		if not os.path.exists(str(work_dir)):
			os.makedirs(str(work_dir))
		if not os.path.exists(str(cfg)):
			copyfile(p, str(cfg))
			print("Default config file generated at " + str(cfg))
		else:
			print("Config file at %s already exists" % str(cfg))
		exit(0)


	try:
		with open(str(cfg), 'r') as ymlfile:
			config.cfg = yaml.load(ymlfile, Loader=yaml.Loader)
			if config_default(config.cfg):
				log.error("You have to change the default credentials in the configuration file. "
				          "Config file in use: \"%s\"" % str(cfg))
				exit(0)
			config.db = SqliteDatabase(str(work_dir / Path(config.cfg['general']['db_path'])))
			logfile = str(work_dir / Path(config.cfg['logging']['logfile']))
			level = config.cfg['logging']['loglevel']
			setup_logging(logfile, level)

	except FileNotFoundError as e:
		log.error("Config file \"%s\" not found. Exiting..." % str(cfg))
		exit(0)

	from gtfeed.gtfeed import GT, TorrentModel  # this needs to be after the config initialization

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
				gt.download_torrent(t, config.cfg['general']['download_folder'])
				TorrentModel.create(torrent_id=t.torrent_id, name=t.name, uploaded_by=t.uploaded_by)


if __name__ == "__main__":
	main()

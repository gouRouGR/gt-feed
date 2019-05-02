import sys
import re
import yaml
import logging
import os
from gtfeed import config
from peewee import SqliteDatabase
from pathlib import Path
from shutil import copyfile

log = logging.getLogger("GT")


def config_default(cfg: dict):
	return cfg['general']['username'] == 'username' and cfg['general']['password'] == 'password'


def main():
	args = sys.argv[:]

	gt_dir = Path.home() / ".gtfeed"
	cur_dir = Path(os.path.dirname(os.path.abspath(__file__)))

	if not os.path.exists(str(gt_dir)):
		os.makedirs(str(gt_dir))
	default_cfg_path = str(gt_dir / "config.yml")
	if not os.path.exists(default_cfg_path):
		copyfile(str(cur_dir / ".." / "config.yml"), default_cfg_path)

	cfg = default_cfg_path
	try:
		with open(cfg, 'r') as ymlfile:
			config.cfg = yaml.load(ymlfile, Loader=yaml.Loader)
			if config_default(config.cfg):
				log.error("You have to change the default credentials in the configuration file. "
				          "The default config file is in \"%s\"" % default_cfg_path)
				exit(0)
			config.db = SqliteDatabase(config.cfg['general']['db_path'])
	except FileNotFoundError as e:
		log.error("Config file \"%s\" not found. Exiting..." % cfg)
		exit(0)

	from gtfeed.gtfeed import GT, TorrentModel  # this needs to be after the config initialization

	filters = config.cfg['filtering']['filters']

	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)

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

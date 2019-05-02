import sys
import re
import yaml
import logging
from gtfeed import config
from peewee import SqliteDatabase


def main():
	args = sys.argv[:]

	with open("config.yml", 'r') as ymlfile:
		config.cfg = yaml.load(ymlfile, Loader=yaml.Loader)
		config.db = SqliteDatabase(config.cfg['general']['db_path'])

	from gtfeed.gtfeed import GT, TorrentModel  # this needs to be after the config initialization

	filters = config.cfg['filtering']['filters']
	log = logging.getLogger("GT")

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

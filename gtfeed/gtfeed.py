#!/usr/bin/python

import requests
import re
import logging
from pathlib import Path
from config import cfg, db
from peewee import Model, IntegerField, CharField

log = logging.getLogger("GT")


class BaseModel(Model):
	class Meta:
		database = db


class TorrentModel(BaseModel):
	torrent_id = IntegerField(unique=True)
	name = CharField()
	uploaded_by = CharField()


class Torrent:
	def __init__(self, torrent_id: int, name: str, uploaded_by: str):
		self.torrent_id = torrent_id
		self.name = name
		self.uploaded_by = uploaded_by


class GT:
	base_url = "https://www.greek-team.cc"
	login_url = base_url + "/login.php"
	shoutbox_url = "https://www.greek-team.cc/shoutbox.php"
	login_payload = {"take_login": 1, "logout": "no", "username": "", "password": ""}
	download_url = base_url + "/download2.php?torrent=%d"

	login_failed_re = re.compile(r"Login failed!")
	shout_t_re = re.compile(
		r"\[New Torrent\]</font></b><a href=\"details\.php\?id=(\d+)\"><b><.*?> (.*?)</font></b></a> Uploaded by <b><font color=.*?>(.*?)<")

	def __init__(self, username: str, password: str):
		self.username = username
		self.password = password
		self.session = requests.Session()
		db.connect()
		db.create_tables([TorrentModel])

	def downloaded(torrent: Torrent):
		return len(TorrentModel.select().where(TorrentModel.torrent_id == torrent.torrent_id)) == 1

	def check_shoutbox(self, tfilters=None) -> list:
		r = self.session.get(self.shoutbox_url)
		matches = GT.shout_t_re.finditer(r.text)
		tlist = []

		no_filters = tfilters is None or len(tfilters) == 0
		log.info("Total filters: %d", 0 if no_filters else len(tfilters))
		if not no_filters:
			log.debug("Filter list:")
			for f in cfg['filtering']['filters']:
				log.debug(f)
		log.debug("No torrents will pass as there is no filter" if no_filters else "Applying filters...")
		log.debug(" ============ Total torrents found in shoutbox ============")
		for m in matches:
			log.debug(m.group(2))
			if any([f.search(m.group(2)) for f in tfilters]):
				tlist.append(Torrent(int(m.group(1)), m.group(2), m.group(3)))
		log.debug(" ==========================================================")
		log.debug(" ========= Torrent list that passed the filtering =========")
		for t in tlist:
			log.debug(t.name)
		log.debug(" ==========================================================")

		return tlist

	def _lp(self, username: str, password: str) -> dict:
		lp = dict(self.login_payload)
		lp["username"] = username
		lp["password"] = password
		return lp

	def login(self) -> bool:
		r = self.session.post(self.login_url, data=self._lp(self.username, self.password))
		if r.status_code != 200 or GT.login_failed_re.search(r.text):
			return False
		else:
			return True

	def download_torrent(self, torrent: Torrent, folder=None):
		r = self.session.get(GT.download_url % torrent.torrent_id, stream=True)
		if r.status_code != 200:
			log.warning("Could not download torrent %s with id %d" % (torrent.name, torrent.torrent_id))
		else:
			if folder is not None:
				path = Path(cfg['general']['download_folder']) / (torrent.name + ".torrent")
			else:
				path = torrent.name + ".torrent"
			with open(path, "wb") as f:
				for chunk in r.iter_content(8192):
					f.write(chunk)
				log.info("Torrent \"%s\" with id %d downloaded" % (torrent.name, torrent.torrent_id))

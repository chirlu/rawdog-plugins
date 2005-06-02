import rawdoglib.plugins, rawdoglib.feedparser
import atomwriter
import os, time, errno
from pprint import pprint

class ArchiverException(Exception): pass

class Archiver:
	def __init__(self):
		self.articles = {}
		self.feeds = {}
		self.dir = os.getenv("HOME") + "/archive/feeds"
		self.now = 0

	def article_added(self, rawdog, config, article, now):
		feed = rawdog.feeds[article.feed]
		feed_id = feed.get_id(config)
		self.feeds[feed_id] = feed.feed_info

		l = self.articles.setdefault(feed_id, [])
		l.append(article.entry_info)

		self.now = now

		return True

	def shutdown(self, rawdog, config):
		day = time.strftime("%Y-%m-%d", time.localtime(self.now))

		for id, feed_info in self.feeds.items():
			if id == "":
				id = "unknown"

			entries = self.articles[id]
			config.log("Archiving ", len(entries), " articles for ", id)

			# Fix up links that contain non-ASCII characters but
			# are marked as ASCII -- I think this is a feedparser
			# bug?
			for entry in entries:
				if not "links" in entry:
					continue
				for link in entry["links"]:
					if not "title" in link:
						continue
					if type(link["title"]) is type(""):
						try:
							link["title"] = link["title"].decode("UTF-8")
						except:
							link["title"] = link["title"].decode("ISO-8859-1")

			dn = self.dir + "/" + id
			try:
				os.makedirs(dn)
			except OSError:
				pass

			seq = 0
			while 1:
				fn = "%s/%s-%s-%d.atom" % (dn, id, day, seq)
				try:
					fd = os.open(fn, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
				except OSError, (no, str):
					if no == errno.EEXIST:
						seq += 1
						continue
					else:
						raise ArchiverException("Error opening " + fn + ": " + str)
				break

			f = os.fdopen(fd, "w")
			atom_data = {"feed": feed_info, "entries": entries}
			#pprint(atom_data)
			atomwriter.write_atom(atom_data, f)
			f.close()

		return True

archiver = Archiver()
rawdoglib.plugins.attach_hook("article_added", archiver.article_added)
rawdoglib.plugins.attach_hook("shutdown", archiver.shutdown)


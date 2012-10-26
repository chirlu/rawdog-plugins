# rawdog plugin to chop the "whatever: " prefix off Twitter messages.
# (Although I wrote this a while ago, and it's probably not very useful now
# Twitter have essentially killed off their feeds.)
# Adam Sampson <ats@offog.org>

import rawdoglib.plugins

def article_seen(rawdog, config, article, ignore):
	if article.feed.startswith("http://twitter.com/statuses/"):
		detail = article.entry_info["title_detail"]
		i = detail["value"].find(": ")
		if i != -1:
			detail["value"] = detail["value"][i + 2:]
	return True

rawdoglib.plugins.attach_hook("article_seen", article_seen)

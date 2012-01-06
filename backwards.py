"""
backwards plugin for rawdog, by Adam Sampson <ats@offog.org>

Sort articles in the reverse of the usual order (i.e. oldest first).
"""

import rawdoglib.plugins

def backwards(rawdog, config, articles):
	articles.sort()
	articles.reverse()
	return False

rawdoglib.plugins.attach_hook("output_sort_articles", backwards)

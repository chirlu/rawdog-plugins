import rawdoglib.plugins

def backwards(rawdog, config, articles):
	articles.reverse()
	return False

rawdoglib.plugins.attach_hook("output_sort", backwards)


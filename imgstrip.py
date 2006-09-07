"""
rawdog plugin to strip img tags from articles.
author Virgil Bucoci <vbucoci at acm.org>
version 0.1
license: GNU GPL v2.0 

This rawdog plugin strips img tags from feed articles.  More and more
feeds include web-bug and advertisement images these days, the most
notorious example being slashdot.

Having only a couple of tens of bugged articles in a rawdog page
really slows down the page reload (because each web-bug image has a
unique URL/name in every article, so they can trace each article, even
though the images are identical and quite small as images go :D),
taking all the fun away from aggregating the feeds locally and
exposing you to privacy invasion.

By default, images are replaced with the string [img] linked to the
image source, but can also be removed without a trace.

Configuration options:

  imgstrip link
     (default) img tags are replaced with the string [img] linked to the
     image source

  imgstrip none
     img tags are simply removed from the article

TODO
  - make a per-feed setting, for feeds those images you want to see (flickr?)
  - something more general for stripping obnoxious tags: font, style,
    script/javascript (maybe tidy already does part of this?)
"""
import rawdoglib.plugins, re

none_i = '<img\\s[^>]*/?>'
# this is kind of kludgy, but it works for now
link_i = """
<img       # tag name
\\s        # whitespace
[^>]*      # anything but a >
src=       # attribute name
['"]?      # optional apostrophe or quote
([^ '"]*)  # image URL
['"]?      # optional apostrophe or quote
[^>]*      # anything but a >
/?         # optional /
>          # tag end
"""

none_repl = ' '
link_repl = '[<a href="\\1">img</a>]'

class ImgStripPlugin:
    """
    Strip img tags from articles.

    The image is replaced by default with a link to the image, but can
    also be only removed with the "imgstrip none" option.
    """
    def __init__(self, pat, repl):
        self.repl = repl
        self.img = re.compile(pat, re.IGNORECASE | re.VERBOSE)

    def imgstrip(self, config, html, baseurl, inline):
        """
        Strip <img> tags from the feed HTML.
        """
        html.value = self.img.sub(self.repl, html.value)

    def config_option(self, config, name, value):
        """
        Configures the stripping through the config file.

        name  - the option name, 'imgstrip'
        value - 'none': simply remove the img tag
                'link': replace the image with a link to image's source.
                        This is the default.
                anything else: raise ValueError
        """
        if name == 'imgstrip':
            if value == 'none':
                self.__init__(none_i, none_repl)
                return False
            elif value == 'link':
                self.__init__(link_i, link_repl)
                return False
            else:
            	raise ValueError, \
                      "imgstrip error: option '%s' has invalid value '%s'" \
                      % (name, value)
        return True

istrip = ImgStripPlugin(link_i, link_repl)
rawdoglib.plugins.attach_hook("clean_html", istrip.imgstrip)
rawdoglib.plugins.attach_hook('config_option', istrip.config_option)

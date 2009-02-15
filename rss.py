# -*- coding: utf-8 -*-
# A simple RSS 2.0 generator for rawdog
# Copyright 2008 Jonathan Riddell
# Copyright 2009 Adam Sampson <ats@offog.org>
#
# rawdog_rss is free software; you can redistribute and/or modify it
# under the terms of that license as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# rawdog_rss is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rawdog_rss; see the file COPYING. If not, write to the Free
# Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA, or see http://www.gnu.org/.
#
# Writes RSS feed at the end of a rawdog run 
# Put in <configdir>/plugins/rawdog_rss.py
# Add "outputxml /path/to/feed.rss" to config to set file out

import os, time, cgi
import rawdoglib.plugins, rawdoglib.rawdog
import libxml2

from time import gmtime, strftime

class RSS_Feed:
    def __init__(self):
        self.options = {
            "outputxml": "rss20.xml",
            "outputfoaf": "foafroll.xml",
            "outputopml": "opml.xml",
            }

        self.doc_open()

        self.xml_articles = self.xml.xpathEval('/rss/channel')[0]

        self.xml_articles.newChild(None, 'title', "Planet KDE")
        self.xml_articles.newChild(None, 'link', "http://planetKDE.org/")
        self.xml_articles.newChild(None, 'language', "en")
        self.xml_articles.newChild(None, 'description', "Planet KDE - http://planetKDE.org/")
        atomLink = self.xml_articles.newChild(None, 'atom:link', None)
        atomLink.setProp('href', 'http://planetKDE.org/rss20.xml')
        atomLink.setProp('rel', 'self')
        atomLink.setProp('type', 'application/rss+xml')

        self.foaf_articles = self.foafdoc_open()
        self.foaf_articles.newChild(None, 'foaf:name', "Planet KDE")
        self.foaf_articles.newChild(None, 'foaf:homepage', "http://planet.kde.org/")
        seeAlso = self.foaf_articles.newChild(None, 'rdfs:seeAlso', None)
        seeAlso.setProp('rdf:resource', '')

        self.opml_articles = self.opmldoc_open()

    def config_option(self, config, name, value):
        if name in self.options:
            self.options[name] = value
            return False
        else:
            return True

    def doc_open(self):
        self.doc = libxml2.newDoc("1.0")
        self.xml = self.doc.newChild(None, 'rss', None)

        self.xml.setProp('version', "2.0")            
        self.xml.setProp('xmlns:dc', "http://purl.org/dc/elements/1.1/")            
        self.xml.setProp('xmlns:atom', 'http://www.w3.org/2005/Atom')

        self.xml.newChild(None, 'channel', None)

    def foafdoc_open(self):
        self.foafdoc = libxml2.newDoc("1.0")
        self.foafxml = self.foafdoc.newChild(None, 'rdf:RDF', None)

        self.foafxml.setProp('xmlns:rdf', "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.foafxml.setProp('xmlns:rdfs', "http://www.w3.org/2000/01/rdf-schema#")
        self.foafxml.setProp('xmlns:foaf', "http://xmlns.com/foaf/0.1/")
        self.foafxml.setProp('xmlns:rss', "http://purl.org/rss/1.0/")
        self.foafxml.setProp('xmlns:dc', "http://purl.org/dc/elements/1.1/")

        return self.foafxml.newChild(None, 'foaf:Group', None)

    def opmldoc_open(self):
        self.opmldoc = libxml2.newDoc("1.0")
        self.opmlxml = self.opmldoc.newChild(None, 'opml', None)
        self.opmlxml.setProp('version', "1.1")

        head = self.opmlxml.newChild(None, 'head', None)
        head.newChild(None, 'title', "Planet KDE")
        head.newChild(None, 'dateCreated', strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + " +0000")
        head.newChild(None, 'dateModified', strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + " +0000")        
        head.newChild(None, 'ownerName', "Jonathan Riddell")
        head.newChild(None, 'ownerEmail', "")

        return self.opmlxml.newChild(None, 'body', None)

    def describe(self, parent, description):
        try:
            parent.newChild(None, 'description', description)
        except TypeError:
            print "TypeError in description"

    def __article_sync(self, xml_article, rawdog, config, article):
        entry_info = article.entry_info
        guid = xml_article.newChild(None, 'guid', article.hash)
        guid.setProp('isPermaLink', 'false')
        try:
            title = entry_info['title_raw'].encode('utf8', 'ignore')
        except KeyError:
            print "KeyError on title"
            return
        for feed in config["feedslist"]:
            if feed[0] == article.feed:
                title = feed[2]["define_name"] + ": " + title
        xml_article.newChild(None, 'title', title)
        date = strftime("%a, %d %b %Y %H:%M:%S", gmtime(article.date)) + " +0000"
        xml_article.newChild(None, 'pubDate', date)
        if entry_info.has_key('link'):
            xml_article.newChild(None, 'link', entry_info['link'])

        if entry_info.has_key('content'):
            for content in entry_info['content']:
                content = content['value']
        elif entry_info.has_key('summary_detail'):
            content = entry_info['summary_detail']['value']
        content = cgi.escape(content).encode('utf8', 'ignore')
        self.describe(xml_article, content)

        return True

    def __write(self):
        self.doc.saveFormatFile(self.options["outputxml"], 1)
        self.doc.freeDoc()

    def output_write(self, rawdog, config, articles):
        for article in articles:
            if article.date is not None:
                xml_article = self.xml_articles.newChild(None, 'item', None)
                self.__article_sync(xml_article, rawdog, config, article)

        self.__write()
        return True

    def shutdown(self, rawdog, config):
        for feed in config["feedslist"]:
            print str(feed)
            member = self.foaf_articles.newChild(None, 'foaf:member', None)
            agent = member.newChild(None, 'foaf:Agent', None)
            agent.newChild(None, 'foaf:name', feed[2]['define_name'])
            weblog = agent.newChild(None, 'foaf:weblog', None)
            document = weblog.newChild(None, 'foaf:Document', None)
            document.setProp('rdf:about', feed[0])
            seealso = document.newChild(None, 'rdfs:seeAlso', None)
            channel = seealso.newChild(None, 'rss:channel', None)
            channel.setProp('rdf:about', '')

            outline = self.opml_articles.newChild(None, 'outline', None)
            outline.setProp('text', feed[2]['define_name'])
            outline.setProp('xmlUrl', feed[0])

        self.foafdoc.saveFormatFile(self.options["outputfoaf"], 1)
        self.foafdoc.freeDoc()

        self.opmldoc.saveFormatFile(self.options["outputopml"], 1)
        self.opmldoc.freeDoc()

rss_feed = RSS_Feed()
rawdoglib.plugins.attach_hook("config_option", rss_feed.config_option)
rawdoglib.plugins.attach_hook("output_write", rss_feed.output_write)
rawdoglib.plugins.attach_hook("shutdown", rss_feed.shutdown)

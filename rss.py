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

    def config_option(self, config, name, value):
        if name in self.options:
            self.options[name] = value
            return False
        else:
            return True

    def describe(self, parent, description):
        try:
            parent.newChild(None, 'description', description)
        except TypeError:
            print "TypeError in description"

    def article_to_xml(self, xml_article, rawdog, config, article):
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

    def write_rss(self, rawdog, config, articles):
        doc = libxml2.newDoc("1.0")

        rss = doc.newChild(None, 'rss', None)
        rss.setProp('version', "2.0")
        rss.setProp('xmlns:dc', "http://purl.org/dc/elements/1.1/")
        rss.setProp('xmlns:atom', 'http://www.w3.org/2005/Atom')

        channel = rss.newChild(None, 'channel', None)
        channel.newChild(None, 'title', "Planet KDE")
        channel.newChild(None, 'link', "http://planetKDE.org/")
        channel.newChild(None, 'language', "en")
        channel.newChild(None, 'description', "Planet KDE - http://planetKDE.org/")

        atom_link = channel.newChild(None, 'atom:link', None)
        atom_link.setProp('href', 'http://planetKDE.org/rss20.xml')
        atom_link.setProp('rel', 'self')
        atom_link.setProp('type', 'application/rss+xml')

        for article in articles:
            if article.date is not None:
                xml_article = channel.newChild(None, 'item', None)
                self.article_to_xml(xml_article, rawdog, config, article)

        doc.saveFormatFile(self.options["outputxml"], 1)
        doc.freeDoc()

    def write_foaf(self, rawdog, config):
        doc = libxml2.newDoc("1.0")

        xml = doc.newChild(None, 'rdf:RDF', None)
        xml.setProp('xmlns:rdf', "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        xml.setProp('xmlns:rdfs', "http://www.w3.org/2000/01/rdf-schema#")
        xml.setProp('xmlns:foaf', "http://xmlns.com/foaf/0.1/")
        xml.setProp('xmlns:rss', "http://purl.org/rss/1.0/")
        xml.setProp('xmlns:dc', "http://purl.org/dc/elements/1.1/")

        group = xml.newChild(None, 'foaf:Group', None)
        group.newChild(None, 'foaf:name', "Planet KDE")
        group.newChild(None, 'foaf:homepage', "http://planet.kde.org/")

        seeAlso = group.newChild(None, 'rdfs:seeAlso', None)
        seeAlso.setProp('rdf:resource', '')

        for feed in config["feedslist"]:
            member = group.newChild(None, 'foaf:member', None)

            agent = member.newChild(None, 'foaf:Agent', None)
            agent.newChild(None, 'foaf:name', feed[2]['define_name'])
            weblog = agent.newChild(None, 'foaf:weblog', None)
            document = weblog.newChild(None, 'foaf:Document', None)
            document.setProp('rdf:about', feed[0])
            seealso = document.newChild(None, 'rdfs:seeAlso', None)
            channel = seealso.newChild(None, 'rss:channel', None)
            channel.setProp('rdf:about', '')

        doc.saveFormatFile(self.options["outputfoaf"], 1)
        doc.freeDoc()

    def write_opml(self, rawdog, config):
        doc = libxml2.newDoc("1.0")

        xml = doc.newChild(None, 'opml', None)
        xml.setProp('version', "1.1")

        head = xml.newChild(None, 'head', None)
        head.newChild(None, 'title', "Planet KDE")
        head.newChild(None, 'dateCreated', strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + " +0000")
        head.newChild(None, 'dateModified', strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + " +0000")
        head.newChild(None, 'ownerName', "Jonathan Riddell")
        head.newChild(None, 'ownerEmail', "")

        body = xml.newChild(None, 'body', None)
        for feed in config["feedslist"]:
            outline = body.newChild(None, 'outline', None)
            outline.setProp('text', feed[2]['define_name'])
            outline.setProp('xmlUrl', feed[0])

        doc.saveFormatFile(self.options["outputopml"], 1)
        doc.freeDoc()

    def output_write(self, rawdog, config, articles):
        self.write_rss(rawdog, config, articles)
        self.write_foaf(rawdog, config)
        self.write_opml(rawdog, config)

        return True

rss_feed = RSS_Feed()
rawdoglib.plugins.attach_hook("config_option", rss_feed.config_option)
rawdoglib.plugins.attach_hook("output_write", rss_feed.output_write)

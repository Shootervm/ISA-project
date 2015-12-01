#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from isaCommon import log
from isaOther import download_file
from isaTorrent import get_peers_for_torrent
import re
import xml.etree.ElementTree as XML

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def torrent_from_rss(url):
    # rss_xml = xml.parse('movies_announce.xml').getroot()
    xml_file = download_file(url, 'movies_announce.xml')
    torrent_from_xml_string(xml_file)


def torrent_from_xml_string(xml_string):
    torrent_from_xml(XML.fromstring(xml_string))


def torrent_from_xml_file(xml_file):
    torrent_from_xml(XML.parse(xml_file))


def torrent_from_xml(rss_xml):
    url = rss_xml.find("./channel/item/enclosure").attrib['url']
    fname = get_fname(rss_xml.find("./channel/item"))

    get_peers_for_torrent(download_file(url, fname))

    with open('movies_announce_list.txt', 'w') as f:
        f.write(generate_txt(rss_xml))
        log('movies_announce_list.txt has been created', 3)


def generate_txt(rss_xml):
    log('Generating movies_announce_list.txt file', 3)
    text = txt_append(rss_xml, './channel/title')
    text += txt_append(rss_xml, './channel/link')
    text += txt_append(rss_xml, './channel/description') + '\n'

    for item_xml in rss_xml.findall('./channel/item'):
        text += '\n'
        text += txt_append(item_xml, './title')
        text += txt_append(item_xml, './category')
        text += txt_append(item_xml, './author')
        text += txt_append(item_xml, './link')
        text += txt_append(item_xml, './pubDate')

        # prints elements that are at namespace
        for ns_item in item_xml.findall('./'):
            if re.search(r'\{.*\}infoHash', ns_item.tag):
                text += 'torrent:infoHash: ' + ns_item.text + '\n'
            elif re.search(r'\{.*\}fileName', ns_item.tag):
                text += 'torrent:fileName: ' + ns_item.text + '\n'

    return text


def txt_append(elm, tag) -> str:
    # create line to txt file tag: text
    xml_elm = elm.find(tag)
    if xml_elm is None:
        return tag[2:] + ': \n'
    return xml_elm.tag + ': ' + xml_elm.text + '\n'


def get_fname(xml_torrent) -> str:
    # parse name spaced file name
    for ns_item in xml_torrent.findall('./'):
        if re.search(r'\{.*\}fileName', ns_item.tag):
            return ns_item.text
    return ""

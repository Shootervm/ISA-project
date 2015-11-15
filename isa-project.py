#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

from pprint import pprint  # only for debug and test reasons, to pretty print objects and lists
from urllib import request
import os
import shutil
import sys
import gzip
import bencodepy
import hashlib

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def log(message, out=sys.stderr):
    print("[  Log  ] " + message + "\n", file=out)


def error(message, code=1, out=sys.stderr):
    print("[ Error ] " + message + "\n", file=out)
    exit(code)


def download_torrent(url):
    fname = os.getcwd() + '/' + url.split('title=')[-1] + '.torrent'
    log('Downloading >> ' + fname)

    try:
        get_request = request.Request(url, method='GET',
                                      headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
                                               'Accept-Charset': 'utf-8', 'Accept-Language': '*',
                                               'Connection': '*'})
        response = request.urlopen(get_request)

        if response.getcode() is not 200:
            error("response from server was not OK, HTTP error code [ " + response.getcode() + "]", 2)

        with open(fname, 'wb') as f:
            shutil.copyfileobj(response, f)

        # server response can be gzipped, this will decode the response so torrent will can be parsed
        if response.getheader('Content-Encoding') == 'gzip':
            log("Decompressing response")
            with open(fname, 'rb') as f:
                torrent = gzip.decompress(f.read())

            with open(fname, 'wb') as f:
                f.write(torrent)
        else:
            log("File should not be compressed according to response header")
            torrent = open_torrent(fname)

        return torrent

    except Exception as e:
        error('Exception happened\n\n' + str(e), 3)


def open_torrent(name):
    with open(name, 'rb') as f:
        return f.read()


def parse_torrent(torrent):
    # Decoded torrent_metadata object contains b'value' as binary data, that is why we need use it explicitly sometimes,
    # otherwise it wont match the values

    torrent_metadata = bencodepy.decode(torrent)

    http_trackers = []

    # if 'announce-list' keyword is missing in list, there is only one tracker for this torrent available
    # and therefor 'announce' will be used to connect to the torrent tracker
    if b'announce-list' in torrent_metadata:
        log("announce-list keyword is present, there are more possible trackers")
        usable_trackers(torrent_metadata[b'announce-list'], http_trackers)
    else:
        log("announce-list keyword is NOT present in dictionary, only one choice for tracker")
        # here will be value under keyword announce used as only tracker
        usable_trackers(torrent_metadata[b'announce'], http_trackers)

    pprint(http_trackers)

    info_hash = get_info_hash(torrent_metadata[b'info'])
    peer_id = "PY3-ISA-project-2015"

    pprint(info_hash)
    pprint(peer_id)

def usable_trackers(tracker, http_trackers):
    # TODO: will be called f.e. split_trackers to http and udp ones and create something like {"http": [], "udp": []}
    # Due to extend of standard list of backups can be passed as single tracker, this will check them all one by one
    # to see if there is any of http ones
    if isinstance(tracker, list):
        # Iterate through the all backups of the tracker or through the all trackers in the list, if more than one
        # tracker is passed (announce-list was present in torrent file metadata)
        for backup in tracker:
            usable_trackers(backup, http_trackers)
    else:
        if tracker[:4] == b'http':
            http_trackers.append(tracker.decode("utf-8"))


def get_info_hash(metadata):
    # info metadata are again bencoded and sha1 hash is created from them
    return hashlib.sha1(bencodepy.encode(metadata)).hexdigest()


def start():
    torrent = download_torrent("http://torcache.net/torrent/3F19B149F53A50E14FC0B79926A391896EABAB6F.torrent?title=[kat.cr]ubuntu.15.10.desktop.64.bit")
    # torrent = open_torrent('test.torrent')

    parse_torrent(torrent)




if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        log('Script will be terminated!')
        exit(0)
#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

from pprint import pprint  # only for debug and test reasons, to pretty print objects and lists
from urllib import request
from urllib.parse import urlencode
import os
import shutil
import sys
import gzip
import bencodepy
import hashlib
import struct

__author__ = 'xmasek15@stud.fit.vutbr.cz'


class Torrent:
    """Simple class that will represent torrent file and methods over it"""

    def __init__(self, file_name):
        self.file_name = file_name


def log(message, out=sys.stderr):
    print("[  Log  ] " + message + "\n", file=out)


def error(message, code=1, err="", out=sys.stderr):
    if err == 'http':
        print("[ Error ] response from server was not OK, HTTP error code [ " + message + "]" + "\n", file=out)
        exit(code)
    else:
        print("[ Error ] " + message + "\n", file=out)
        exit(code)


def download_torrent(url):
    fname = os.getcwd() + '/' + url.split('title=')[-1] + '.torrent'
    log('Downloading >> ' + fname)

    try:
        get_request = request.Request(url, method='GET', headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
                                                                  'Accept-Charset': 'utf-8', 'Accept-Language': '*',
                                                                  'Connection': '*'})
        response = request.urlopen(get_request)

        if response.getcode() is not 200:
            error(response.getcode(), 2, 'http')

        with open(fname, 'wb') as f:
            shutil.copyfileobj(response, f)

        # server response can be gzipped, this will decode the response so torrent will can be parsed
        return open_torrent(fname, response.getheader('Content-Encoding') == 'gzip')

    except Exception as e:
        error('Exception happened\n\n' + str(e), 3)


def open_torrent(name, gzipped=False):
    if gzipped:
        return open_gzipped_file(name)
    else:
        log("File should not be compressed according to response header")
        return open_standard_file(name)


def open_standard_file(name):
    with open(name, 'rb') as f:
        return f.read()


def open_gzipped_file(name):
    log("Decompressing response")
    with open(name, 'rb') as f:
        torrent = gzip.decompress(f.read())
    with open(name, 'wb') as f:
        f.write(torrent)
    return torrent


def parse_torrent(torrent):
    # Decoded torrent_metadata object contains b'value' as binary data, that is why we need use it explicitly sometimes,
    # otherwise it wont match the values
    torrent_data = {'metadata': bencodepy.decode(torrent), 'trackers': {'http': [], 'udp': []}, 'info_hash': '',
                    'peer_id': "PY3-ISA-project-2015"}

    # if 'announce-list' keyword is missing in list, there is only one tracker for this torrent available
    # and therefor 'announce' will be used to connect to the torrent tracker
    if b'announce-list' in torrent_data['metadata']:
        log("announce-list keyword is present, there are more possible trackers")
        usable_trackers(torrent_data['metadata'][b'announce-list'], torrent_data['trackers'])
    else:
        log("announce-list keyword is NOT present in dictionary, only one choice for tracker")
        # here will be value under keyword announce used as only tracker
        usable_trackers(torrent_data['metadata'][b'announce'], torrent_data['trackers'])

    torrent_data['info_hash'] = get_info_hash(torrent_data['metadata'][b'info'])

    return torrent_data


def usable_trackers(tracker, trackers):
    # Due to extend of standard list of backups can be passed as single tracker, this will check them all one by one
    # to see if there is any of http ones
    if isinstance(tracker, list):
        # Iterate through the all backups of the tracker or through the all trackers in the list, if more than one
        # tracker is passed (announce-list was present in torrent file metadata)
        for backup in tracker:
            usable_trackers(backup, trackers)
    else:
        if tracker[:4] == b'http':
            trackers['http'].append(tracker.decode("utf-8"))
        elif tracker[:3] == b'udp':
            trackers['udp'].append(tracker.decode("utf-8"))
        else:
            log("tracker is not http or upd ( " + tracker + " )")


def get_info_hash(metadata):
    # info metadata are again bencoded and sha1 hash is created from them
    return hashlib.sha1(bencodepy.encode(metadata)).digest()


def connect_to_tracker(announce, torrent_data):
    announce = torrent_data['trackers']['http'][2]

    url = announce + create_tracker_request(torrent_data)
    pprint(url)

    fname = "test_connect.get"
    try:
        get_request = request.Request(url, method='GET', headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
                                                                  'Accept-Charset': 'utf-8', 'Connection': '*',
                                                                  'Accept': 'application/x-bittorrent'})
        response = request.urlopen(get_request)

        if response.getcode() is not 200:
            error(response.getcode(), 3, 'http')

        with open(fname, 'wb') as f:
            shutil.copyfileobj(response, f)

        # server response can be gzipped, this will decode the response so torrent will can be parsed
        return open_torrent(fname, response.getheader('Content-Encoding') == 'gzip')

    except Exception as e:
        error('Exception happened\n\n' + str(e), 3)


def create_tracker_request(params):
    return "?%s" % urlencode({'uploaded': 0, 'downloaded': 0, 'left': 1000, 'compact': 1, 'port': 6886,
                              'info_hash': params['info_hash'], 'peer_id': params['peer_id']})


def get_peers_for_torrent(torrent):
    torrent_data = parse_torrent(torrent)
    # announce = torrent_data['trackers']['http'][2]

    for announce in torrent_data['trackers']['http']:
        print(get_peers_from_tracker(announce, torrent_data))


def get_peers_from_tracker(announce, torrent_data):
    response = connect_to_tracker(announce, torrent_data)
    pprint(response)

    # response from tracker is bencoded and binary representation of peers addresses will be parsed to readable form
    decoded = bencodepy.decode(response)
    bin_peers = decoded[b'peers']
    peers = ""
    # bin peers data is field of bytes, where each 6 bytes represent one peer
    for i in range(0, len(bin_peers), 6):
        peers += parse_bin_peer(bin_peers[i:i + 6]) + "\n"

    return peers


def parse_bin_peer(bin_peer):
    # will return a string containing first four bytes of byte peer formatted as IP address
    # and second two as unsigned integer port for big endian network conversion
    return "%d.%d.%d.%d:%d" % (int(bin_peer[0]), int(bin_peer[1]), int(bin_peer[2]), int(bin_peer[3]),
                               struct.unpack(">H", bin_peer[4:6])[0])  # dereference of returned tuple first item


def start():
    # torrent = download_torrent("http://torcache.net/torrent/3F19B149F53A50E14FC0B79926A391896EABAB6F.torrent?title=[kat.cr]ubuntu.15.10.desktop.64.bit")

    torrent = open_torrent('/home/shooter/PROJECTS/SCHOOL/ISA-project/[kat.cr]ubuntu.15.10.desktop.64.bit.torrent')

    peers_list = get_peers_for_torrent(torrent)
    print(peers_list)


if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        log('Script will be terminated!')
        exit(0)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint  # only for debug and test reasons, to pretty print objects and lists
from urllib import request
from isaCommon import log, error
from isaConnector import connect_to_http_tracker, connect_to_udp_tracker
import isaCommon
import os
import shutil
import gzip
import bencodepy
import hashlib
import struct

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def download_torrent(url):
    fname = os.getcwd() + '/' + url.split('title=')[-1] + '.torrent'
    log('Downloading >> ' + fname, 1)

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


def open_torrent(name, gzipped=False) -> str:
    """Function will open and read the data of the torrent file, if needed it will also gzip decode it

    :param str name: file name of the torrent to open and read
    :param bool gzipped: signalize if file is gzipped or not (default is False)
    :return: data of the opened torrent
    """
    if gzipped:
        return open_gzipped_file(name)
    else:
        log("File should not be compressed according to response header", 2)
        return open_standard_file(name)


def open_standard_file(name) -> bytes:
    """Function to read standard file

    :param str name: file name to open and read
    :return: data of the opened file
    """
    with open(name, 'rb') as f:
        return f.read()


def open_gzipped_file(name) -> bytes:
    """Function to read gzipped standard file

    :param str name: file name to open and read
    :return: data of the opened and decoded file
    """
    log("Decompressing response", 2)
    with open(name, 'rb') as f:
        torrent = gzip.decompress(f.read())
    with open(name, 'wb') as f:
        f.write(torrent)
    return torrent


def parse_torrent(torrent) -> dict:
    # Decoded torrent_metadata object contains b'value' as binary data, that is why we need use it explicitly sometimes,
    # otherwise it wont match the values
    # Also this contains additional items that will be used for connection to announce
    torrent_data = {'metadata': bencodepy.decode(torrent), 'trackers': {'http': [], 'udp': []}, 'info_hash': '',
                    'hex_info_hash': '', 'peer_id': "PY3-ISA-project-2015",
                    'uploaded': 0, 'downloaded': 0, 'left': 1000, 'compact': 1, 'port': 6886, 'numwant': -1,
                    }

    # if 'announce-list' keyword is missing in list, there is only one tracker for this torrent available
    # and therefor 'announce' will be used to connect to the torrent tracker
    if b'announce-list' in torrent_data['metadata']:
        log("announce-list keyword is present, there are more possible trackers", 2)
        split_trackers(torrent_data['metadata'][b'announce-list'], torrent_data['trackers'])
    else:
        log("announce-list keyword is NOT present in dictionary, only one choice for tracker", 2)
        # here will be value under keyword announce used as only tracker
        split_trackers(torrent_data['metadata'][b'announce'], torrent_data['trackers'])

    torrent_data['info_hash'] = get_info_hash(torrent_data['metadata'][b'info'])
    torrent_data['hex_info_hash'] = get_info_hash(torrent_data['metadata'][b'info'], True)

    return torrent_data


def split_trackers(tracker, trackers):
    # Due to extend of standard list of backups can be passed as single tracker, this will check them all one by one
    # to see if there is any of http ones
    if isinstance(tracker, list):
        # Iterate through the all backups of the tracker or through the all trackers in the list, if more than one
        # tracker is passed (announce-list was present in torrent file metadata)
        for backup in tracker:
            split_trackers(backup, trackers)
    else:
        if tracker[:4] == b'http':
            trackers['http'].append(tracker.decode("utf-8"))
        elif tracker[:3] == b'udp':
            trackers['udp'].append(tracker.decode("utf-8"))
        else:
            log("tracker is not http or upd ( " + tracker + " )", 3)


def get_info_hash(metadata, hex_hash=False) -> str:
    # info metadata are again bencoded and sha1 hash is created from them
    if hex_hash:
        return hashlib.sha1(bencodepy.encode(metadata)).hexdigest()
    else:
        return hashlib.sha1(bencodepy.encode(metadata)).digest()


def get_peers_for_torrent(torrent):
    torrent_data = parse_torrent(torrent)
    # announce = torrent_data['trackers']['http'][2]
    peers = []

    if not torrent_data['trackers']['http']:
        log('List of HTTP trackers is empty', 0)  # TODO: return or end script

    for announce in torrent_data['trackers']['http']:
        log("Getting peers for announce %s" % announce, 1)
        peers.extend(get_peers_from_tracker(announce, torrent_data))

    peers.extend(get_peers_from_tracker("", torrent_data, http=False))  # should be get_peers_from_tracker(announce, torrent_data)

    write_peers_to_file(torrent_data['hex_info_hash'], peers)


def get_peers_from_tracker(announce, torrent_data, http=True) -> list:
    response = connect_to_http_tracker(announce, torrent_data) if http else connect_to_udp_tracker(
        torrent_data['trackers']['udp'][0], torrent_data)
    if response == b'':
        log('Response of tracker was empty', 2)
        return []  # if error has occurred empty list of peers will be returned

    # response from tracker is bencoded binary representation of peers addresses will be parsed to readable form
    decoded = bencodepy.decode(response)

    if not decoded:
        log("Decoded response is empty", 1)
        return []
    elif b'peers' not in decoded:
        log("Decoded response has no peers data in it", 1)
        return []

    peers = []
    bin_peers = decoded[b'peers']
    # bin peers data is field of bytes, where each 6 bytes represent one peer
    # for each peer will be appended to peers list
    for i in range(0, len(bin_peers), 6):
        peers.append(parse_bin_peer(bin_peers[i:i + 6]))

    return peers


def parse_bin_peer(bin_peer) -> str:
    """Function to create readable IP address and port string of the peer

    Args:
        bin_peer (bytes): six byte representation of peer binary data

    Returns:
        str: IP address string of the peer
    """
    return "%d.%d.%d.%d:%d" % (int(bin_peer[0]), int(bin_peer[1]), int(bin_peer[2]), int(bin_peer[3]),
                               struct.unpack(">H", bin_peer[4:6])[0])  # dereference of returned tuple first item


def write_peers_to_file(name, peers):
    """Function to read standard file

    Args:
        name (str): file name to write to
        peers (list): list of peers to write
    """
    with open(name + ".peerlist", 'w') as f:
        for peer in peers:
            f.write(peer + "\n")


def start():
    # url = "http://torcache.net/torrent/3F19B149F53A50E14FC0B79926A391896EABAB6F.torrent?title=[kat.cr]ubuntu.15.10.desktop.64.bit"
    # torrent = download_torrent(url)
    torrent = open_torrent('/home/shooter/PROJECTS/SCHOOL/ISA-project/[kat.cr]ubuntu.15.10.desktop.64.bit.torrent')

    get_peers_for_torrent(torrent)


if __name__ == '__main__':
    # max log deep is 3, if you choose 3 or more ALL LOGs WILL BE DISPLAYED
    # if -1 there will be NO LOGs at all, and 0 is displaying only non breaking error logs
    isaCommon.SHOW_FLAG = 5

    try:
        start()
    except KeyboardInterrupt:
        error('Script will be terminated!', 0)
        exit(0)

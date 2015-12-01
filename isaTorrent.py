#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint
from isaCommon import log, get_udp_transaction_id
from isaConnector import connect_to_http_tracker, connect_to_udp_tracker
import hashlib
import struct
# Is imported as whole module because of setting values to the script environment global variables located in it
import isaCommon

try:
    import bencodepy
except ImportError:
    from bencodepyFolder import bencodepy

__author__ = 'xmasek15@stud.fit.vutbr.cz'


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

    # Get peers for trackers
    if isaCommon.params.tracker_annonce_url:
        announce = isaCommon.params.tracker_annonce_url
        log("Used only announce %s" % announce, 1)
        pprint(announce)
        if announce[:4] == 'http':
            log("Getting peers for announce %s" % announce, 1)
            peers.extend(get_peers_from_tracker(announce, torrent_data))
        elif announce[:3] == 'udp':
            log("Getting peers for announce %s" % announce, 1)
            peers.extend(get_peers_from_tracker(announce, torrent_data, http=False))
    else:
        for announce in torrent_data['trackers']['http']:
            log("Getting peers for announce %s" % announce, 1)
            peers.extend(get_peers_from_tracker(announce, torrent_data))
        for announce in torrent_data['trackers']['udp']:
            log("Getting peers for announce %s" % announce, 1)
            peers.extend(get_peers_from_tracker(announce, torrent_data, http=False))

    write_peers_to_file(torrent_data['hex_info_hash'], peers)


def get_peers_from_tracker(announce, torrent_data, http=True) -> list:
    if http:
        response = connect_to_http_tracker(announce, torrent_data)
    else:
        transaction_id = get_udp_transaction_id()  # randomized transaction ID for UDP
        response = connect_to_udp_tracker(announce, torrent_data, transaction_id)

    if response == b'':
        log('Response of tracker was empty', 2)
        return []  # if error has occurred empty list of peers will be returned

    if http:
        # response from tracker is bencoded binary representation of peers addresses will be parsed to readable form
        decoded = bencodepy.decode(response)
        if not decoded:
            log("Decoded response is empty", 1)
            return []
        elif b'peers' not in decoded:
            log("Decoded response has no peers data in it", 1)
            return []
        bin_peers = decoded[b'peers']
    else:
        bin_peers = parse_udp_announce_response(response, transaction_id)

    log("There should be %u peers" % (len(bin_peers) / 6), 1)
    peers = []

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
                               struct.unpack("!H", bin_peer[4:6])[0])  # dereference of returned tuple first item


def write_peers_to_file(name, peers):
    """Function to read standard file

    Args:
        name (str): file name to write to
        peers (list): list of peers to write
    """
    with open(name + ".peerlist", 'w') as f:
        for peer in peers:
            f.write(peer + "\n")

    log("Peers have been written to file %s.peerlist" % name, 1)


def parse_udp_announce_response(response, transaction_id) -> bytes:
    # Handle the errors of udp announce response
    if len(response) < 20:  # constant 20 represents min byte length that is required only for metadata without peers
        log("Too short response length %s, returning empty response" % len(response), 0)
        return b''

    log("Response length is %s" % len(response), 1)

    action = struct.unpack_from("!I", response)[0]
    if action != 0x1:
        log("Received wrong action number %d, returning empty response" % action, 0)
        return b''

    received_transaction_id = struct.unpack_from("!I", response, 4)[0]  # next 4 bytes is transaction id
    if received_transaction_id != transaction_id:
        log("Transaction ID is wrong. Expected %s, received %s, returning empty response"
            % (transaction_id, received_transaction_id), 0)
        return b''

    log("Reading Response", 3)
    meta = dict()
    offset = 8  # Action and Transaction ID has been at first 8 bytes, that is why offset 8 is needed
    meta['interval'], meta['leeches'], meta['seeds'] = struct.unpack_from("!iii", response, offset)
    offset += 12  # three integers by 4 bytes
    log("Interval = %d, Leeches = %d, Seeds = %d" % (meta['interval'], meta['leeches'], meta['seeds']), 3)

    log("Actual peer data in response are %s" % response[offset:], 3)
    return response[offset:]  # all the rest data in response are peers coded as 6 byte entities

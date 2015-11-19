#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint  # only for debug and test reasons, to pretty print objects and lists
from isaTorrent import get_peers_for_torrent, open_torrent, download_torrent
from isaCommon import log
import isaCommon

__author__ = 'xmasek15@stud.fit.vutbr.cz'


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
        log('Script will be terminated!', 0)
        exit(0)

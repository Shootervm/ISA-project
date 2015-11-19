#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint  # only for debug and test reasons, to pretty print objects and lists
from isaTorrent import get_peers_for_torrent, open_torrent
from isaCommon import log, get_parameters
# Is imported as whole module because of setting values to the script environment global variables located in it
import isaCommon

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def start():
    log("Starting ./antipirat python3 script", 1)
    get_parameters()  # Will get, parse and validate script parameters

    if isaCommon.params.torrent_file:
        get_peers_for_torrent(open_torrent(isaCommon.params.torrent_file))
    elif isaCommon.params.rss:
        pass
    elif isaCommon.params.input_announcement:
        pass


if __name__ == '__main__':

    # Script environment setup
    # if -1 there will be NO LOGs at all, and 0 is displaying only non breaking error logs
    isaCommon.SHOW_FLAG = 5  # max log deep is 3, if you choose 3 or more ALL LOGs WILL BE DISPLAYED

    # set connection timeout to specific value in seconds (None for no timeout), default is 10 seconds
    isaCommon.TIMEOUT = 1
    # when testing best values for timeout, more than 10 seemed to have no effect on getting response from not
    #  responding trackers, most of them didn't responded even after the 50 and more seconds timeout

    try:
        start()
    except KeyboardInterrupt:
        log('Script will be terminated!', 0)
        exit(0)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from isaTorrent import get_peers_for_torrent
from isaCommon import log, get_parameters, error
from isaOther import open_file
from isaFeed import torrent_from_rss, torrent_from_xml_file
# Is imported as whole module because of setting values to the script environment global variables located in it
import isaCommon
import sys

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def welcome():
    log("Antipirat python3 script has started", 0, not_err=True)
    if isaCommon.SHOW_FLAG < 1:
        message = "\nif you want to see more logs, be sure to higher the logs level\n" \
                  "(set if isaCommon.SHOW_FLAG to more than 0)"
    else:
        message = "\nif you want to see less logs, be sure to lower the logs level\n" \
                  "(set if isaCommon.SHOW_FLAG to 0 for only non breaking error logs and -1 to no logs at all)"

    log("Logging is set to %u level, %s" % (isaCommon.SHOW_FLAG, message), 0, not_err=True)
    log("Timeout of the connection is set to %u seconds" % isaCommon.TIMEOUT, 1)


def start():
    if len(sys.argv) == 1:
        error("No parameters passed to the script, use --help option to see list of supported ones", 1)

    welcome()  # welcome message

    get_parameters()  # Will get, parse and validate script parameters

    if isaCommon.params.tracker_annonce_url:
        log("Default announce is passed to script, it will the only one used for peer gathering", 1)

    if isaCommon.params.torrent_file:
        get_peers_for_torrent(open_file(isaCommon.params.torrent_file))
    elif isaCommon.params.rss:
        torrent_from_rss(isaCommon.params.rss)
    elif isaCommon.params.input_announcement:
        torrent_from_xml_file(isaCommon.params.input_announcement)


if __name__ == '__main__':

    # Script environment setup
    # if -1 there will be NO LOGs at all, and 0 is displaying only non breaking error logs
    isaCommon.SHOW_FLAG = 1  # max log deep is 3, if you choose 3 or more ALL LOGs WILL BE DISPLAYED

    # set connection timeout to specific value in seconds (None for no timeout), default is 10 seconds
    isaCommon.TIMEOUT = 3
    # when testing best values for timeout were 5-10 and circa 7 seconds, more than 10 seemed to have no effect on
    # getting response from not responding trackers, most of them didn't responded even after the 50 seconds and more

    try:
        start()
    except KeyboardInterrupt:
        log('Script will be terminated!', 0)
        exit(0)

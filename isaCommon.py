#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pprint
import sys
import random
import argparse

__author__ = 'xmasek15@stud.fit.vutbr.cz'

# Script parameters are stored in this variable
params = None  # is empty before actual params are stored

# Default flag, means only logs clarified as nonfatal error are shown
SHOW_FLAG = 0  # set to -1 for no logs, 0 is displaying only non breaking error logs, higher number means more logs

# Variable used as socket timeout
TIMEOUT = 7  # default is set to 7 seconds, use None for no timeout

# Default log and error function output file (descriptor)
output = sys.stderr


def log(message, show=2, out=output):
    # SHOW_FLAG will determine which logs will be printed out
    if show <= SHOW_FLAG:
        print("[  Log  ] " + message + "\n", file=out)


def error(message, code=1, err="", out=sys.stderr):
    if err == 'http':
        print("[ Error ] response from server was not OK, HTTP error code [ " + message + "]" + "\n", file=out)
        exit(code)
    else:
        print("[ Error ] " + message + "\n", file=out)
        exit(code)


def get_udp_transaction_id():
    return int(random.randrange(0, 255))


def check_parameters(params):
    # Function will check parameters of the script
    # there is at least one required parameter but only one can be present at the same time,
    # if there are more or none of required script will be terminated with error message and error code
    count = 0
    if params.rss:
        count += 1
    if params.input_announcement:
        count += 1
    if params.torrent_file:
        count += 1
    if count > 1:
        error("Wrong combination of script parameters", 5)
    elif count == 0:
        error("None of the required script parameters are present", 4)


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rss", type=str, default=None,
                        help="Passes URL address of RSS feed to script and feed will be downloaded")
    parser.add_argument("-i", "--input-announcement", type=str, default=None,
                        help="Passes RSS feed that is already downloaded")
    parser.add_argument("-t", "--torrent-file", type=str, default=None, help="Already downloaded torrent file")
    parser.add_argument("-a", "--tracker-annonce-url", "--tracker-announce-url", type=str, default=None,
                        help="Default announcement, all other will be overwritten")

    global params

    params = parser.parse_args()

    log("Server parameters : %s" % params, 2)

    check_parameters(params)  # Will perform check of the script parameters, if error occurs, script will be terminated

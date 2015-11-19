#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import random

__author__ = 'xmasek15@stud.fit.vutbr.cz'

# Default flag, means only logs clarified as nonfatal error are shown
SHOW_FLAG = 0  # set to -1 for no logs, 0 is displaying only non breaking error logs, higher number means more logs

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

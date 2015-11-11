#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

__author__ = 'xmasek15'

import os
from urllib import request
import shutil
import sys
import gzip


def log(message, out=sys.stderr):
    print("[  Log  ] " + message + "\n", file=out)


def error(message, code=1, out=sys.stderr):
    print("[ Error ] " + message + "\n", file=out)
    exit(code)


def download_torrent(url, fname):
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

        if response.getheader('Content-Encoding') == 'gzip':
            log("Decompressing response")
            with open(fname, 'rb') as f:
                unzipped = gzip.decompress(f.read())

            with open(fname, 'wb') as f:
                f.write(unzipped)
        else:
            log("File should not be compressed according to response header")

    except Exception as e:
        error('Exception happend\n\n' + str(e), 3)


def start():
    url = "http://torcache.net/torrent/3F19B149F53A50E14FC0B79926A391896EABAB6F.torrent?title=[kat.cr]ubuntu.15.10.desktop.64.bit"
    fname = os.getcwd() + '/' + url.split('title=')[-1] + '.torrent'

    log('Downloading >> ' + fname)
    download_torrent(url, fname)
    log('>> Done <<')


if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        log('Script will be terminated!')
        exit(0)

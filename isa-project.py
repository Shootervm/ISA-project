#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

__author__ = 'xmasek15'

import os
from urllib import request
import shutil
import sys
import gzip


def download_torrent(url, fname):
    try:
        get_request = request.Request(url, method='GET',
                                      headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
                                               'Accept-Charset': 'utf-8',
                                               'Accept-Encoding': 'gzip', 'Accept-Language': '*',
                                               'Connection': 'keep-alive'})
        response = request.urlopen(get_request)

    # TODO: momentalne to od gzipovava, treba zistit ci to dostanem v gzipe stale alebo len vdaka tomu ze ho pozadujem

        with open(fname, 'wb') as f:\
            shutil.copyfileobj(response, f)

        with open(fname, 'rb') as f:
            unzipped = gzip.decompress(f.read())

        with open(fname, 'wb') as f:
            f.write(unzipped)

    except Exception as e:
        print('error nastal\n' + str(e))
        sys.exit(99)


def start():
    url = "http://torcache.net/torrent/3F19B149F53A50E14FC0B79926A391896EABAB6F.torrent?title=[kat.cr]ubuntu.15.10.desktop.64.bit"
    fname = os.getcwd() + '/' + url.split('title=')[-1] + '.torrent'

    print('Download >> ' + fname)

    download_torrent(url, fname)

    print('>> Done <<')


if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        print('\nScript will be terminated!')
        exit(0)

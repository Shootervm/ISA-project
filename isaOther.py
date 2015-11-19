#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib import request
from isaCommon import log, error
import os
import shutil
import gzip

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def download_file(url, fname=""):
    if not fname:
        fname = os.getcwd() + '/' + url.split('title=')[-1] + '.torrent'
        if not fname:
            fname = 'torrent.torrent'

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
        return open_file(fname, response.getheader('Content-Encoding') == 'gzip')

    except Exception as e:
        error('Exception happened\n\n' + str(e), 3)


def open_file(name, gzipped=False) -> str:
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from isaCommon import log, error
from urllib.parse import urlencode, urlparse
import socket
import re

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def create_socket(hostname, port):
    log('Creating socket', 2)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        log("Connecting to tracker socket", 2)
        s.connect((hostname, port))
    except socket.gaierror:
        log('Can not translate %s to IP address' % hostname, 1)
        s.close()
        return None  # FIXME: asi nemozem vracat none
    except Exception as e:
        log('Connection to server has failed', 1)
        s.close()
        error('Socket exception happened\n\n' + str(e), 88)

    s.settimeout(None)
    return s  # return opened and connected socket


def connect_to_tracker(announce, torrent_data):
    hostname = urlparse(announce).hostname
    port = urlparse(announce).port

    s = create_socket(hostname, port)
    if s is None:
        log("Returned socket is empty", 2)
        return b''

    headers = "User-Agent: Mozilla/5.0 (X11; Linux x86_64)\r\n" + \
              "Host: " + hostname + ":" + str(port) + "\r\n" + \
              "Accept-Charset: utf-8\r\n" + \
              "Connection: *\r\n" + \
              "Accept: application/x-bittorrent\r\n"

    # Send the GET message
    # GET request is created from announce path part, torrent data part and headers
    send_get_message(s, urlparse(announce).path + create_tracker_request(torrent_data), headers)

    # Receive a response
    response, content_length, is_chunked, encoding = receive_response(s)
    log('Response received', 2)

    if is_chunked:
        log("Starting chunked communication", 3)
        received = chunked_receive(s).decode(encoding)
    elif content_length is not None:
        log("Length of content being received is %s Bytes" % content_length, 3)
        received = receiving(s, content_length)
    else:
        log("communication is NOT chunked and length of content is not specified", 3)
        s = s.makefile(newline='', mode='rb')
        received = s.read()
        log("Length of content is %i Bytes" % len(received), 3)

    log('Closing socket', 2)
    s.close()

    return received


def create_tracker_request(params) -> str:
    return "?%s" % urlencode({'uploaded': 0, 'downloaded': 0, 'left': 1000, 'compact': 1, 'port': 6886,
                              'info_hash': params['info_hash'], 'peer_id': params['peer_id']})


def send_get_message(sock, path, headers):
    message = "GET " + path + " HTTP/1.0\r\n" + headers + "\r\n"
    message = bytes(message, 'utf-8')
    log("Message is %s" % message, 3)  # TODO: this message is messing
    try:
        log('Sending GET message to tracker', 2)
        sock.send(message)
    except Exception as e:
        log('Sending data to server has failed. Exception %s' % e, 0)
        sock.close()


def check_response(response):
    if re.search(r'HTTP/1.[01].*\r\n\r\n', response, flags=re.DOTALL | re.MULTILINE):
        if re.search(r'HTTP/1.[01] 200.*\r\n\r\n', response, flags=re.DOTALL | re.MULTILINE):
            return 200
        elif re.search(r'HTTP/1.[01] 404.*\r\n\r\n', response, flags=re.DOTALL | re.MULTILINE):
            return 404
        else:
            return -1
    else:
        log("response is weird -> %s" % response, 3)
        return None


def receive_response(sock):
    log('Waiting for response', 3)
    response = receive_header(sock)
    log('Response from server: %s' % response)
    response = response.decode('utf-8')

    code = check_response(response)
    if code is None:
        log("Tracker response HTTP error code [ %d ]" % code, 2)
    elif code == 404:
        log("Response from server is Error 404", 0)
    elif code == 200:
        log("Response from server is OK", 2)
    else:
        log("Unknown response from server -> code %s" % code, 2)

    content_length = gef_conntent_length(response)

    is_chunked = is_set_chunk(response)
    if is_chunked:
        log("Communication will be chunked", 2)

    encoding = get_encoding(response)
    log("Encoding of content is: %s" % encoding, 2)
    return response, content_length, is_chunked, encoding


def receive_size(sock):
    request = b''
    while True:
        request += sock.recv(1)
        if len(request) > 2 and request[-2:] == b'\r\n':
            break

    _ret = request
    request = request.decode('utf-8')

    if request[:2] == '\r\n':
        request = request[2:]

    if not re.match(r'[0-9a-f]+\r\n', request):
        return None, _ret

    return int(request, 16), _ret


def gef_conntent_length(response):
    match = re.search(r'Content-Length: [0-9]+', response, flags=re.DOTALL | re.MULTILINE)
    if match:
        return int(response[match.start() + 16:match.end()])
    else:
        return None


def get_encoding(response):
    match = re.search(r'Content-Type: text/html.*charset=.*\r\n', response, flags=re.DOTALL | re.MULTILINE)
    if match:
        match = re.search(r'charset=.*\r\n', response)
        return response[match.start() + 8:match.end() - 2]
    else:
        return 'utf-8'


def chunked_receive(sock):
    all_received = b''
    while True:
        chunk_size, bin_chunk_size = receive_size(sock)
        log('chunk_size: %s' % chunk_size, 3)
        if chunk_size is None:
            sock.close()
            log("Received chunk size was None, returning empty data", 2)
            return b''
        if chunk_size == 0:
            break

        received = receiving(sock, chunk_size)
        all_received += received
        if len(received) != chunk_size:
            sock.close()
            log("Received size is not same as chunk size should be, returning empty data", 2)
            return b''

    return all_received


def receiving(sock, content_length):
    received = b''
    received_length = 0
    while received_length < content_length:
        received += sock.recv(1)
        received_length += 1

    if len(received) != content_length:
        sock.close()
        print(len(received), "   ", content_length)
        print(received)
        error("While receiving, length is not right", 5)

    # log('Received from server: %s' % received, 3)
    return received


def receive_header(sock):
    request = b''
    while True:
        request += sock.recv(1)

        if len(request) > 4 and request[len(request) - 4:] == b'\r\n\r\n':
            break
        if len(request) > 4 and request[len(request) - 4:] == b'\r\n<!':
            return None

    return request


def is_set_chunk(request):
    if re.search(r'((Accept)|(Transfer))-Encoding: .*chunked.*', request, flags=re.DOTALL | re.MULTILINE):
        return True
    else:
        return False

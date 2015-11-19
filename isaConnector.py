#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint  # only for debug and test reasons, to pretty print objects and lists
from isaCommon import log, error, get_udp_transaction_id
from urllib.parse import urlencode, urlparse
import socket
import struct
import re

TIMEOUT = 7  # default is set to 7 seconds, use None for no timeout

__author__ = 'xmasek15@stud.fit.vutbr.cz'


def create_socket(hostname, port, http=True) -> socket:
    if http:
        log('Creating socket', 2)
        # TODO: there probably could be IPv6 socket condition
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.settimeout(TIMEOUT)  # TODO: set and test timeout

    try:
        log("Connecting to tracker socket", 2)
        s.connect((hostname, port))
    except socket.gaierror:
        log('Can not translate %s to IP address' % hostname, 0)
        s.close()
        return None
    except Exception as e:
        log('Connection to server has failed %s' % str(e), 0)
        s.close()
        return None

    return s  # return opened and connected socket, if error happens closed socked is returned


def connect_to_http_tracker(announce, torrent_data):
    hostname = urlparse(announce).hostname
    port = urlparse(announce).port

    s = create_socket(hostname, port, http=True)
    if not isinstance(s, socket.socket):
        log("Returned socket is empty", 2)
        return b''

    headers = "User-Agent: Mozilla/5.0 (X11; Linux x86_64)\r\n" + \
              "Host: " + hostname + ":" + str(port) + "\r\n" + \
              "Accept-Charset: utf-8\r\n" + \
              "Connection: *\r\n" + \
              "Accept: application/x-bittorrent\r\n"

    # Send the GET message
    # GET request is created from announce path part, torrent data part and headers
    send_get_message(s, create_tracker_request(urlparse(announce).path, torrent_data), headers)

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


def create_tracker_request(path, params) -> str:
    return "%s?%s%s" % (urlparse(path).path,
                        urlencode(
                            {'uploaded': params['uploaded'], 'downloaded': params['downloaded'], 'left': params['left'],
                             'compact': params['compact'], 'port': params['port'], 'numwant': params['numwant'],
                             'info_hash': params['info_hash'], 'peer_id': params['peer_id']}),
                        urlparse(path).query)


def send_get_message(sock, path, headers):
    """Function will send http GET message to tracer ip opened in passed socket

    Args:
        sock (object): socket that will be used for connection
    """
    message = "GET " + path + " HTTP/1.0\r\n" + headers + "\r\n"
    message = bytes(message, 'utf-8')
    log("Message is %s" % message, 3)
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

    content_length = get_conntent_length(response)

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


def get_conntent_length(response):
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


def connect_to_udp_tracker(announce, torrent_data, transaction_id):
    hostname = urlparse(announce).hostname
    port = urlparse(announce).port

    s = create_socket(hostname, port, http=False)
    if s is None:
        log("Returned socket is empty", 2)
        return b''

    connection_id = 0x41727101980  # default connection id

    s.sendto(create_udp_connection_request(connection_id, transaction_id), (socket.gethostbyname(hostname), port))

    try:
        con_response = s.recvfrom(2048)[0]
    except socket.timeout:
        log("Socket connection has timed out", 0)
        return b''
    except socket.error as e:
        log("Cannot connect %s" % e, 0)
        s.close()
        return b''
    except Exception as e:
        log('Connection to server has failed %s' % str(e), 0)
        s.close()
        return b''

    connection_id = parse_udp_connection_response(con_response, transaction_id)
    log("New connection ID is %u" % connection_id, 3)

    socket_port = s.getsockname()[1]  # port number on which socket is communicating

    s.sendto(create_udp_announce_request(connection_id, transaction_id, torrent_data, socket_port),
             (socket.gethostbyname(hostname), port))

    try:
        response = s.recvfrom(2048)[0]
    except socket.timeout:
        log("Socket connection has timed out", 0)
        return b''

    return response


def create_udp_connection_request(connection_id, transaction_id):
    # Function will create udp request for getting new connection ID
    request = struct.pack("!Q", connection_id)
    request += struct.pack("!I", 0x0)  # action 0 means asking for new connection ID
    request += struct.pack("!I", transaction_id)
    return request


def create_udp_announce_request(connection_id, transaction_id, torrent_data, port):
    request = struct.pack("!Q", connection_id)  # connection ID
    request += struct.pack("!I", 0x1)  # action (1 represents announce)
    request += struct.pack("!I", transaction_id)  # transaction ID
    request += struct.pack("!20s", torrent_data['info_hash'])  # info_hash of the torrent
    request += struct.pack("!20s", bytes(torrent_data['peer_id'], "utf-8"))  # peer_id
    request += struct.pack("!Q", int(torrent_data['downloaded']))
    request += struct.pack("!Q", int(torrent_data['left']))
    request += struct.pack("!Q", int(torrent_data['uploaded']))
    request += struct.pack("!I", 0x2)  # event 2 should denote start of downloading
    request += struct.pack("!I", 0x0)  # should be 0 (IP)
    request += struct.pack("!I", get_udp_transaction_id())  # client key (have to be unique) randomized
    request += struct.pack("!i", int(torrent_data['numwant']))  # (uint) is set to -1 (default), most peers are returned
    request += struct.pack("!I", port)  # communication port of socket
    return request


def parse_udp_connection_response(response, sent_transaction_id):
    # Handle the errors of udp announce response
    if len(response) < 16:  # constant 16 represents min byte length that is required only for metadata
        log("Too short response length %s, returning empty response" % len(response), 0)
        return b''

    action, res_transaction_id = struct.unpack_from("!II", response)

    if res_transaction_id != sent_transaction_id:
        log("Transaction ID is not same as Connection ID in response, Expected %s and got %s, returning empty response"
            % (sent_transaction_id, res_transaction_id), 0)
        return b''

    if action == 0x0:  # Connection established, getting Connection ID
        return struct.unpack_from("!Q", response, 8)[0]  # unpack 8 bytes, should be the connection_id
    elif action == 0x3:  # Error message in response
        log("Error message in response: { %s }, returning empty response" % struct.unpack_from("!s", response, 8)[0], 0)
        return b''

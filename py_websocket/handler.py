# -*- coding: utf-8 -*-

import re
import struct
import logging
from base64 import b64encode
from hashlib import sha1
from SocketServer import StreamRequestHandler

from py_websocket.op_code import op_code

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.INFO)

class WebSocketHandler(StreamRequestHandler):

    def __init__(self, socket, addr, server):
        self.server = server
        StreamRequestHandler.__init__(self, socket, addr, server)

    def setup(self):
        StreamRequestHandler.setup(self)
        self.keep_alive = True
        self.handshake_done = False
        self.valid_client = False

    def handle(self):
        while self.keep_alive:
            if not self.handshake_done:
                self.handshake()
            elif self.valid_client:
                self.read_message()

    def read_bytes(self, num):
        bytes = self.rfile.read(num)
        return map(ord, bytes)

    def handshake(self):
        message = self.request.recv(20480).decode().strip()
        upgrade = re.search('\nupgrade[\s]*:[\s]*websocket', message.lower())
        if not upgrade:
            self.keep_alive = False
            return
        key = re.search('\n[sS]ec-[wW]eb[sS]ocket-[kK]ey[\s]*:[\s]*(.*)\r\n', message)
        if key:
            key = key.group(1)
        else:
            logger.warning('Client tried to connect but was missing a key')
            self.keep_alive = False
            return
        response = self.make_handshake_response(key)
        self.handshake_done = self.request.send(response.encode())
        self.valid_client = True
        self.server.new_client(self)

    def make_handshake_response(self, key):
        return \
            'HTTP/1.1 101 Switching Protocols\r\n' \
            'Upgrade: websocket\r\n' \
            'Connection: Upgrade\r\n' \
            'Sec-WebSocket-Accept: %s\r\n' \
            '\r\n' % self.calculate_response_key(key)

    def calculate_response_key(self, key):
	    GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
	    hash = sha1(key.encode() + GUID.encode())
	    response_key = b64encode(hash.digest()).strip()
	    return response_key.decode('ASCII')

    def read_message(self):
        try:
            b1, b2 = self.read_bytes(2)
        except ValueError as e:
            b1, b2 = 0, 0

        fin = b1 & op_code.get('FIN')
        opcode = b1 & op_code.get('OPCODE')
        masked = b2 & op_code.get('MASKED')
        playload_len = b2 & op_code.get('PLAYLOAD_LEN')

        if not b1:
            logger.info('Client closed connection.')
            self.keep_alive = False
            return
        # 断开
        if opcode == op_code.get('OPCODE_CLOSE'):
            logger.info('Client asked to close connection.')
            self.keep_alive = False
            return
        # 没有掩码处理
        # print('opcode is %d' % opcode)
        if not masked:
            logger.error('Client must always be masked')
            self.keep_alive = False
            return
        if opcode == op_code.get('OPCODE_CONTINUATION'):
            logger.warn('Continuation frames are not supported.')
            return
        if opcode == op_code.get('OPCODE_BINARY'):
            logger.warn('Binary frames are not supported.')
            return
        elif opcode == op_code.get('OPCODE_TEXT'):
            opcode_handler = self.server.message_received
        elif opcode == op_code.get('OPCODE_PING'):
            opcode_handler = self.server.ping_received
        elif opcode == op_code.get('OPCODE_PONG'):
            logger.warn('pong frames are not supported.')
            return
        else:
            logger.warn("Unknown opcode %#x." + opcode)
            self.keep_alive = False
            return

        if playload_len == 126:
            playload_len = struct.unpack('>H', self.rfile.read(2))[0] # integer
        elif playload_len == 127:
            playload_len = struct.unpack('>Q', self.rfile.read(8))[0] # long

        masks = self.read_bytes(4)
        decoded = ''
        # 对message进行解码
        # print self.read_bytes(playload_len)
        for char in self.read_bytes(playload_len):
            char ^= masks[len(decoded) % 4]
            decoded += chr(char)
        opcode_handler(self, decoded)

    def send_message(self, message, opcode):
        self.send_text(message, op_code.get('OPCODE_TEXT'))

    def send_pong(self, message):
        self.send_text(message, op_code.get('OPCODE_PONG'))

    def send_text(self, message, opcode):
        if isinstance(message, bytes):
            message = decode_UTF8(message)
            if not message:
                logger.error('Can\'t send message, message is not valid UTF-8')
                return False
        elif isinstance(message, str) or isinstance(message, unicode):
            pass
        else:
            logger.error('Can\'t send message, message has to be a string or bytes. Given type is %s' % type(message))
            return
        
        header = bytearray()
        playload = encode_to_UTF8(message)
        playload_len = len(playload)

        if playload_len <= 125:
            header.append(op_code.get('FIN') | opcode)
            header.append(playload_len)

        elif playload_len > 125 and playload_len <= 65535:
            header.append(op_code.get('FIN') | opcode)
            header.append(op_code.get('PLAYLOAD_LEN_EXT16'))
            header.extend(struct.pack('>H', playload_len))

        elif playload_len < 18446744073709551616:
            header.append(op_code.get('FIN') | opcode)
            header.append(op_code.get('PLAYLOAD_LEN_EXT64'))
            header.extend(struct.pack('>Q', playload_len))
    
        else:
            raise Exception('Message is too big. Consider breaking it into chunks.')
            return

        self.request.send(header + playload)

    def finish(self):
        self.server.client_left(self)

def encode_to_UTF8(data):
    try:
        return data.encode('UTF-8')
    except UnicodeEncodeError as e:
        logger.error('Could not encode data to UTF-8 -- %s' % e)
    except Exception as e:
        raise(e)
        return False

def decode_UTF8(data):
    try:
        return data.decode('UTF-8')
    except UnicodeEncodeError as e:
        logger.error('Could not decode data to UTF-8 -- %s' % e)
    except Exception as e:
        raise(e)
        return False
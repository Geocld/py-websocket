# -*- coding: utf-8 -*-

import logging
from SocketServer import TCPServer, ThreadingMixIn

from py_websocket.api import API
from py_websocket.handler import WebSocketHandler

logger = logging.getLogger(__name__)
logging.basicConfig()


class WebsocketServer(ThreadingMixIn, TCPServer, API):

    def __init__(self, port=9001, host='127.0.0.1', loglevel=logging.WARNING):
        logger.setLevel(loglevel)
        self.port = port
        self.id_count = 0
        self.clients = []
        TCPServer.__init__(self, (host, port), WebSocketHandler)

    def new_client(self, handler):
        self.id_count += 1
        client = {
            'id': self.id_count,
            'handler': handler,
            'address': handler.client_address
        }
        self.clients.append(client)
        print("New client connected and was given id %d" % client['id'])

    def client_left(self, handler):
        client = self.handler_to_client(handler)
        if client in self.clients:
	        self.clients.remove(client)
        print client # debug
        # print("Client(%d) disconnected" % client['id'])

    def _uniticast_(self, client, msg):
        client['handler'].send_message(msg)

    def _multicast_(self, msg):
        for client in self.clients:
            self._uniticast_(client, msg)

    def handler_to_client(self, handler):
        for client in self.clients:
            if client['handler'] == handler:
                return client

    def message_received(self, handler, message):
        client = self.handler_to_client(handler)
        print("Client(%d) said: %s" % (client['id'], message))
    
    def ping_received(self, handler, message):
        handler.send_pong(message)

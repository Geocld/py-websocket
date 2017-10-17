# -*- coding: utf-8 -*-

import logging
from SocketServer import TCPServer, ThreadingMixIn

from api import API

logger = logging.getLogger(__name__)
logging.basicConfig()


class WebsocketServer(TCPServer, ThreadingMixIn, API):

    def __init__(self, port=9001, host='127.0.0.1', loglevel=logging.WARNING):
        logger.setLevel(loglevel)
        self.port = port
        TCPServer.__init__(self, (host, port), WebSocketHandler)

class WebSocketHandler:
    
    def __init__(self):
        self.test = True
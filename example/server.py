# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

from py_websocket.application import WebsocketServer

ws = WebsocketServer()
ws.run_forever()

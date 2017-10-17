# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)
logging.basicConfig()


class API:

    def run_forever(self):
        try:
            print('Listening on port %d for client..' % self.port)
            # logger.info('Listening on port %d for client..' % self.port)
            self.serve_forever()
        except keyboardInterrupt:
            self.server_close()
            logger.info('Server terminated')
        except Except as e:
            logger.error(str(e), exc_info = True)
            exit(1)

    def client_left(self, client, server):
        pass

    def message_received(self, client, server, message):
        pass

    def set_fn_message_received(self, fn):
        self.message_received = fn

    def send_message(self, client, msg):
        self._unicast_(client, msg)

    def send_message_to_all(self, msg):
        self._multicast_(msg)

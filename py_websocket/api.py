# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)
logging.basicConfig()


class API:

    def run_forever(self):
        global keyboardInterrupt
        try:
            logger.setLevel(logging.INFO)
            logger.info('Listening on port %d for client..' % self.port)
            self.serve_forever()
        except keyboardInterrupt:
            self.server_close()
            logger.info('Server terminated')
        except Except as e:
            logger.error(str(e), exc_info = True)
            exit(1)

    def send_message(self, client, msg):
        self._unicast_(client, msg)

    def send_message_to_all(self, msg):
        self._multicast_(msg)

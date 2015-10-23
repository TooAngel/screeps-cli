"""Screeps CLI

Usage:
  screeps.py log
"""
import os
import logging

from docopt import docopt
import json
import requests
import websocket
import sys


class ScreepsWSConnection(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def on_message(self, ws, message):
        if (message.startswith('auth ok')):
            ws.send('subscribe user:' + self.user_id + '/console')
            return

        if (message.startswith('time')):
            return

        data = json.loads(message)

        if 'messages' in data[1]:
            if 'log' in data[1]['messages']:
                for line in data[1]['messages']['log']:
                    print line
            return

        print('on_message', message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        ws.send('auth {}'.format(self.token))

    def get_token(self):
        url = 'https://screeps.com/api/auth/signin'
        data = dict(email=self.email, password=self.password)
        response = requests.post(url=url, data=data)
        self.token = response.json()['token']

    def get_user_id(self):
        url = 'https://screeps.com/api/auth/me'
        headers = {'X-Token': self.token, 'X-Username': self.token}
        response = requests.get(url=url, headers=headers)
        self.user_id = response.json()['_id']

    def connect(self):
        url = 'wss://screeps.com/socket/websocket'
        ws = websocket.WebSocketApp(url=url,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close,
                                    on_open=self.on_open)
        ws.run_forever(ping_interval=1)

    def start(self):
        self.get_token()
        self.get_user_id()
        self.connect()


def main():
    logging.basicConfig()
    _ = docopt(__doc__)

    email = os.environ.get('email')
    password = os.environ.get('password')

    if not email or not password:
        sys.exit('Please set email and password as environment variables.')

    swsc = ScreepsWSConnection(email, password)
    swsc.start()

if __name__ == '__main__':
    main()

"""Screeps CLI

Usage:
  screeps.py log [--ptr]
  screeps.py me [--ptr]
  screeps.py download [--dest=<directory>] [--ptr] [--debug]
"""
import json
import logging
import os
import sys

import requests

from docopt import docopt
from screeps.screeps import Connection
from pprint import pprint
import threading


def save(name, data, dest):
    with open('{}/{}.js'.format(dest, name), 'w') as f:
        f.write(data)


def me(email, password, arguments):
    connection = Connection(email, password, arguments['--ptr'])
    pprint(connection.get_me())

def download(email, password, arguments):
    print(arguments)
    dest = arguments.get('--dest')
    if not dest:
        dest = 'dist'

    if not os.path.isdir(dest):
        os.mkdir(dest)

    url = 'https://screeps.com/api/user/code'

    if arguments.get('--ptr'):
        url = 'https://screeps.com/ptr/api/user/code?branch=$activeWorld'

    auth = (email, password)
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    data = response.json()

    if 'error' in data:
        sys.exit(data['error'])

    for module in data['modules']:
        if data['modules'][module]:
            if arguments.get('--debug'):
                print('save {}'.format(module))
            save(module, data['modules'][module], dest)
        else:
            try:
                os.remove('{}/{}.js'.format(dest, module))
            except OSError:
                pass


def sysout(message):
    if message.startswith('time'):
        return

    data = json.loads(message)

    if 'messages' in data[1]:
        if 'log' in data[1]['messages']:
            for line in data[1]['messages']['log']:
                print(line)
        return
    print('on_message', message)

class ReadStdin(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.connection = connection
        self.running = True

    def run(self):
        while self.running:
            line = input()
            self.connection.console(line)

def main():
    logging.basicConfig()
    arguments = docopt(__doc__)

    email = os.environ.get('email')
    password = os.environ.get('password')

    if not email or not password:
        sys.exit('Please set email and password as environment variables.')

    if arguments.get('log'):
        connection = Connection(email, password, arguments['--ptr'])
        read_stdin = ReadStdin(connection)
        try:
            read_stdin.start()
            connection.startWebSocket(sysout)
        except KeyboardInterrupt:
            read_stdin.running = False

    if arguments.get('download'):
        download(email, password, arguments)

    if arguments.get('me'):
        me(email, password, arguments)


if __name__ == '__main__':
    main()

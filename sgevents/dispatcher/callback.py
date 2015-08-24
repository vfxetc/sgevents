import cPickle as pickle
import logging
import os
import subprocess
import sys

import yaml

from ..event import Event
from ..utils import get_func


log = logging.getLogger(__name__)


class Callback(object):
    
    def __init__(self, callback, callback_in_subprocess=True):
        self.callback = callback
        self.callback_in_subprocess = bool(callback_in_subprocess)

        self._callback = None


    def handle_event(self, dispatcher, context, event):

        # TODO: Setup context.

        if not self.callback_in_subprocess:
            # Load it the first time.
            if self._callback is None:
                self._callback = get_func(self.callback)
            self._callback(event)
            return

        environ = os.environ.copy()
        # TODO: Setup dev mode here.

        proc = subprocess.Popen([sys.executable, '-m', 'sgevents.dispatcher.callback'], stdin=subprocess.PIPE, env=environ)
        proc.stdin.write(yaml.dump({
            'callback': self.callback,
            'event': dict(event),
        }))
        proc.stdin.close()

        ret = proc.wait()
        if ret:
            log.error('subprocess for %s returned %s' % (self.callback, ret))



def subprocess_main():

    raw_package = sys.stdin.read()

    package = yaml.load(raw_package)

    callback = get_func(package['callback'])
    event = Event.factory(package['event'])

    callback(event)


if __name__ == '__main__':
    exit(subprocess_main() or 0)

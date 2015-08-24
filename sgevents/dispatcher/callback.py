import cPickle as pickle
import logging
import os
import subprocess
import sys

import yaml

from ..event import Event
from ..utils import get_func, get_func_name, get_command_prefix
from .filter import Filter


log = logging.getLogger(__name__)


class Callback(object):
    
    def __init__(self, callback, name=None, callback_in_subprocess=True, filter=None, args=None, kwargs=None):

        self.name = name or get_func_name(callback)
        self.callback = callback
        self.callback_in_subprocess = bool(callback_in_subprocess)
        self._callback = None
        self.args = tuple(args or ())
        self.kwargs = dict(kwargs or {})
        self.filter = Filter(filter) if filter else None

    def __repr__(self):
        if self.name:
            return '<%s %r>' % (self.__class__.__name__, self.name)
        else:
            return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def get_extra_fields(self):
        return self.filter.get_extra_fields() if self.filter else []

    def handle_event(self, dispatcher, envvars, event):

        # TODO: Setup context.

        if not self.callback_in_subprocess:
            # Load it the first time.
            if self._callback is None:
                self._callback = get_func(self.callback)
            self._callback(event, *self.args, **self.kwargs)
            return

        environ = os.environ.copy()
        environ.update(envvars)

        cmd = get_command_prefix(envvars)
        cmd.extend((sys.executable, '-m', 'sgevents.dispatcher.callback'))

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, env=environ)
        proc.stdin.write(yaml.dump({
            'callback': self.callback,
            'args': self.args,
            'kwargs': self.kwargs,
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
    args = package.get('args', ())
    kwargs = package.get('kwargs', {})
    event = Event.factory(package['event'])

    callback(event, *args, **kwargs)


if __name__ == '__main__':
    exit(subprocess_main() or 0)

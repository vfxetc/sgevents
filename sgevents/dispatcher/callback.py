import logging
import os
import subprocess
import sys

import yaml

from ..event import Event
from .. import logs
from ..utils import get_func, get_func_name, get_command_prefix
from .filter import Filter


log = logging.getLogger(__name__)


class Callback(object):
    
    def __init__(self, callback, name=None, callback_in_subprocess=True, filter=None, envvars=None, args=None, kwargs=None, extra_fields=None):
        self.name = name or get_func_name(callback)
        self.callback = callback
        self.callback_in_subprocess = bool(callback_in_subprocess)
        self.args = tuple(args or ())
        self.kwargs = dict(kwargs or {})
        self.filter = Filter(filter) if filter else None
        self.envvars = dict(envvars or {})
        self.extra_fields = list(extra_fields or [])
        self._callback = None

    def __repr__(self):
        if self.name:
            return '<%s %r>' % (self.__class__.__name__, self.name)
        else:
            return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def get_extra_fields(self):
        return (self.filter.get_extra_fields() if self.filter else []) + self.extra_fields

    def handle_event(self, dispatcher, envvars, event):

        if not self.callback_in_subprocess:
            # Load it the first time.
            if self._callback is None:
                self._callback = get_func(self.callback)
            self._callback(event, *self.args, **self.kwargs)
            return

        # From here down is running in a subprocess.

        environ = os.environ.copy()
        environ.update(envvars)
        environ.update(self.envvars)

        cmd = get_command_prefix(envvars)
        cmd.extend((sys.executable, '-m', 'sgevents.dispatcher.callback'))

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, env=environ)
        proc.stdin.write(yaml.dump({

            'callback': get_func_name(self.callback),
            'event': dict(event),

            'args': self.args,
            'kwargs': self.kwargs,

            'log_setup': logs.get_log_setup(),
            'log_meta': logs.get_log_meta(),

        }))
        proc.stdin.close()

        ret = proc.wait()
        if ret:
            log.error('subprocess for %s returned %s' % (self.callback, ret))



def _test(event):
    print 'hello from the callback!'
    print event



def subprocess_main():

    raw_package = sys.stdin.read()
    package = yaml.load(raw_package)

    callback = get_func(package['callback'])
    event = Event.factory(package['event'])
    args = package.get('args', ())
    kwargs = package.get('kwargs', {})
    log_setup = package.get('log_setup')
    log_meta = package.get('log_meta')

    # Restore logging state.
    if log_setup:
        logs.setup_logs(*log_setup)
    if log_meta:
        logs.update_log_meta(**log_meta)
    logs.update_log_meta(event=event.id)

    callback(event, *args, **kwargs)


if __name__ == '__main__':
    exit(subprocess_main() or 0)

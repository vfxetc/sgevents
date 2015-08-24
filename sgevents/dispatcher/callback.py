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
    
    def __init__(self, callback, name=None, callback_in_subprocess=True, callback_on_qube=False, filter=None, envvars=None, args=None, kwargs=None):
        self.name = name or get_func_name(callback)
        self.callback = callback
        self.callback_in_subprocess = bool(callback_in_subprocess)
        self.callback_on_qube = bool(callback_on_qube)
        self.args = tuple(args or ())
        self.kwargs = dict(kwargs or {})
        self.filter = Filter(filter) if filter else None
        self.envvars = dict(envvars or {})

        self._callback = None

        if self.callback_on_qube and not self.callback_in_subprocess:
            raise ValueError('Cannot callback on Qube but not in subprocess')

    def __repr__(self):
        if self.name:
            return '<%s %r>' % (self.__class__.__name__, self.name)
        else:
            return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def get_extra_fields(self):
        fields = self.filter.get_extra_fields() if self.filter else []
        if self.callback_on_qube:
            fields.append('user.HumanUser.login')
        return fields

    def handle_event(self, dispatcher, envvars, event):

        if self.callback_on_qube:

            from qbfutures import Executor

            envvars = envvars.copy()
            envvars.update(self.envvars)

            extra = {
                'name': 'SGEvent: %s on %s' % (get_func_name(self.callback), event.summary),
                'env': envvars,
            }

            login = event.get('user.HumanUser.login')
            if login:
                extra['user'] = login.split('@')[0]

            args = [event]
            args.extend(self.args)

            future = Executor().submit_ext(self.callback, args, self.kwargs, **extra)
            log.info('Submitted to Qube as %s' % future.job_id)
            return


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
            'args': self.args,
            'kwargs': self.kwargs,
            'event': dict(event),
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
    args = package.get('args', ())
    kwargs = package.get('kwargs', {})
    event = Event.factory(package['event'])

    callback(event, *args, **kwargs)


if __name__ == '__main__':
    exit(subprocess_main() or 0)

import cPickle as pickle
import logging
import os
import subprocess
import sys

import yaml

from ..event import Event
from ..utils import get_func
from .filter import Filter
from ..utils import envvars_for_event, get_command_prefix


log = logging.getLogger(__name__)


class ShellScript(object):
    
    def __init__(self, script, name=None, filter=None):

        self.name = name
        self.script = script
        self.filter = Filter(filter) if filter else None

    def __repr__(self):
        if self.name:
            return '<%s %r>' % (self.__class__.__name__, self.name)
        else:
            return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def get_extra_fields(self):
        return self.filter.get_extra_fields() if self.filter else []

    def handle_event(self, dispatcher, envvars, event):

        environ = os.environ.copy()
        environ.update(envvars)
        environ.update(envvars_for_event(event))

        cmd = get_command_prefix(envvars)
        cmd.extend(('/bin/bash', '-c', self.script))

        proc = subprocess.Popen(cmd, env=environ)

        ret = proc.wait()
        if ret:
            log.error('shell script %r returned %s' % (self.script, ret))



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

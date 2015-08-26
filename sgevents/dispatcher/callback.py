import logging
import os
import subprocess
import sys

import yaml

from .. import logs
from ..event import Event
from ..subprocess import call_in_subprocess
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

        envvars = dict(envvars or {})
        envvars.update(self.envvars)
        proc = call_in_subprocess(self.callback, (event, ) + self.args, self.kwargs, envvars=envvars)

        ret = proc.wait()
        if ret:
            log.error('subprocess for %s returned %s' % (self.callback, ret))


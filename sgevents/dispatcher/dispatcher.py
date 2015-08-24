import os
import logging

import yaml

from ..utils import get_adhoc_module
from .callback import Callback
from .context import Context
from .shell import ShellScript

log = logging.getLogger(__name__)


class Dispatcher(object):

    def __init__(self):
        self.contexts = []
        self.handlers = []

    def load_plugins(self, dir_path):
        """Load plugins from ``*.yml`` and ``*.py`` files in given directory."""
        for name in os.listdir(dir_path):

            # Our NFS makes these all over the place.
            if name.startswith('.'):
                continue

            base, ext = os.path.splitext(name)
            if ext == '.py':
                self._load_python_plugin(os.path.join(dir_path, name))
            elif ext in ('.yml', '.yaml'):
                self._load_yaml_plugin(os.path.join(dir_path, name))

    def _load_python_plugin(self, path):
        log.info('Loading Python plugin(s) from %s' % path)

        module = get_adhoc_module(path)

        # Look for something that wants to register itself.
        init_func = getattr(module, '__sgevents_init__', None)
        if init_func:
            init_func(self)
            return

        # Look for a dictionary of metadata structured as one would find
        # in the yaml file.
        desc = getattr(module, '__sgevents__', None)
        if desc is not None:
            self._load_described_plugin(desc)
            return

        raise ValueError('missing __sgevents_init__ function and __sgevents__ dict in Python plugin')

    def _load_described_plugin(self, desc):

        if isinstance(desc, (list, tuple)):
            for x in desc:
                self._load_described_plugin(x)
            return

        if not isinstance(desc, dict):
            raise TypeError('plugin descriptions are dicts; got %s' % type(desc))

        kwargs = desc.copy()
        type_ = kwargs.pop('type')
        if type_ == 'callback':
            self.register_callback(**kwargs)
        elif type_ == 'shell':
            self.register_shell_script(**kwargs)
        elif type_ == 'context':
            self.register_context(**kwargs)
        else:
            raise ValueError('unknown plugin type %s' % type_)
        return

    def _load_yaml_plugin(self, path):
        log.info('Loading YAML plugin(s) from %s' % path)
        for data in yaml.load_all(open(path).read()):
            self._load_described_plugin(data)

    def register_callback(self, **kwargs):
        self.handlers.append(Callback(**kwargs))

    def register_shell_script(self, **kwargs):
        self.handlers.append(ShellScript(**kwargs))

    def register_context(self, **kwargs):
        self.contexts.append(Context(**kwargs))

    def get_extra_fields(self):
        """Get list of extra fields for ``EventLog`` for filter evaluation."""
        res = []
        for ctx in self.contexts:
            res.extend(ctx.get_extra_fields())
        for cb in self.handlers:
            res.extend(cb.get_extra_fields())
        return res

    def dispatch(self, event):
        """Dispatch the given event."""

        envvars = {}
        for ctx in self.contexts:
            if ctx.filter is None or ctx.filter.eval(event):
                log.info('Matched context %s; setting %s' % (ctx.name, ' '.join(sorted('%s=%s' % x for x in ctx.envvars.iteritems()))))
                envvars.update(ctx.envvars)

        for handler in self.handlers:
            if handler.filter is None or handler.filter.eval(event):
                log.info('Dispatching to %s %s' % (handler.__class__.__name__.lower(), handler.name))
                handler.handle_event(self, envvars, event)



import os
import logging

import yaml

from .callback import Callback
from .context import Context


log = logging.getLogger(__name__)


class Dispatcher(object):

    def __init__(self):
        self.contexts = []
        self.callbacks = []

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
        log.info('Loading Python plugin from %s' % path)

        namespace = {'__name__': path, '__file__': path}
        execfile(path, namespace)

        # Look for something that wants to register itself.
        init_func = namespace.get('__sgevents_init__')
        if init_func:
            init_func(self)
            return

        # Look for a dictionary of metadata structured as one would find
        # in the yaml file.
        desc = namespace.get('__sgevents__')
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
        elif type_ == 'context':
            self.register_context(**kwargs)
        else:
            raise ValueError('unknown plugin type %s' % type_)
        return

    def _load_yaml_plugin(self, path):
        for data in yaml.load_all(open(path).read()):
            self._load_described_plugin(data)

    def register_callback(self, **kwargs):
        self.callbacks.append(Callback(**kwargs))

    def register_context(self, **kwargs):
        self.contexts.append(Context(**kwargs))


    def get_extra_fields(self):
        """Get list of extra fields for ``EventLog`` for filter evaluation."""
        raise NotImplementedError

    def dispatch(self, event):
        """Dispatch the given event."""

        # TODO: Figure out a context.

        for callback in self.callbacks:
            # TODO: filter
            callback.handle_event(self, None, event)



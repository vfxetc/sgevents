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

        raise NotImplementedError('need __sgevents_init__ in python plugin')

    def _load_yaml_plugin(self, path):
        raise NotImplementedError

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



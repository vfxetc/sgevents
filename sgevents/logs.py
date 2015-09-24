from urllib import quote
import datetime
import itertools
import logging
import os
import sys
import threading
import time

try:
    from flask import request
except ImportError:
    request = None


log_globals = threading.local()


def get_log_meta():
    try:
        return log_globals.meta
    except AttributeError:
        log_globals.meta = meta = {}
        return meta


class _LogMetaContext(object):

    def __init__(self, kwargs):
        self.restore = get_log_meta()
        log_globals.meta = new_meta = self.restore.copy()
        new_meta.update(kwargs)

    def __enter__(self):
        pass

    def __exit__(self, *args):
        log_globals.meta = self.restore


def update_log_meta(**kwargs):
    return _LogMetaContext(kwargs)


_log_setup = None

def get_log_setup():
    return _log_setup
    
def setup_logs(
    file_dir=None, file_level=logging.INFO,
    smtp_args=None, smtp_level=logging.ERROR,
    debug=False
):

    # Stash these for subprocesses to pick up on.
    global _log_setup
    _log_setup = (file_dir, file_level, smtp_args, smtp_level, debug)

    # Silence connection pool opening and closing.
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)
    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Clear existing handlers.
    root.handlers[:] = []

    injector = RequestContextInjector()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s pid:%(pid)d %(meta_str)s %(name)s - %(message)s')

    def add_handler(handler):
        handler.addFilter(injector)
        handler.setFormatter(formatter)
        root.addHandler(handler)

    # Console logging.
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    add_handler(handler)

    # File logging.
    if file_dir:
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        handler = PatternedFileHandler(os.path.join(file_dir, '{date}.{pid}.log'))
        handler.setLevel(file_level)
        add_handler(handler)

    # Email logging.
    if smtp_args:
        handler = logging.handlers.SMTPHandler(*smtp_args)
        handler.setLevel(smtp_level)
        add_handler(handler)



class RequestContextInjector(logging.Filter):

    def filter(self, record):
        record.pid = os.getpid() # Would love to cache this, but we can't.
        record.__dict__.update(log_globals.__dict__)

        meta = getattr(record, 'meta', {})
        record.meta_str = ' '.join('%s:%s' % x for x in sorted(meta.iteritems()))
        return True


class PatternedFileHandler(logging.FileHandler):

    def __init__(self, *args, **kwargs):
        self._last_path = None
        super(PatternedFileHandler, self).__init__(*args, **kwargs)

    def _current_path(self):
        now = datetime.datetime.utcnow()
        return self.baseFilename.format(
            date=now.date().isoformat(),
            pid=os.getpid(),
        )

    def _open(self):
        self._last_path = path = self._current_path()
        return open(path, self.mode)

    def emit(self, record):
        if self._last_path and self._last_path != self._current_path():
            self.close()
        super(PatternedFileHandler, self).emit(record)



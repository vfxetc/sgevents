from __future__ import absolute_import

import cPickle as pickle
import os
import subprocess
import sys

from .utils import get_command_prefix, get_func_name, get_func
from . import logs


def call_in_subprocess(func, args=None, kwargs=None, envvars=None, ):

    cmd = get_command_prefix(envvars) if envvars else []
    cmd.extend((sys.executable, '-m', 'sgevents.subprocess'))

    environ = os.environ.copy()
    environ.update(envvars or {})

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, env=environ)

    proc.stdin.write(pickle.dumps({
        'func': get_func_name(func),
        'args': args,
        'kwargs': kwargs,
        'log_setup': logs.get_log_setup(),
        'log_meta': logs.get_log_meta(),

    }))
    proc.stdin.close()

    return proc


def _main():

    raw_package = sys.stdin.read()
    package = pickle.loads(raw_package)

    func = get_func(package['func'])
    args = package.get('args') or ()
    kwargs = package.get('kwargs') or {}
    log_setup = package.get('log_setup')
    log_meta = package.get('log_meta')

    # Restore logging state.
    if log_setup:
        logs.setup_logs(*log_setup)
    if log_meta:
        logs.update_log_meta(**log_meta)

    func(*args, **kwargs)



def test(*args, **kwargs):
    print __name__, args, kwargs



if __name__ == '__main__':
    exit(_main() or 0)
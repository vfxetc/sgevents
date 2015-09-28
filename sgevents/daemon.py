import argparse
import json
import logging
import os
import socket
import time

from .dispatcher import Dispatcher
from .eventlog import EventLog
from .logs import setup_logs, log_globals
from .utils import try_call_except_traceback


def main(argv=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--plugin-dir', action='append')
    parser.add_argument('-s', '--state-path')

    parser.add_argument('-l', '--log-dir')
    parser.add_argument('-e', '--email-errors', action='append')

    args = parser.parse_args(argv)

    # Set a global socket timeout, so that nothing socket related will ever
    # lock us up. This is likely to cause a few extra problems, but we can
    # deal with them.
    socket.setdefaulttimeout(60.1)
    
    smtp_args = (
        'localhost',
        'sgevents@mail.westernx',
        args.email_errors,
        'SGEvents on %s' % socket.gethostname(),
    ) if args.email_errors else None
    setup_logs(debug=args.verbose, file_dir=args.log_dir, smtp_args=smtp_args)

    state = {}
    state_path = args.state_path
    if state_path:
        state_dir = os.path.dirname(os.path.abspath(state_path))
        if not os.path.exists(state_dir):
            os.makedirs(state_dir)
        if os.path.exists(state_path):
            try:
                state = json.load(open(state_path))
            except ValueError as e:
                print e

    dispatcher = Dispatcher()
    for plugin_dir in args.plugin_dir or ():
        dispatcher.load_plugins(plugin_dir)

    event_log = EventLog(extra_fields=dispatcher.get_extra_fields(), last_id=state.get('last_id'))
    
    def on_event(event):
        try:
            dispatcher.dispatch(event)
        finally:
            if state_path:
                state['last_id'] = event.id
                with open(state_path, 'w') as fh:
                    fh.write(json.dumps(state))

    # Be hyper-vigilant.
    while True:
        try_call_except_traceback(event_log.process_events_forever, on_event)
        time.sleep(10)


if __name__ == '__main__':
    
    # We REALLY don't want to be using the cache for this stuff.
    os.environ.pop('SGCACHE', None)

    main()

import argparse
import json
import socket
import os

from ..dispatcher import Dispatcher
from ..eventlog import EventLog
from ..logs import setup_logs, log_globals


def main(argv=None):

    # We REALLY don't want to be using the cache for this stuff.
    os.environ.pop('SGCACHE', None)

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--plugin-dir', action='append')

    state_group = parser.add_mutually_exclusive_group()
    state_group.add_argument('-s', '--state-path')
    state_group.add_argument('--last-id', type=int)

    parser.add_argument('-l', '--log-dir')
    parser.add_argument('-e', '--email-errors', action='append')

    args = parser.parse_args(argv)

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

    event_log = EventLog(extra_fields=dispatcher.get_extra_fields(), last_id=args.last_id or state.get('last_id'))
    
    @event_log.process_events_forever
    def on_event(event):
        try:
            dispatcher.dispatch(event)
        finally:
            if state_path:
                state['last_id'] = event.id
                with open(state_path, 'w') as fh:
                    fh.write(json.dumps(state))


if __name__ == '__main__':
    main()

import argparse
import logging

from .dispatcher import Dispatcher
from .eventlog import EventLog
from .logs import setup_logs, log_globals


def main(argv=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--plugin-dir', action='append')
    args = parser.parse_args(argv)

    setup_logs(debug=args.verbose)

    dispatcher = Dispatcher()
    for plugin_dir in args.plugin_dir or ():
        dispatcher.load_plugins(plugin_dir)

    event_log = EventLog(extra_fields=dispatcher.get_extra_fields())
    event_log.process_events_forever(dispatcher.dispatch)


if __name__ == '__main__':

    main()

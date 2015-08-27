import argparse
import os
import sys
import logging

from ..dispatcher import Dispatcher
from ..event import Event
from ..eventlog import EventLog
from ..logs import setup_logs, log_globals
from ..utils import get_shotgun


log = logging.getLogger(__name__)


def main(argv=None):

    # We REALLY don't want to be using the cache for this stuff.
    os.environ.pop('SGCACHE', None)

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--plugin-dir', action='append')
    parser.add_argument('ids', nargs='+', type=int)

    args = parser.parse_args(argv)

    setup_logs(debug=args.verbose)

    dispatcher = Dispatcher()
    for plugin_dir in args.plugin_dir or ():
        dispatcher.load_plugins(plugin_dir)

    shotgun = get_shotgun()
    return_fields = list(Event.return_fields) + dispatcher.get_extra_fields()
    events = shotgun.find('EventLogEntry', [('id', 'in', args.ids)], return_fields,
        order=[{'field_name': 'created_by', 'direction': 'asc'}]
    )

    returned_ids = set(e['id'] for e in events)
    missing_ids = set(id_ for id_ in args.ids if id_ not in returned_ids)
    if missing_ids:
        print >> sys.stderr, 'Could not find events: %s' % ', '.join(map(str, sorted(missing_ids)))
        exit(1)

    for event in events:
        event = Event(event)
        log.info(event.summary)
        dispatcher.dispatch(event)


if __name__ == '__main__':
    main()

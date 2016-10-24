import argparse
import os
import sys
import logging
import json
import re

from ..dispatcher import Dispatcher
from ..event import Event
from ..eventlog import EventLog
from ..logs import setup_logs, log_globals
from ..utils import get_shotgun


log = logging.getLogger(__name__)


def iter_from_path(path):

    content = open(path).read()

    # Strip out comments.
    lines = content.splitlines()
    lines = [x for x in lines if not x.lstrip().startswith('#')]
    lines = [x for x in lines if not x.lstrip().startswith('//')]
    content = '\n'.join(lines)

    # Split up events.
    for chunk in re.split(r'(?:^|})\s*(?:\{|$)', content):
        chunk = chunk.strip()
        if not chunk:
            continue
        yield json.loads('{%s}' % chunk)


def main(argv=None):

    # We REALLY don't want to be using the cache for this stuff.
    os.environ.pop('SGCACHE', None)

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-P', '--plugin-dir', action='append')
    parser.add_argument('-p', '--plugin', action='append')

    parser.add_argument('ids_or_paths', nargs='+',
        help='path to log file, or IDs to fetch')

    args = parser.parse_args(argv)

    setup_logs(debug=args.verbose)

    dispatcher = Dispatcher()
    for plugin_dir in args.plugin_dir or ():
        dispatcher.load_plugin_dir(plugin_dir)
    for plugin_path in args.plugin or ():
        dispatcher.load_plugin(plugin_path)

    ids = [int(x) for x in args.ids_or_paths if x.isdigit()]
    if ids:

        shotgun = get_shotgun()
        return_fields = list(Event.return_fields) + dispatcher.get_extra_fields()
        events = shotgun.find('EventLogEntry', [('id', 'in', ids)], return_fields,
            order=[{'field_name': 'created_by', 'direction': 'asc'}]
        )

        # Assert we have them all.
        returned_ids = set(e['id'] for e in events)
        missing_ids = set(id_ for id_ in args.ids if id_ not in returned_ids)
        if missing_ids:
            print >> sys.stderr, 'Could not find events: %s' % ', '.join(map(str, sorted(missing_ids)))
            exit(1)

        events_by_id = {e['id']: e for e in events}

    for arg in args.ids_or_paths:

        if arg.isdigit():
            events = [events_by_id[int(arg)]]
        else:
            events = iter_from_path(arg)

        for event in events:
            event = Event.factory(event)
            log.info(event.summary)
            dispatcher.dispatch(event)


if __name__ == '__main__':
    main()

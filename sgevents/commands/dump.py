import argparse
import json
import os
import datetime
import sys

import yaml

from ..eventlog import EventLog
from ..logs import setup_logs


def json_default(value):
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return value


def main(argv=None):

    # We REALLY don't want to be using the cache for this stuff.
    os.environ.pop('SGCACHE', None)

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--pretty', action='store_true')
    parser.add_argument('-C', '--colour', action='store_true')
    parser.add_argument('-o', '--output')
    parser.add_argument('--last-id', type=int)

    args = parser.parse_args(argv)

    if args.colour:
        from pygments import highlight, lexers, formatters

    setup_logs(debug=args.verbose)

    out_fh = open(args.output, 'w') if args.output else None

    event_log = EventLog(last_id=args.last_id)
    for event in event_log.iter_events_forever():
        encoded = json.dumps(dict(event), default=json_default, indent=4 if args.pretty else None, sort_keys=True)
        if out_fh:
            out_fh.write(encoded + '\n\n')
        if args.colour:
            encoded = highlight(unicode(encoded, 'UTF-8'), lexers.JsonLexer(), formatters.TerminalFormatter())
        print encoded
        print
        sys.stdout.flush()


if __name__ == '__main__':
    main()

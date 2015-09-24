import argparse
import logging
import sys

from .eventlog import EventLog
from .logs import setup_logs


log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--pretty', action='store_true')
parser.add_argument('-d', '--dumps', action='store_true')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

setup_logs(debug=args.verbose)


for e in EventLog().iter_events_forever():
    if args.dumps:
        if args.verbose:
            log.info(e.summary)
        print e.dumps(pretty=args.pretty)
    else:
        print e.summary


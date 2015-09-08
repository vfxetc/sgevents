import argparse
import sys

from .eventlog import EventLog


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--pretty', action='store_true')
parser.add_argument('-d', '--dumps', action='store_true')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()


for e in EventLog().iter_events():
    if args.dumps:
        if args.verbose: print >> sys.stderr, e.summary
        print e.dumps(pretty=args.pretty)
    else:
        print e.summary


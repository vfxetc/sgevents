import json

from .core import EventLog


for e in EventLog().iter():
    print json.dumps(e, sort_keys=True, indent=4, default=str)

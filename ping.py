import time
import json
import logging
import pprint
import socket
import sys
import os
import urllib

os.environ.pop('SGCACHE', None)
sys.path.append('/usr/local/vee/environments/westernx/master/lib/python2.7/site-packages')

from shotgun_api3_registry import connect

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(('graylog.westernx', 12201))


time1 = time.time()

res = urllib.urlopen('http://httpbin.org/ip').read()

time2 = time.time()

sg = connect()
sg.info()

time3 = time.time()

res = sg.find('Project', [])

time4 = time.time()


msg = dict(
    version='1.1',
    host=socket.gethostname(),
    short_message='pinged Shotgun in %dms' % (1000 * (time4 - time3)),
    _application='shotgun.ping',
    _httpbin_total_time_ms=1000 * (time2 - time1),
    _shotgun_total_time_ms=1000 * (time4 - time2),
    _shotgun_connection_time_ms=1000 * (time3 - time2),
    _shotgun_request_time_ms=1000 * (time4 - time3),
)

encoded = json.dumps(msg)
sock.send(encoded)





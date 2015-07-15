import time
import pprint
import logging


try:
    from sgapi import Shotgun
except ImportError:
    from shotgun_api3 import Shotgun

try:
    from shotgun_api3_registry import get_args as get_sg_args
except ImportError:
    get_sg_args = None



log = logging.getLogger(__name__)


class EventLog(object):

    def __init__(self, shotgun=None, last_id=None, last_time=None):

        if shotgun is None:
            if get_sg_args is None:
                raise ValueError('Shotgun instance is required if shotgun_sg3_registry:get_args does not exist')
            shotgun_args = get_sg_args()
            shotgun = Shotgun(*shotgun_args)
        self.shotgun = shotgun
        
        self.last_id = last_id or None
        self.last_time = last_time or None

    def iter(self, batch_size=100, delay=3.0):
        while True:
            e = self.read(batch_size)
            if e:
                yield e
            else:
                time.sleep(delay)

    def read(self, batch_size=100):

        if self.last_id:
            entities = self._read(batch_size, filters=[('id', 'greater_than', self.last_id)])
        else:
            if self.last_time:
                # everything since the last time
                entities = self._read(batch_size, filters=[('created_at', 'greater_than', self.last_time)])
            else:
                # the last event
                entities = self._read(1, order=[{
                    'field_name': 'created_at',
                    'direction': 'desc',
                }])

        if entities:
            self.last_id = max(self.last_id or 0, max(e['id'] for e in entities))
            last_time = max(e['created_at'] for e in entities)
            self.last_time = max(self.last_time, last_time) if self.last_time else last_time

        return entities or None

    def _read(self, limit, filters=None, order=None):
        return self.shotgun.find('EventLogEntry', filters or [], order=order or [], limit=limit, fields=[
            'attribute_name',
            'created_at',
            'entity',
            'event_type',
            'meta',
            'project',
            'user',
        ])






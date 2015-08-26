import json
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(('graylog.westernx', 12201))


def callback(event):
    
    entity = event.get('entity') or {}
    entity.setdefault('type', 'NOTYPE')
    entity.setdefault('id', 0)

    msg = dict(
        version='1.1',
        host='sgevents.westernx', # socket.gethostname(),
        short_message=event.summary,
        _application='shotgun.events',
        _shotgun_event_type=event['event_type'],
    )

    encoded = json.dumps(msg)
    sock.send(encoded)


__sgevents__ = dict(
    type='callback',
    callback_in_subprocess=False,
    callback=callback,
)




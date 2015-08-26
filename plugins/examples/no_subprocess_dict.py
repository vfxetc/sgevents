import logging
import os

log = logging.getLogger('no_subprocess_dict')


def handle_event(event):
    log.info('%s %d %s' % (__file__, os.getpid(), event))


__sgevents__ = {
    'type': 'callback',
    'callback': handle_event,
    'callback_in_subprocess': False,
}



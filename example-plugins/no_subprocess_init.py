import logging
import os

log = logging.getLogger(os.path.basename(__file__))


def handle_event(event):
    log.info('%s %d %s' % (__file__, os.getpid(), event))


def __sgevents_init__(dispatcher):
    dispatcher.register_callback(callback=handle_event, callback_in_subprocess=False)


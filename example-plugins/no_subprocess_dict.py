

def handle_event(event):
    print __file__, event


__sgevents__ = {
    'type': 'callback',
    'callback': handle_event,
    'callback_in_subprocess': False,
}



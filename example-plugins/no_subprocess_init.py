

def handle_event(event):
    print __file__, event


def __sgevents_init__(dispatcher):
    dispatcher.register_callback(callback=handle_event, callback_in_subprocess=False)


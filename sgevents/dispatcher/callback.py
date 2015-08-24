
class Callback(object):
    
    def __init__(self, callback, callback_in_subprocess=True):
        self.callback = callback
        self.callback_in_subprocess = bool(callback_in_subprocess)

    def handle_event(self, dispatcher, context, event):

        # TODO: Setup context.

        if not self.callback_in_subprocess:
            self.callback(event)
            return

        raise NotImplementedError('no subprocesses for callbacks yet')



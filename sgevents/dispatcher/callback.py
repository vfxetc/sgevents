
class Callback(object):
    
    def __init__(self, callback, in_subprocess=True):
        self.callback = callback
        self.in_subprocess = bool(in_subprocess)

    def handle_event(self, dispatcher, context, event):

        # TODO: Setup context.

        if not self.in_subprocess:
            self.callback(event)
            return

        raise NotImplementedError('no subprocesses for callbacks yet')



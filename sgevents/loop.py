import threading


class LoopController(object):

    def __init__(self):
        self._allowed_to_run = threading.Event()
        self._allowed_to_run.set()
        self._is_sleeping = threading.Event()
        self._poll_signal = threading.Condition()
        self._sleep_signal = threading.Condition()

    def sleep(self, delay):

        self._is_sleeping.set()

        # If anything is waiting for us to sleep, let them know.
        with self._sleep_signal:
            self._sleep_signal.notify_all()

        # Sleep until something wakes us up.
        delay = min(delay, 60)
        with self._poll_signal:
            self._poll_signal.wait(delay)

        # Finally, make sure we are allowed to continue from here.
        self._allowed_to_run.wait()
        self._is_sleeping.clear()

    def poll(self, wait=False, timeout=30.0):
        """Force a poll from another thread."""
        self._allowed_to_run.set()
        with self._poll_signal:
            self._poll_signal.notify_all()
        if wait:
            with self._sleep_signal:
                self._sleep_signal.wait(timeout)

    def start(self):
        """Start the loop from another thread."""
        state = self._allowed_to_run.is_set()
        self._allowed_to_run.set()
        return not state

    def stop(self, timeout=30.0):
        """Stop the loop from another thread."""
        state = self._allowed_to_run.is_set()
        self._allowed_to_run.clear()
        self._is_sleeping.wait(timeout)
        return state

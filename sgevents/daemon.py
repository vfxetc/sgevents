
from .dispatcher import Dispatcher
from .eventlog import EventLog



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--plugins', action='append')
    args = parser.parse_args()

    dispatcher = Dispatcher()
    for plugin_dir in args.plugins or ():
        dispatcher.load_plugins(plugin_dir)

    for e in EventLog().iter_events():
        dispatcher.dispatch(e)



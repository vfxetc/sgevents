import logging

from ..utils import get_func_name
from .filter import Filter


log = logging.getLogger(__name__)


class QubeCallback(object):

    def __init__(self, callback, name=None, filter=None, envvars=None, args=None, kwargs=None):

        self.name = name or get_func_name(callback)
        self.callback = callback
        self.args = tuple(args or ())
        self.kwargs = dict(kwargs or {})
        self.filter = Filter(filter) if filter else None
        self.envvars = dict(envvars or {})

    def __repr__(self):
        if self.name:
            return '<%s %r>' % (self.__class__.__name__, self.name)
        else:
            return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def get_extra_fields(self):
        fields = self.filter.get_extra_fields() if self.filter else []
        fields.append('user.HumanUser.login')
        return fields

    def handle_event(self, dispatcher, envvars, event):

        from qbfutures import Executor

        envvars = envvars.copy()
        envvars.update(self.envvars)

        extra = {
            'name': 'Shotgun: %r on %s' % (self.name, event.summary),
            'env': envvars,
        }

        login = event.get('user.HumanUser.login')
        if login:
            extra['user'] = login.split('@')[0]

        args = [event]
        args.extend(self.args)

        future = Executor().submit_ext(self.callback, args, self.kwargs, **extra)
        log.info('Submitted to Qube as %s' % future.job_id)


def _test(event):
    print 'HELLO FROM THE TEST CALLBACK!'
    print event



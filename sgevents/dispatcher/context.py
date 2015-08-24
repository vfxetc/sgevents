from .filter import Filter

class Context(object):

    def __init__(self, name=None, envvars=None, filter=None):
        self.name = name or str(envvars)
        self.envvars = dict(envvars or {})
        self.filter = Filter(filter) if filter else None

    def __repr__(self):
        if self.name:
            return '<%s %r>' % (self.__class__.__name__, self.name)
        else:
            return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def get_extra_fields(self):
        return self.filter.get_extra_fields() if self.filter else []

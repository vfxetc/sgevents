import re


def get_func(spec):

    if not isinstance(spec, basestring):
        return spec
    
    m = re.match(r'([\w\.]+):([\w]+)$', spec)
    if m:
        mod_name, func_name = m.groups()
        mod = __import__(mod_name, fromlist=['.'])
        return getattr(mod, func_name)

    m = re.match(r'(.+):([\w]+)$', spec)
    if m:
        path, func_name = m.groups()
        if '/' in path:
            namespace = {'__name__': path, '__file__': path}
            execfile(path, namespace)
            return namespace[func_name]

    raise ValueError('spec must be like "/path/to/module.py:func_name" or "package.module:func_name"; got %r' % spec)



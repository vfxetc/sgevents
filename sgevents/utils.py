import imp
import hashlib
import re
import sys


def get_adhoc_module(path):
    name = re.sub('\W+', '__', path) + '_' + hashlib.md5(path).hexdigest()[:8]
    try:
        return sys.modules[name]
    except KeyError:
        return imp.load_source(name, path)


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
            module = get_adhoc_module(path)
            return getattr(module, func_name)

    raise ValueError('spec must be like "/path/to/module.py:func_name" or "package.module:func_name"; got %r' % spec)



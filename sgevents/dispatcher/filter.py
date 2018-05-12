import functools
import re

from ..utils import get_func


class Filter(object):

    def __init__(self, input_):

        self.attributes = None
        self.callback = None
        self._callback = None

        if isinstance(input_, dict):
            self.attributes = {}
            for k, v in input_.iteritems():

                # Regex patterns.
                if isinstance(v, basestring):
                    m = re.match(r'^/(.+?)/([iIlLmMsSuUxX]*)$', v)
                    if m:
                        pattern, flags = m.groups()
                        compiled = re.compile(pattern, flags=sum((getattr(re, flag.upper()) for flag in flags), 0))
                        self.attributes[k] = functools.partial(self._eval_regex, compiled)
                        continue

                if isinstance(v, dict) and 'type' in v and 'id' in v:
                    self.attributes[k] = functools.partial(self._eval_entity_equality, v['type'], v['id'])
                    return

                if isinstance(v, (tuple, set)):
                    self.attributes[k] = lambda key, value: value in v
                    return
                
                self.attributes[k] = functools.partial(self._eval_equality, v)

        else:
            self.callback = input_

    def get_extra_fields(self):
        if self.attributes:
            return self.attributes.keys()
        else:
            return []

    def eval(self, event):

        if self.callback:
            if self._callback is None:
                self._callback = get_func(self.callback)
            return self.callback(event)

        elif self.attributes:
            for k, func in self.attributes.iteritems():
                if not func(k, event.get(k)):
                    return False
            return True

        else:
            raise NotImplementedError()

    def _eval_regex(self, pattern, key, value):
        return bool(pattern.match(str(value or '')))

    def _eval_entity_equality(self, type_, id_, key, value):
        return isinstance(value, dict) and value.get('type') == type_ and value.get('id') == id_

    def _eval_equality(self, expected, key, value):
        return value == expected


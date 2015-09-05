import json
import re

from .utils import pickleable


def _item_property(key, doc=None, transform=None):
    if transform:
        def _func(event):
            return transform(event.get(key))
    else:
        def _func(event):
            return event.get(key)
    return property(_func, doc=doc)


_specialization_classes = []

def _specialization(predicate):
    def _decorator(cls):
        _specialization_classes.append(cls)
        return cls
    return _decorator



class Event(dict):

    """A smarter ``EventLogEntry`` entity.

    This is a dict, just as would be returned from the Shotgun API, but it
    is instrumented with a number of properties and methods to smooth out
    some of the edge cases of the event log.

    """

    #: Required fields to query from the API.
    return_fields = (
        'attribute_name',
        'created_at',
        'entity',
        'event_type',
        'meta',
        'project',
        'user',
    )
    
    @classmethod
    def factory(cls, event):
        # Look for one of the specializations.
        for subcls in _specialization_classes:
            obj = subcls.specialist_factory(event)
            if obj:
                return obj
        return cls(event)


    def __init__(self, raw, shotgun=None):
        super(Event, self).__init__(raw)
        self._shotgun = shotgun

    id = _item_property('id', """The ID of the ``EventLogEntry`` entity.""")

    created_at = _item_property('created_at',
        """When the event happened, in the type returned by the Shotgun API object.""")

    event_type = _item_property('event_type',
        """The complete type of the event, e.g. ``"Shotgun_Shot_Change"``.""")

    domain = _item_property('event_type', transform=lambda x: x.split('_', 2)[0], doc=
        """The event's namespace; every Shotgun event will have the domain ``"Shotgun"``.""")
    
    subtype = _item_property('event_type', transform=lambda x: x.split('_', 2)[-1], doc=
        """The action associated with this event; Shotgun events are of the subtype:

        - ``"New"``: creation of an entity
        - ``"Change"``: updates to an entity
        - ``"Retirement"``: "deletion" of an entity
        - ``"Revival"``: "un-deletion" of an entity
        - ``"View"``: tracking that a human has viewed an entity

        Behaviour is only defined for Shotgun events.

        """)

    user = _item_property('user', 
        """The ``HumanUser`` or ``ApiUser`` that triggered this event.""")

    # We've seen this come back None when Shotgun does automatic updates.
    meta = _item_property('meta', transform=lambda x: x if x is not None else {})

    entity = _item_property('entity',
        """The entity, if availible.

        The entity will often not load immediately if it has been retired.
        :meth:`find_retired_entity` will attempt to find it.

        """)

    def _entity_type_transform(x):
        x = x.split('_')
        return x[1] if len(x) > 1 else None

    entity_type = _item_property('event_type', transform=_entity_type_transform, doc="""
        The type of the entity.

        This is as reported by the event's :attr:`type`, which is always availible even
        if the entity is not. However, there is at least one case in which
        this differs from the type of the :attr:`entity`: the :ref:`reading_meta_type`.

        Behaviour is only defined for Shotgun events.

    """.strip())

    @property
    def entity_id(self):
        """The ID of the entity, which is sometimes availible even when the entity is not.

        There is an ``entity_id`` key in the :attr:`meta` dict, but there are
        circumstances in which that value is wrong. This property attempts to
        filter them out.

        """

        if self.entity:
            return self.entity['id']
        if 'entity_id' in self.meta:
            if self.subtype == 'Change' and 'actual_attribute_changed' in self.meta:
                # The metadata for backref changes is wrong; it refers to the
                # triggering entity, not the backref.
                return
            return self.meta['entity_id']

    @property
    def subject_entity(self):
        """The subject of an event; usually :attr:`entity`.

        This differs for ``"View"`` events.

        """
        return self.entity

    @property
    def summary(self):

        parts = [self.event_type]

        subject = self.subject_entity or self.entity
        if subject:
            parts.append('on %s:%d' % (subject['type'], subject['id']))
            if subject.get('name'):
                parts.append('("%s")' % subject['name'])
        else:
            parts.append('on %s:%s' % (self.entity_type, self.entity_id or 'unknown'))

        if self.user:
            parts.append('by %s:%d' % (self.user['type'], self.user['id']))
            if self.user.get('name'):
                parts.append('("%s")' % self.user['name'])

        return ' '.join(parts)


    def __str__(self):
        return '<Event %s>' % self.summary

    def dumps(self, pretty=False):
        return json.dumps(self, sort_keys=pretty, indent=4 if pretty else None, default=str)

    def find_retired_entity(self):
        """Find the "retired" entity that goes with this event log.

        If this event already has an entity, it will be returned. Ergo, this
        method can safely be called in all circumstances if you want an entity
        no matter where it comes from.

        .. warning:: This depends upon the ``$FROM$`` filter syntax,
            which is officially unsupported.

        """
        if not self.entity:
            e = self._shotgun.find_one(self.entity_type, [('$FROM$EventLogEntry.entity.id', 'is', self.id)])
            if not e:
                raise ValueError('could not find retired %s for event %d' % (self.entity_type, self.id))
            self['entity'] = e
        return self.entity

    def __reduce__(self):
        return (self.__class__, (pickleable(self), ))


@_specialization
class ReadingChangeEvent(Event):

    @classmethod
    def specialist_factory(cls, event):
        if event['event_type'] == 'Shotgun_Reading_Change':
            return cls(event)

    @property
    def entity_type(self):
        return self.entity['type']


@_specialization
class ViewEvent(Event):

    @classmethod
    def specialist_factory(cls, event):
        type_ = event['event_type']
        if type_.endswith('_View') and type_.startswith('Shotgun_'):
            return cls(event)

    @property
    def subject_entity(self):
        try:
            return {
                'type': self.meta['link_entity_type'],
                'id': self.meta['link_entity_id'],
            }
        except KeyError:
            pass


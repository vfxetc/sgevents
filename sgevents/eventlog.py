import time
import pprint
import logging

from .event import Event
from .logs import update_log_meta
from .utils import get_func_name, get_shotgun


log = logging.getLogger(__name__)


class EventLog(object):

    """An object to poll Shotgun's API for new ``EventLogEntry`` entities.

    :param shotgun: A ``shotgun_api3`` compatible Shotgun API instance,
        a tuple of arguments for ``shotgun_api3.Shotgun`` or ``None``.
        Typically we actually use ``sgapi``. If ``None``, we get API arguments
        via ``shotgun_api3_registry:get_args`` (if such a module exists).
    :param int last_id: The last ``EventLogEntry`` id that was fully
        processed.
    :param last_time: The last time any events were processed. Note that
        this must be the same type as returned by the ``shotgun`` object;
        care is taken so that we can handle either ``str`` or ``datetime``.

    """

    def __init__(self, shotgun=None, last_id=None, last_time=None, extra_fields=None):

        self.shotgun = get_shotgun(shotgun)
        
        #: The highest event ID for which we have processed everything lower.
        self.max_complete_id = last_id or 0

        #: The highest event ID we have seen; those missing from :attr:`max_complete_id`
        #: and here will have a record in :attr:`missing_ids`.
        self.max_partial_id = last_id or 0

        #: Mapping from missing IDs to when they were declared missing.
        self.missing_ids = {}

        #: How long to track missing IDs until we give up on them;
        #: defaults to 30 seconds.
        self.id_timeout = 30.0

        #: The time of the last event we have seen.
        self.last_time = last_time or None

        self.return_fields = list(Event.return_fields)
        if extra_fields:
            self.return_fields.extend(extra_fields)

    def process_events_forever(self, func, *args, **kwargs):
        while True:
            try:
                for event in self.iter_events_forever(*args, **kwargs):
                    try:
                        with update_log_meta(event=event.id):
                            log.info(event.summary)
                            func(event)
                    except KeyboardInterrupt:
                        return
                    except:
                        log.exception('error calling %s with event %d:\n%s' % (get_func_name(func), event.id, event.dumps(pretty=True)))
            
            except KeyboardInterrupt:
                return
            except:
                log.exception('error during event iteration; sleeping for 10s')
                time.sleep(10)
            else:
                log.warning('iter_events_forever returned; sleeping for 10s')
                time.sleep(10)

    def iter_events_forever(self, batch_size=100, idle_delay=3.0):
        """Yields :class:`Event` objects as they become availible.

        :param int batch_size: The number of events to read from the API at once.
        :param float idle_delay: The delay between idle polls of the event log,
            in seconds.

        Exceptions from the connection to Shotgun (which happen more frequently
        than you might think when this is left running 24/7) will be raised,
        although they tend to be ``sgapi.TransportError``.

        ::

            for event in event_log.iter_events_forever():
                handle_event(event)

        """
        
        while True:

            batch = self.iter_events(batch_size)
            for e in batch:
                yield e

            if not batch:
                time.sleep(idle_delay)

    def iter_events(self, count=100, wrap=True):
        """Polls for new events, filtering with :func:`filter_new`.

        The EventLog assumes that once an event has been yielded OR an exception
        raised, the underlying event has been processed and will not be yielded
        again by subsequent calls. This is required for our error handling
        to not go into an infinite loop in case we have internal errors for
        specific events (e.g. in the specialization classes).

        :param int count: The number of events to read from the API at once.
        :param bool wrap: Return :class:`Event` instead of raw ``EventLogEntry``.
        :return generator: of events (or entities).

        """
        raw_entities = self.find_next_entities(count)
        for entity in raw_entities:
            if self.filter_new(entity):
                yield Event.factory(entity) if wrap else entity

    def find_next_entities(self, count=100):
        """Find the next raw ``EventLogEntry`` entities.

        This method does NOT update the ``last_id`` or ``last_time`` fields;
        use :meth:`filter_new` on each entity for that.

        """

        if self.max_complete_id:
            entities = self.find_entities(count, filters=[('id', 'greater_than', self.max_complete_id)])
        else:
            if self.last_time:
                # everything since the last time
                log.info('starting at most recent event since %s' % self.last_time)
                entities = self.find_entities(count, filters=[('created_at', 'greater_than', self.last_time)])
            else:
                # the last event
                log.info('starting at most recent event')
                entities = self.find_entities(1, order=[{
                    'field_name': 'created_at',
                    'direction': 'desc',
                }])
            if entities:
                log.info('most recent event is %d at %s' % (entities[0]['id'], entities[0]['created_at']))

        return entities or []

    def filter_new(self, entity):
        """Filter out entities which we have seen before, and update our records.

        Due to the transaction model of Shotgun's underlying database, it is
        possible for events with lower IDs to be created after those with
        higher IDs. This method is primarly dealing with remembering those
        gaps, and making sure we don't skip those events if they do eventually
        show up in the log stream.

        :param dict entity: A raw ``EventLogEntry`` entity.
        :return: The entity if it has not been seen before, else ``None``.

        """

        # We try to be agressively defensive in this function, doing
        # things in a manner/order such that if we made a mistake (or get
        # odd entities from Shotgun) then we do not go into an infinite loop
        # of fetching and processing the same entities over and over.

        id_ = entity['id']
        entity_is_new = id_ > self.max_partial_id or id_ in self.missing_ids

        now = time.time()
        newly_missed = []

        # If we have run before, and there is a gap being introduced by
        # this event, then track it.
        if self.max_partial_id:
            for i in xrange(self.max_partial_id + 1, id_):
                newly_missed.append(i)
                self.missing_ids[i] = now

        self.max_partial_id = max(self.max_partial_id, id_)
        self.missing_ids.pop(id_, None)

        if newly_missed:
            log.warning('missing %d event id%s: %s' % (
                len(newly_missed),
                's' if len(newly_missed) > 1 else '',
                ', '.join(str(i) for i in sorted(newly_missed)),
            ))

        # Prune any missing ids which have gotten too old.
        expired_ids = [i for i, t in self.missing_ids.iteritems() if (now - t) > self.id_timeout]
        if expired_ids:
            log.warning('pruning %d event id%s which have timed out: %s' % (
                len(expired_ids),
                's' if len(expired_ids) > 1 else '',
                ', '.join(str(i) for i in sorted(expired_ids)),
            ))
            for i in expired_ids:
                self.missing_ids.pop(i)

        # Figure out what the last id we have complete knowledge of is.
        if self.missing_ids:
            self.max_complete_id = min(self.missing_ids) - 1
        else:
            self.max_complete_id = self.max_partial_id

        # We don't use this ourselves after the first scan, but it may be nice to have.
        self.last_time = max(self.last_time, entity['created_at']) if self.last_time else entity['created_at']

        return entity if entity_is_new else None

    def find_entities(self, limit, filters=None, **kwargs):
        return self.shotgun.find('EventLogEntry',
            filters or [],
            self.return_fields,
            limit=limit,
            **kwargs
        )






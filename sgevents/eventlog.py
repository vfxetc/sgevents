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
        #: defaults to 15 seconds.
        self.id_timeout = 15.0

        #: The time of the last event we have seen.
        self.last_time = last_time or None

        self.return_fields = list(Event.return_fields)
        if extra_fields:
            self.return_fields.extend(extra_fields)

    def process_events_forever(self, func, *args, **kwargs):
        while True:
            try:
                for event in self.iter_events(*args, **kwargs):
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

    def iter_events(self, batch_size=100, idle_delay=3.0):
        """Yields :class:`Event` objects as they become availible.

        :param int batch_size: The number of events to read from the API at once.
        :param float idle_delay: The delay between idle polls of the event log,
            in seconds.

        Exceptions from the connection to Shotgun (which happen more frequently
        than you might think when this is left running 24/7) will be raised,
        although they tend to be ``sgapi.TransportError``.

        ::

            for event in event_log.iter():
                handle_event(event)

        """
        
        while True:

            batch = self.read(batch_size)
            for e in batch:
                yield e

            if not batch:
                time.sleep(idle_delay)


    def read(self, count=100):
        """Polls for new events, filtering with :func:`filter_new`.

        :param int count: The number of events to read from the API at once.
        :return list: of new :class:`Event`.

        """

        if self.max_complete_id:
            entities = self._find(count, filters=[('id', 'greater_than', self.max_complete_id)])
        else:
            if self.last_time:
                # everything since the last time
                log.info('starting at most recent event since %s' % self.last_time)
                entities = self._find(count, filters=[('created_at', 'greater_than', self.last_time)])
            else:
                # the last event
                log.info('starting at most recent event')
                entities = self._find(1, order=[{
                    'field_name': 'created_at',
                    'direction': 'desc',
                }])
            if entities:
                log.info('most recent event is %d at %s' % (entities[0].id, entities[0].created_at))

        return self.filter_new(entities) if entities else []

    def filter_new(self, entities):
        """Filter out entities which we have seen before.

        Due to the transaction model of Shotgun's underlying database, it is
        possible for events with lower IDs to be created after those with
        higher IDs. This method is primarly dealing with remembering those
        gaps, and making sure we don't skip those events if they do eventually
        show up in the log stream.

        """

        now = time.time()
        newly_missed = []
        unseen_entities = []

        # TODO: be really defensive in here re: exceptions being raised
        # and causing our tracking data to corrupt if we keep polling afterwards.
        
        for e in entities:
            
            if e.id > self.max_partial_id or e.id in self.missing_ids:
                unseen_entities.append(e)

            # If we have run before, and there is a gap being introduced by
            # this event, then track it.
            if self.max_partial_id:
                for i in xrange(self.max_partial_id + 1, e.id):
                    log.info('newly missed event?? %s' % e.summary)
                    newly_missed.append(i)
                    self.missing_ids[i] = now

            self.max_partial_id = max(self.max_partial_id, e.id)
            self.missing_ids.pop(e.id, None)

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
        self.last_time = max(e['created_at'] for e in entities)

        return unseen_entities


    def _find(self, limit, filters=None, **kwargs):
        raw_events = self.shotgun.find('EventLogEntry',
            filters or [],
            self.return_fields,
            limit=limit,
            **kwargs
        )
        return [Event.factory(e) for e in raw_events]






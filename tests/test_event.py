from . import *



class TestEvent(TestCase):

    def test_odd_event_types(self):

        event = Event.factory({'event_type': 'ClientLogin_Failed'})
        # These are undefined behaviour...
        self.assertEqual(event.domain, 'ClientLogin')
        self.assertEqual(event.subtype, 'Failed')

        event = Event.factory({'event_type': 'SG_RV_Session_Validate_Success'})
        # These are undefined behaviour...
        self.assertEqual(event.domain, 'SG')
        self.assertEqual(event.subtype, 'Session_Validate_Success')

    def test_entity_type(self):

        # Most events don't need the actual entity.
        event = Event.factory({
            'event_type': 'Shotgun_Version_Change',
        })
        self.assertEqual(event.entity_type, 'Version')

        # Reading events do!
        entity = dict(type='Version', id=1234)
        event = Event.factory({
            'event_type': 'Shotgun_Reading_Change',
            'entity': entity,
        })
        self.assertEqual(event.__class__.__name__, 'ReadingChangeEvent')
        self.assertEqual(event.entity_type, 'Version')

    def test_subject_entity(self):

        event = Event.factory({
            'event_type': 'Shotgun_Page_Change',
            'entity': {'type': 'Page', 'id': 1234},
            'meta': {'link_entity_type': 'Version', 'link_entity_id': 1234},
        })
        self.assertEqual(event.entity_type, 'Page')
        self.assertEqual(event.entity, {'type': 'Page', 'id': 1234})
        self.assertEqual(event.subject_entity, {'type': 'Page', 'id': 1234})

        event = Event.factory({
            'event_type': 'Shotgun_Version_View',
            'entity': {'type': 'Page', 'id': 1234},
            'meta': {'link_entity_type': 'Version', 'link_entity_id': 1234},
        })
        self.assertEqual(event.__class__.__name__, 'ViewEvent')
        self.assertEqual(event.entity_type, 'Version')
        self.assertEqual(event.entity, {'type': 'Page', 'id': 1234}) # This is wierd.
        self.assertEqual(event.subject_entity, {'type': 'Version', 'id': 1234})

    def test_entity_is_retired(self):

        event = Event.factory({
            'event_type': 'Shotgun_Version_Change',
            'entity': {'type': 'Version', 'id': 1234},
        })
        self.assertFalse(event.entity_is_retired)

        event = Event.factory({
            'event_type': 'Shotgun_Version_Change',
            'entity': None,
        })
        self.assertTrue(event.entity_is_retired)

        event['entity'] = {'type': 'Version', 'id': 1234}
        self.assertTrue(event.entity_is_retired)
        


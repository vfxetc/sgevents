import logging

from sgevents.subprocess import call_in_subprocess
from sgsession import Session


log = logging.getLogger(__name__)


def callback(event):
    
    sg = Session()
    event = sg.merge(event)
    
    # Must be setting it to a non-zero version.
    version = event.get('entity.PublishEvent.sg_version')
    if not version:
        log.info('Publish is still being created; skipping')
        return

    # For now, we only run for the Testing Sandbox.
    #if event['project']['id'] != 66:
    #    log.info('Project %r in not Testing Sandbox; skipping' % (event['project'].get('name') or event['project']['id']))
    #    return

    # Our first job, is to create camera and geocache publishes from generic maya scenes.
    pub_type = event.get('entity.PublishEvent.sg_type')
    if pub_type != 'maya_scene':
        log.info('sg_type %r is not maya_scene; skipping' % pub_type)
        return
    step_code = event.get('entity.PublishEvent.sg_link.Task.step.Step.short_name')
    if step_code not in ('Anim', 'Roto'):
        log.info('sg_link.step.short_code %s is not Anim or Roto; skipping' % step_code)
        return
    
    log.info('Delegating to sgactions')
    call_in_subprocess('%s:republish' % __file__, [event['entity.PublishEvent.id']])


def republish(id_):

    from mayatools.actions.publishes import republish_camera, republish_geocache

    log.info('Scheduling camera republish...')
    republish_camera('PublishEvent', [id_])

    log.info('Scheduling geocache republish...')
    republish_geocache('PublishEvent', [id_])


__sgevents__ = dict(
    type='callback',
    callback_in_subprocess=False,
    callback=callback,
    filter={
        'event_type': 'Shotgun_PublishEvent_Change',
        'attribute_name': 'sg_version',
    },
    extra_fields=[
        'entity.PublishEvent.sg_link',
        'entity.PublishEvent.sg_link.Task.step.Step.short_name',
        'entity.PublishEvent.sg_type',
        'entity.PublishEvent.sg_version',
    ],
)




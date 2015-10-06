import logging

from sgevents.subprocess import call_in_subprocess
from sgsession import Session


log = logging.getLogger(__name__)


def callback(event):
    
    sg = Session()
    
    # Must be setting it to a non-zero version.
    # NOTE: We MUST check the meta for this, otherwise we are liable to
    # schedule this job multiple times as the `entity` field is always
    # up to date.
    version = event.meta.get('new_value')
    if not version:
        log.info('Publish is still being created; skipping')
        return

    entity = sg.merge(event)['entity']
    if not entity:
        log.info('Publish appeares to have been retired; skipping')
        return

    # For now, we only run for the Testing Sandbox.
    #if event['project']['id'] != 66:
    #    log.info('Project %r in not Testing Sandbox; skipping' % (event['project'].get('name') or event['project']['id']))
    #    return

    # Our first job, is to create camera and geocache publishes from generic maya scenes.
    pub_type = entity.get('sg_type')
    if pub_type != 'maya_scene':
        log.info('sg_type %r is not maya_scene; skipping' % pub_type)
        return
    step_code = entity.get('sg_link.Task.step.Step.short_name')
    if step_code not in ('Anim', 'Roto', 'Rotomation'):
        log.info('sg_link.step.short_code %s is not Anim or Roto; skipping' % step_code)
        return
    
    log.info('Delegating to sgactions')
    call_in_subprocess('%s:republish' % __file__, [entity['id']])


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
    ],
)




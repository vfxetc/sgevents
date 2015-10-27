import logging

from sgsession import Session
from shotgun_api3_registry import connect
import qbfutures


log = logging.getLogger(__name__)


def callback(event):
    
    # Must be setting it to a non-zero version.
    # NOTE: We MUST check the meta for this, otherwise we are liable to
    # schedule this job multiple times as the `entity` field is always
    # up to date.
    version = event.meta.get('new_value')
    if not version:
        log.info('Publish is still being created; skipping')
        return

    sg = Session(connect())
    
    entity = sg.merge(event)['entity']
    if not entity:
        log.info('Publish appeares to have been retired; skipping')
        return
        
    entity.fetch(('code', 'sg_link.Task.step.Step.short_name', 'sg_type', 'created_by.HumanUser.login'))

    # For now, we only run for the Testing Sandbox.
    #if event['project']['id'] != 66:
    #    log.info('Project %r in not Testing Sandbox; skipping' % (event['project'].get('name') or event['project']['id']))
    #    return

    pub_type = entity.get('sg_type')
    if pub_type != 'plate':
        log.info('sg_type %r is not plate; skipping' % pub_type)
        return

    step_code = entity.get('sg_link.Task.step.Step.short_name')
    if step_code not in ('Online', ):
        log.info('sg_link.step.short_code %s is not Online; skipping' % step_code)
        return
    
    # TODO: Make sure it doesn't already exist.

    # Run it as the correct user; assume their Shotgun login matches.
    login = entity.get('created_by.HumanUser.login')
    user = login.split('@')[0] if login else None

    future = qbfutures.submit_ext('kspipeline.edit.plate_publish.core:republish_as_proxy',
        args=[entity.minimal],
        name='Republish plate %d "%s" as proxy' % (entity['id'], entity['code']),
        user=user,
        priority=8000,
    )

    log.info('republish_as_proxy scheduled on Qube as %d' % future.job_id)


__sgevents__ = dict(
    type='callback',
    callback_in_subprocess=False,
    callback=callback,
    filter={
        'event_type': 'Shotgun_PublishEvent_Change',
        'attribute_name': 'sg_version',
    },
)




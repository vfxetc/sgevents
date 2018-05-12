import re

from sgsession import Session


def callback(event):

    sg = Session()
    version = sg.merge(event.entity)

    if event.event_type == 'Shotgun_Version_New':
        shot_name, project = version.fetch(('entity.Shot.name', 'project'))

        sg.update('Shot', version['entity']['id'], dict(sg_latest_version=version))

        m = re.match(r'([A-Z]{2})\d+', shot_name)
        if not m:
            print 'Shot name does not match specs.'
            return
        seq_code = m.group(1)
        update_playlist(sg, project, seq_code)

    elif event.event_type == 'Shotgun_Version_Change':

        shot = version.fetch('entity')
        sg.share_thumbnail([shot], source_entity=version, filmstrip_thumbnail=event['attribute_name'] == 'filmstrip_image')

def update_playlist(sg, project, seq_code):

    all_versions = sg.find('Version', [
        ('entity.Shot.sg_sequence.Sequence.code', 'is', seq_code),
        ('project', 'is', project),
    ], [
        'entity.Shot.sg_cut_in',
        'created_at',
    ])
    by_order = {}
    for V in sorted(all_versions, key=lambda V: V['created_at']):
        #V.pprint()
        cut_in = V.get('entity.Shot.sg_cut_in')
        if cut_in is not None:
            by_order[cut_in] = V

    playlist_versions = [x[1] for x in sorted(by_order.items())]
    if not playlist_versions:
        return

    print playlist_versions

    playlist_code = '{} latest'.format(seq_code)
    playlist = sg.find_one('Playlist', [
        ('code', 'is', playlist_code),
        ('project', 'is', project),
    ])
    if playlist:
        sg.update('Playlist', playlist['id'], dict(
            versions=playlist_versions,
        ))
    else:
        playlist = sg.create('Playlist', dict(
            code=playlist_code,
            project=project,
            versions=playlist_versions
        ))
    
    #playlist.pprint()


    
def filter(e):
    if e.event_type == 'Shotgun_Version_New':
        return True
    if e.event_type == 'Shotgun_Version_Change':
        return e.get('attribute_name') in ('image', 'filmstrip_image')


__sgevents__ = dict(
    type='callback',
    callback=callback,
    callback_in_subprocess=False,
    filter=filter,

)


if __name__ == '__main__':

    sg = Session()

    for seq in sg.find('Sequence', ()):
        print seq
        update_playlist(sg, seq['project'], seq['code'][:2])

    for shot in sg.find('Shot', ()):
        version = sg.find_one('Version', [
            ('entity', 'is', shot),
        ], order=[{'field_name':'created_at', 'direction':'desc'}])
        print shot, version
        if version:
            sg.update('Shot', shot['id'], dict(sg_latest_version=version))
            sg.share_thumbnail([shot], source_entity=version, filmstrip_thumbnail=False)
            sg.share_thumbnail([shot], source_entity=version, filmstrip_thumbnail=True)


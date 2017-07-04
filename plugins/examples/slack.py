import requests
import logging
from shotgun_api3 import Shotgun
from sgsession import Session
import json

log = logging.getLogger(__name__)

SLACK_CHANNEL = SLACK_CHANNEL
SLACK_TOKEN = SLACK_TOKEN

def callback(event):
    sg = Session()
    print event['entity']
    if event['project']['id'] != 74:
        return "checking project id is not 74 " + str(event['project']['id'])
    elif event['meta']['new_value'] != 'rev':
        return "checking new value is not rev" +  str(event['meta']['new_value'])
    elif event['event_type'] != "Shotgun_Task_Change":
        return "checking: event['event_type']" +  str(event['event_type'])

    else: 
        seq_link = ""
        task_id = event['entity']['id']
        task = sg.find_one('Task', [('id', 'is', task_id)], ['entity'])
        shot_id = task['entity']['id']
        if 'sg_sequence' in task['entity']: 
            seq_id = task['entity']['sg_sequence']['id']
            print seq_id
            seq_type = task['entity']['sg_sequence']['type']
            print seq_type
            seq_name =task['entity']['sg_sequence']['name']
            print seq_name
            seq_link = '\n<https://markmedia.shotgunstudio.com/detail/Shot/' + str(shot_id) + '|Shot Link> \n<https://markmedia.shotgunstudio.com/detail/Shot/' + str(shot_id) +'#' + str(seq_type) + '_' + str(seq_id) + '_' + str(seq_name) + '|Sequence Link>'
        print "checking else statement"
        print event['project']['id'],  event['meta']['new_value'], event['event_type']
        print "\n"

        requests.get(
            'https://slack.com/api/chat.postMessage',
                params={
                'channel': SLACK_CHANNEL,
                'fallback': 'This is ready for review: '+ str(task['entity']['name']) + '>'  + str(event['entity']['name']),
                'params':  None,
                'attachments': json.dumps([
                                	{'fallback': 'This is ready for review: ' + str(task['entity']['name']) + ' > ' +  str(event['entity']['name']),
                                	 'title': 'This is ready for review: ' + str(task['entity']['name']) + ' > ' +  str(event['entity']['name']),
                                	 'text': '<https://markmedia.shotgunstudio.com/detail/Task/'+str(event['entity']['id']) + '/|'+ str(task['entity']['name']) + ' ' + str(event['entity']['name']) + ">\nProject: " + str(event['project']['name']) + seq_link
                                	   }
                                ]),
                'token': SLACK_TOKEN,
                'username': 'elainew',
                'as_user': True
            }
        )
    

__sgevents__ = {
    'type': 'callback',
    'callback': '%s:callback' % __file__.rstrip('c'),
}

'''
what change
- is it a task? (event object ? event_type > meta (attr name, new value = rev))
- sg_status_list on the task?
- is it interesting for stubbs? (is it rev? )
- if interesting, ping stubbs
'''


'''build/scripts/sgevents-dispatch -p plugins/examples/slack.py outputcopy.json 
on rf40.mm -> python build/scripts/sgevents-daemon -p plugins/examples/slack.py
'''
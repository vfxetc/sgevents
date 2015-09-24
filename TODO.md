
- move sgevents or sgcache loop error handling into sgapi.retry

- have another thread watching the the event loop, making sure that
  it is actually returning periodically

  last event seemed to be:

    2015-09-15.27691.log:2015-09-15 10:14:18,158 INFO     pid:27691 event:2205093 sgcache.events - skipping event; unknown event subtype View


- instrument the event loop to print out what the max last id is

- EventLog.iter_events should skip any events that it has internal errors on
    - This could require a big refactor to turn everything into an iterator.

- ViewEvent.subject_entity
    - Should the page be moved to viewing_entity, or something?
    
- run as user
    - need to run as root
    - fall back to generic user if it is an ApiUser

- log all execution so that it may be displayed in a web browser

- add ability to interact with (failed) events in emails and the web log:
    - button to mark as resolved
    - button to re-dispatch
    - code to copy-paste to terminal to run in your own environment:
      sgevents-dispatch 12345 module:function
 
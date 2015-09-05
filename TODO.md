
- tests
    - ClientLogin_Failed parses okay
    - event specializations work okay
    
- run as user
    - need to run as root
    - fall back to generic user if it is an ApiUser

- qbfutures handler type

- very agressive error handling

- send emails on errors

- log all execution so that it may be displayed in a web browser

- add ability to interact with (failed) events in emails and the web log:
    - button to mark as resolved
    - button to re-dispatch
    - code to copy-paste to terminal to run in your own environment:
      sgevents-dispatch 12345 module:function
 

- create sgevents.dispatcher.{core,context,handler,sandbox}
- create sgevents.daemon


- pull in exception loop from sgcache
- be able to register callbacks in that loop
  - filters, like ShotgunEventDaemon
- be able to filter dev mode by:
  - project
  - user (which requires sudo_as_login to be on)
  - some other filters

- use imp.load_module to load files as modules (so that the autoreloader
  will have an easier time of them); hash their paths into a module name

  $basename_$hash

- plugin registration via directory full of Python files:

  __sgevents__ = {
    # Same data as in YAML below.
  }

  # OR:

  def __sgevents_init__(sge):
      sge.register_callback(**kwargs)
      sge.register_context(**kwargs)


- OR plugin registration via directory full of YAML files:

    type: callback

    # Event attributes to test.
    filter:
      event_type: Shotgun_Publish_Create
      entity.PublishEvent.sg_type: maya_scene

    # Filter function (which is called in the process).
    filter: package.module:filter_
    filter: $HERE/$NAME.py:filter_

    # Extra fields that the filter function wants.
    extra_fields:
      entity.PublishEvent.sg_version

    # Function to run (which is called in a subprocess).
    callback: package.module:handler
    # or
    callback: /path/to/file.py:function # It has a slash, therefore it is to be execfiled
    # or
    callback: $PLUGINS/file.py:function # envvars!

    nonfatal_exceptions:
      - sgevents.loader:NotFoundError

    # Disable default behaviour of running in a subprocess.
    subprocess: false

    ---
    type: context
    filter:
      who.HumanUser.login: /mreid|mboers/
    envvars:
      VEE_EXEC_ARGS: "--dev"

    ---
    type: context
    filter:
      project.Project.id: 66
    envvars:
      VEE_EXEC_ARGS: "--dev"




- plugin takes a context and event. The context has a `shotgun` attribute
  which is set to sudo_as_login if a HumanUser triggered the event.

- convenience method for those functions calls a given function (or string
  pointing to a function) in the environment specified by the filters:

      ctx.call_in_subprocess('module:function', event)

      This runs in much the same way that the qbfutures does.

- log all execution so that it may be displayed in a web browser

- instead of tracking error states of each plugin, we will email/log about it
  and the emails/weblog will have copy-pastable commands to re-run it
  - button to mark as resolved
  - button to re-dispatch
  - code to copy-paste to terminal to run in your own environment:
    sgevents-dispatch 12345 module:function

from sgpublish.republishes import RepublishEventPlugin
from sgpublish import Publisher


plugin = __sgevents_init__ = RepublishEventPlugin(name='republish-looper')


@plugin.register('dev_loop_1', 'dev_loop_2')
def one_to_two(src):

    with Publisher(template=src, type='dev_loop_2'):
        pass

@plugin.register('dev_loop_2', 'dev_loop_1')
def two_to_one(src):

    with Publisher(template=src, type='dev_loop_1'):
        pass



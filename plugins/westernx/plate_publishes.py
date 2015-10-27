from sgpublish.republishes import RepublishEventPlugin

plugin = __sgevents_init__ = RepublishEventPlugin(name='republish_as_proxy')
plugin.register(
    src_types='plate',
    dst_types='plate_proxy',
    src_steps='Online',
    func='kspipeline.edit.plate_publish.core:republish_as_proxy',
)


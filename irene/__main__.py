from irene.brain.brain_plugin import BrainPlugin
from irene.plugin_loader.core_plugins import ConfigPlugin, PluginDiscoveryPlugin
from irene.plugin_loader.core_plugins.logging import LoggingPlugin
from irene.plugin_loader.launcher import launch_application

launch_application(
    [
        ConfigPlugin(template_paths=('{irene_path}/config_templates',)),
        PluginDiscoveryPlugin(),
        LoggingPlugin(),
        BrainPlugin(),
    ],
    canonical_launch_command='python -m irene',
)

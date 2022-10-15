from os import environ
from os.path import dirname

from irene.brain.brain_plugin import BrainPlugin
from irene.compatibility.compatibility_plugin import OriginalCompatibilityPlugin
from irene.plugin_loader.core_plugins import ConfigPlugin, PluginDiscoveryPlugin
from irene.plugin_loader.core_plugins.logging import LoggingPlugin
from irene.plugin_loader.file_patterns import register_variable, substitute_pattern
from irene.plugin_loader.launcher import launch_application

register_variable('irene_path', dirname(__file__))
register_variable('irene_home', environ.get('IRENE_HOME', list(substitute_pattern('{user_home}/irene'))))

launch_application(
    [
        ConfigPlugin(template_paths=('{irene_path}/config_templates',)),
        PluginDiscoveryPlugin(),
        LoggingPlugin(),
        BrainPlugin(),
        OriginalCompatibilityPlugin(),
    ],
    canonical_launch_command='python -m irene',
)

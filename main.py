"""
Biomni Plugin Entry Point
"""

from dify_plugin import Plugin, DifyPluginEnv

def create_plugin():
    """
    Create and configure the Biomni plugin
    """
    plugin = Plugin(DifyPluginEnv())
    
    # The plugin will automatically discover providers and tools
    # based on the file structure and naming conventions
    
    return plugin

if __name__ == "__main__":
    # Run the plugin in development/debugging mode
    create_plugin().run()

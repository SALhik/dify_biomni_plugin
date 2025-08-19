"""
Biomni Plugin Entry Point
"""

from dify_plugin import DifyPlugin


def create_plugin():
    """
    Create and configure the Biomni plugin
    """
    plugin = DifyPlugin()
    return plugin


if __name__ == "__main__":
    # Run the plugin in development/debugging mode
    create_plugin().run()

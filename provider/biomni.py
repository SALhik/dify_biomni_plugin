"""
Biomni Provider Implementation
"""

import logging
from typing import Any, Dict

from dify_plugin.entities.model import AIModelEntity
from dify_plugin.entities.tool import ToolProviderCredentialValidationError
from dify_plugin.interfaces.tool import ToolProvider

logger = logging.getLogger(__name__)


class BiomniProvider(ToolProvider):
    """
    Biomni tool provider for biomedical research tasks
    """
    
    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Validate the credentials for Biomni provider.
        Since Biomni runs locally, we mainly check if the agent is accessible.
        
        Args:
            credentials: The credentials to validate (empty for local agent)
            
        Raises:
            ToolProviderCredentialValidationError: If validation fails
        """
        try:
            # 🔧 CONFIGURE: Add your Biomni agent import and basic validation here
            # Example validation - replace with your actual agent import
            
            # import sys
            # sys.path.append('/path/to/your/biomni')  # Configure your path
            # from your_biomni_module import agent
            
            # Test basic agent availability
            # You might want to do a simple test call here
            # test_result = agent.test_connection()  # If you have such method
            
            logger.info("Biomni agent validation successful")
            
        except ImportError as e:
            logger.error(f"Failed to import Biomni agent: {str(e)}")
            raise ToolProviderCredentialValidationError(
                f"Biomni agent not found or not properly configured: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Biomni agent validation failed: {str(e)}")
            raise ToolProviderCredentialValidationError(
                f"Biomni agent validation failed: {str(e)}"
            )

    def _get_tools(self) -> list:
        """
        Get available tools from this provider
        """
        return ["biomni_agent"]

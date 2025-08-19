"""
Biomni Provider Implementation
"""

import logging
import os
import sys
import importlib
from typing import Any, Dict, Optional

from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from dify_plugin.interfaces.tool import ToolProvider

logger = logging.getLogger(__name__)


# --------------------------
# Tool Provider
# --------------------------
class BiomniProvider(ToolProvider):
    """
    Biomni tool provider for biomedical research tasks
    """

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Validate the credentials for Biomni provider by attempting to import the agent
        configured via environment variables.
        """
        try:
            python_path = os.getenv("BIOMNI_PYTHON_PATH")
            if python_path and python_path not in sys.path:
                sys.path.append(python_path)

            import_expr = os.getenv("BIOMNI_AGENT_IMPORT")
            if import_expr:
                module_path, _, attribute_name = import_expr.partition(":")
                if not module_path:
                    raise ImportError("Invalid BIOMNI_AGENT_IMPORT: module is empty")
                module = importlib.import_module(module_path)
                agent_obj: Optional[Any] = getattr(module, attribute_name) if attribute_name else module
                if callable(agent_obj) and getattr(agent_obj, "__name__", None):
                    agent_obj = agent_obj()
            else:
                try:
                    module = importlib.import_module("biomni")
                    agent_obj = getattr(module, "agent", None)
                    if agent_obj is None and hasattr(module, "BiomniAgent"):
                        agent_obj = getattr(module, "BiomniAgent")()
                except Exception as inner:
                    raise ImportError(str(inner))

            if agent_obj is None:
                raise ImportError("Biomni agent could not be resolved")

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
        Return a list of available tool names from this provider
        """
        return ["biomni_agent"]


# --------------------------
# Tool Implementation
# --------------------------
    

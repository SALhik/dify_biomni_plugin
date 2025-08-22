"""
Biomni Provider Implementation
"""

import logging
import os
from typing import Any, Dict

from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from dify_plugin.interfaces.tool import ToolProvider

logger = logging.getLogger(__name__)


class BiomniProvider(ToolProvider):
    """
    Biomni tool provider for biomedical research tasks
    """

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Validate the credentials and environment for Biomni A1 agent
        """
        try:
            # Check if Biomni can be imported
            from biomni.agent import A1
            from biomni.config import default_config
            
            # Check required API keys based on model selection
            llm_model = os.getenv("BIOMNI_LLM_MODEL", "claude-sonnet-4-20250514")
            
            if "claude" in llm_model.lower():
                if not os.getenv("ANTHROPIC_API_KEY"):
                    raise ToolProviderCredentialValidationError(
                        "ANTHROPIC_API_KEY is required for Claude models"
                    )
            elif "gpt" in llm_model.lower() or "openai" in llm_model.lower():
                if not os.getenv("OPENAI_API_KEY"):
                    raise ToolProviderCredentialValidationError(
                        "OPENAI_API_KEY is required for OpenAI models"
                    )
            elif "gemini" in llm_model.lower():
                if not os.getenv("GEMINI_API_KEY"):
                    raise ToolProviderCredentialValidationError(
                        "GEMINI_API_KEY is required for Gemini models"
                    )
            
            # Validate data path
            data_path = os.getenv("BIOMNI_DATA_PATH", "./data")
            try:
                os.makedirs(data_path, exist_ok=True)
            except Exception as e:
                raise ToolProviderCredentialValidationError(
                    f"Cannot access data path {data_path}: {str(e)}"
                )
            
            # Try to initialize A1 agent (minimal validation without full setup)
            try:
                # Quick validation without full initialization
                default_config.llm = llm_model
                logger.info(f"Biomni A1 agent validation successful with model: {llm_model}")
            except Exception as e:
                raise ToolProviderCredentialValidationError(
                    f"Failed to configure Biomni A1 agent: {str(e)}"
                )

        except ImportError as e:
            logger.error(f"Failed to import Biomni: {str(e)}")
            raise ToolProviderCredentialValidationError(
                "Biomni package not found. Install with: pip install biomni"
            )
        except ToolProviderCredentialValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Biomni validation failed: {str(e)}")
            raise ToolProviderCredentialValidationError(
                f"Biomni validation failed: {str(e)}"
            )

    def _get_tools(self) -> list:
        """
        Return a list of available tool names from this provider
        """
        return ["biomni_agent"]

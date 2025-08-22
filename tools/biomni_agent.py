"""
Biomni Agent Tool Implementation for Dify Plugin
"""

import logging
import os
import time
from typing import Any, Dict, Generator, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)


class BiomniAgentTool(Tool):
    """
    Tool for executing biomedical research tasks using Biomni A1 agent
    """

    def __init__(self):
        super().__init__()
        self.agent: Optional[Any] = None
        self._setup_biomni_agent()

    def _setup_biomni_agent(self) -> None:
        """
        Setup Biomni A1 agent with correct initialization parameters
        """
        try:
            # Import the correct Biomni agent
            from biomni.agent import A1
            from biomni.config import default_config
            
            # Configure Biomni settings
            data_path = os.getenv("BIOMNI_DATA_PATH", "./data")
            llm_model = os.getenv("BIOMNI_LLM_MODEL", "claude-sonnet-4-20250514")
            timeout = int(os.getenv("BIOMNI_TIMEOUT_SECONDS", "600"))
            
            # Set global config (affects all operations)
            default_config.llm = llm_model
            default_config.timeout_seconds = timeout
            
            # Initialize A1 agent with required parameters
            self.agent = A1(path=data_path, llm=llm_model)
            
            logger.info(f"Biomni A1 agent initialized successfully with model: {llm_model}")

        except ImportError as e:
            logger.error(f"Failed to import Biomni A1 agent: {str(e)}")
            logger.error("Make sure Biomni is installed: pip install biomni")
            self.agent = None
        except Exception as e:
            logger.error(f"Error setting up Biomni A1 agent: {str(e)}")
            self.agent = None

    def _invoke(
        self,
        user_id: str,
        tool_parameters: Dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the Biomni A1 agent with the given parameters
        """

        research_query = tool_parameters.get("research_query", "").strip()
        max_execution_time = int(tool_parameters.get("max_execution_time", 600) or 600)
        include_citations = bool(tool_parameters.get("include_citations", True))

        if not research_query:
            yield self.create_text_message("❌ **Error**: Please provide a research query")
            return

        if self.agent is None:
            yield self.create_text_message(
                "❌ **Error**: Biomni A1 agent is not properly configured.\n\n"
                "**Setup Requirements**:\n"
                "1. Install Biomni: `pip install biomni`\n"
                "2. Set required API keys (ANTHROPIC_API_KEY, etc.)\n"
                "3. Ensure sufficient disk space (~11GB for data lake)\n"
                "4. Configure environment variables:\n"
                "   - BIOMNI_DATA_PATH (default: ./data)\n"
                "   - BIOMNI_LLM_MODEL (default: claude-sonnet-4-20250514)\n"
                "   - ANTHROPIC_API_KEY (required for Claude models)"
            )
            return

        try:
            yield self.create_text_message(
                f"🧬 **Biomni A1 Agent Started**\n\n"
                f"**Query**: {research_query[:200]}{'...' if len(research_query) > 200 else ''}\n"
                f"**Max Time**: {max_execution_time} seconds\n"
                f"**Citations**: {'Enabled' if include_citations else 'Disabled'}\n\n"
                f"⏳ **Status**: Processing biomedical research query...\n"
                f"📥 **Note**: First run may take longer due to data lake download (~11GB)"
            )

            start_time = time.time()

            # Call the Biomni A1 agent using the correct .go() method
            result = self.agent.go(research_query)

            execution_time = time.time() - start_time

            if execution_time > max_execution_time:
                yield self.create_text_message(
                    f"⚠️ **Warning**: Execution took {execution_time:.1f} seconds (limit {max_execution_time} seconds)"
                )

            yield self.create_text_message(
                f"✅ **Biomni A1 Analysis Complete**\n\n"
                f"**Query**: {research_query}\n\n"
                f"**Execution Time**: {execution_time:.1f} seconds\n\n"
                f"**Results**:\n\n{self._format_result(result, include_citations)}"
            )

            logger.info(f"Biomni A1 agent completed successfully for user {user_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Biomni A1 agent error for user {user_id}: {error_msg}")

            # Provide specific troubleshooting for common Biomni issues
            troubleshooting = self._get_troubleshooting_tips(error_msg)

            yield self.create_text_message(
                f"❌ **Biomni A1 Agent Error**\n\n"
                f"**Error**: {error_msg}\n"
                f"**Query**: {research_query}\n\n"
                f"**Troubleshooting Tips**:\n{troubleshooting}"
            )

    def _get_troubleshooting_tips(self, error_msg: str) -> str:
        """
        Provide specific troubleshooting tips based on error message
        """
        if "API" in error_msg or "key" in error_msg.lower():
            return (
                "• Check API key configuration:\n"
                "  - ANTHROPIC_API_KEY for Claude models\n"
                "  - OPENAI_API_KEY for GPT models\n"
                "  - Other provider keys as needed\n"
                "• Ensure API keys are valid and have sufficient credits"
            )
        elif "data" in error_msg.lower() or "path" in error_msg.lower():
            return (
                "• Check data path configuration (BIOMNI_DATA_PATH)\n"
                "• Ensure sufficient disk space (~11GB for data lake)\n"
                "• Verify read/write permissions for data directory\n"
                "• Allow time for initial data lake download"
            )
        elif "timeout" in error_msg.lower():
            return (
                "• Increase BIOMNI_TIMEOUT_SECONDS environment variable\n"
                "• Complex biomedical analyses may require more time\n"
                "• Consider breaking down complex queries into parts"
            )
        else:
            return (
                "• Ensure Biomni is properly installed: pip install biomni\n"
                "• Check environment setup following Biomni documentation\n"
                "• Verify all required dependencies are installed\n"
                "• Check the logs for more detailed error information"
            )

    def _format_result(self, result: Any, include_citations: bool = True) -> str:
        """
        Format the result from Biomni A1 agent for display
        
        Note: Biomni A1 returns results as strings, but may contain structured information
        """
        try:
            if isinstance(result, str):
                # Biomni A1 typically returns string results
                return result
            elif isinstance(result, dict):
                # Handle structured results if present
                formatted_result = ""
                
                if "analysis" in result:
                    formatted_result += f"**Analysis**:\n{result['analysis']}\n\n"
                if "conclusions" in result:
                    formatted_result += f"**Conclusions**:\n{result['conclusions']}\n\n"
                if "recommendations" in result:
                    formatted_result += f"**Recommendations**:\n{result['recommendations']}\n\n"
                if include_citations and "references" in result:
                    formatted_result += f"**References**:\n{result['references']}\n\n"
                    
                return formatted_result or str(result)
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            return f"Result: {str(result)}"

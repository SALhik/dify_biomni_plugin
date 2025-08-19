"""
Biomni Agent Tool Implementation
"""

import logging
import os
import sys
import time
import importlib
import inspect
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, Generator, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)


class BiomniAgentTool(Tool):
    """
    Tool for executing biomedical research tasks using Biomni agent
    """

    def __init__(self):
        super().__init__()
        self.agent: Optional[Any] = None
        self.agent_method_name: str = os.getenv("BIOMNI_AGENT_METHOD", "go")
        self._setup_biomni_agent()

    def _import_from_string(self, import_path: str) -> Any:
        """
        Import an object from a string in the form 'package.module:attribute'.
        """
        module_path, _, attribute_name = import_path.partition(":")
        if not module_path:
            raise ImportError("Invalid import path: module is empty")
        module = importlib.import_module(module_path)
        return getattr(module, attribute_name) if attribute_name else module

    def _setup_biomni_agent(self) -> None:
        """
        Setup and import the Biomni agent using environment variables for flexibility.
        - BIOMNI_PYTHON_PATH: Optional sys.path entry to locate Biomni source
        - BIOMNI_AGENT_IMPORT: Import path like 'biomni.agent:agent' or 'biomni:BiomniAgent'
        - BIOMNI_AGENT_METHOD: Method on the agent to invoke (default: 'go')
        """
        try:
            python_path = os.getenv("BIOMNI_PYTHON_PATH")
            if python_path and python_path not in sys.path:
                sys.path.append(python_path)

            import_expr = os.getenv("BIOMNI_AGENT_IMPORT")
            if import_expr:
                imported_obj = self._import_from_string(import_expr)
                # If the imported object is a class, instantiate it; if it's an instance, use as-is
                self.agent = imported_obj() if inspect.isclass(imported_obj) else imported_obj
            else:
                # Best-effort default import if Biomni is installed as a package
                try:
                    module = importlib.import_module("biomni")
                    # Prefer a top-level 'agent' attribute; else attempt to construct a default agent class if present
                    self.agent = getattr(module, "agent", None)
                    if self.agent is None and hasattr(module, "BiomniAgent"):
                        self.agent = getattr(module, "BiomniAgent")()
                except Exception:
                    # Leave self.agent as None; handled below
                    self.agent = None

            if self.agent is None:
                logger.warning("Biomni agent is not configured (set BIOMNI_AGENT_IMPORT or ensure package is importable)")
            else:
                logger.info("Biomni agent setup completed")

        except ImportError as e:
            logger.error(f"Failed to import Biomni agent: {str(e)}")
            self.agent = None
        except Exception as e:
            logger.error(f"Error setting up Biomni agent: {str(e)}")
            self.agent = None

    def _invoke(
        self,
        user_id: str,
        tool_parameters: Dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the Biomni agent with the given parameters

        Args:
            user_id: The ID of the user invoking the tool
            tool_parameters: Parameters for the tool execution

        Yields:
            ToolInvokeMessage: Messages representing the tool execution progress and results
        """

        research_query = tool_parameters.get("research_query", "").strip()
        max_execution_time = int(tool_parameters.get("max_execution_time", 600) or 600)

        def _to_bool(value: Any, default: bool = True) -> bool:
            if isinstance(value, bool):
                return value
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                v = value.strip().lower()
                if v in {"true", "1", "yes", "y", "on"}:
                    return True
                if v in {"false", "0", "no", "n", "off"}:
                    return False
            return default

        include_citations = _to_bool(tool_parameters.get("include_citations"), True)

        if not research_query:
            yield self.create_text_message("❌ **Error**: Please provide a research query")
            return

        if self.agent is None:
            yield self.create_text_message(
                "❌ **Error**: Biomni agent is not properly configured. "
                "Set BIOMNI_AGENT_IMPORT or ensure the Biomni package is installed."
            )
            return

        try:
            yield self.create_text_message(
                f"🧬 **Biomni Agent Started**\n\n"
                f"**Query**: {research_query[:200]}{'...' if len(research_query) > 200 else ''}\n"
                f"**Max Time**: {max_execution_time} seconds\n"
                f"**Citations**: {'Enabled' if include_citations else 'Disabled'}\n\n"
                f"⏳ **Status**: Processing your biomedical research query..."
            )

            start_time = time.time()

            # Determine callable method to execute
            method_name = self.agent_method_name
            if not hasattr(self.agent, method_name):
                # Try a few common fallbacks if custom method not found
                for candidate in ("go", "run", "process_query", "__call__"):
                    if hasattr(self.agent, candidate):
                        method_name = candidate
                        break
                else:
                    raise AttributeError(
                        "Agent method not found. Set BIOMNI_AGENT_METHOD or expose one of: go, run, process_query, __call__."
                    )

            agent_callable = getattr(self.agent, method_name)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(agent_callable, research_query)
                try:
                    result = future.result(timeout=max_execution_time)
                except FuturesTimeoutError:
                    yield self.create_text_message(
                        f"⏰ **Timeout**: The analysis exceeded the maximum execution time of {max_execution_time} seconds. "
                        f"Try breaking down your query into smaller parts or increasing the timeout limit."
                    )
                    return

            execution_time = time.time() - start_time

            if execution_time > max_execution_time:
                yield self.create_text_message(
                    f"⚠️ **Warning**: Execution took {execution_time:.1f} seconds (limit {max_execution_time} seconds)"
                )

            yield self.create_text_message(
                f"✅ **Biomni Analysis Complete**\n\n"
                f"**Query**: {research_query}\n\n"
                f"**Execution Time**: {execution_time:.1f} seconds\n\n"
                f"**Results**:\n\n{self._format_result(result, include_citations)}"
            )

            logger.info(f"Biomni agent completed successfully for user {user_id}")

        except TimeoutError:
            yield self.create_text_message(
                f"⏰ **Timeout**: The analysis exceeded the maximum execution time of {max_execution_time} seconds. "
                f"Try breaking down your query into smaller parts or increasing the timeout limit."
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Biomni agent error for user {user_id}: {error_msg}")

            yield self.create_text_message(
                f"❌ **Biomni Agent Error**\n\n"
                f"**Error**: {error_msg}\n"
                f"**Query**: {research_query}\n\n"
                f"**Troubleshooting Tips**:\n"
                f"• Check if your query is properly formatted\n"
                f"• Ensure the Biomni agent is running and accessible\n"
                f"• Set BIOMNI_AGENT_IMPORT and BIOMNI_AGENT_METHOD appropriately\n"
                f"• Check the logs for more detailed error information"
            )

    def _format_result(self, result: Any, include_citations: bool = True) -> str:
        """
        Format the result from Biomni agent for display.

        Args:
            result: The result from Biomni agent
            include_citations: Whether to include citations in the output

        Returns:
            str: Formatted result string
        """
        try:
            if isinstance(result, dict):
                formatted_result = ""

                if "analysis" in result:
                    formatted_result += f"**Analysis**:\n{result['analysis']}\n\n"

                if "conclusions" in result:
                    formatted_result += f"**Conclusions**:\n{result['conclusions']}\n\n"

                if "recommendations" in result:
                    formatted_result += f"**Recommendations**:\n{result['recommendations']}\n\n"

                if include_citations and "references" in result:
                    formatted_result += f"**References**:\n{result['references']}\n\n"

                if not formatted_result:
                    formatted_result = str(result)

                return formatted_result

            if isinstance(result, str):
                return result

            return str(result)

        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            return f"Result: {str(result)}"

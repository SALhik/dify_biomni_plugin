"""
Biomni Agent Tool Implementation
"""

import logging
import sys
import time
from typing import Any, Dict, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)


class BiomniAgentTool(Tool):
    """
    Tool for executing biomedical research tasks using Biomni agent
    """
    
    def __init__(self):
        super().__init__()
        self._setup_biomni_agent()
    
    def _setup_biomni_agent(self):
        """
        Setup and import the Biomni agent
        🔧 CONFIGURE: Modify this method to properly import your Biomni agent
        """
        try:
            # 🔧 CONFIGURE: Add the path to your Biomni installation
            # Example: sys.path.append('/home/user/biomni')
            # sys.path.append('/path/to/your/biomni')
            
            # 🔧 CONFIGURE: Import your actual Biomni agent
            # Example imports (replace with your actual imports):
            # from biomni import BiomniAgent
            # self.agent = BiomniAgent()
            
            # OR if you have a global agent instance:
            # from your_biomni_module import agent
            # self.agent = agent
            
            # Temporary placeholder - replace with actual import
            self.agent = None
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
        
        # Extract parameters
        research_query = tool_parameters.get('research_query', '').strip()
        max_execution_time = tool_parameters.get('max_execution_time', 600)
        include_citations = tool_parameters.get('include_citations', True)
        
        # Validate input
        if not research_query:
            yield self.create_text_message("❌ **Error**: Please provide a research query")
            return
        
        # Check if agent is available
        if self.agent is None:
            yield self.create_text_message(
                "❌ **Error**: Biomni agent is not properly configured. "
                "Please check the installation and configuration."
            )
            return
        
        try:
            # Send initial status message
            yield self.create_text_message(
                f"🧬 **Biomni Agent Started**\n\n"
                f"**Query**: {research_query[:200]}{'...' if len(research_query) > 200 else ''}\n"
                f"**Max Time**: {max_execution_time} seconds\n"
                f"**Citations**: {'Enabled' if include_citations else 'Disabled'}\n\n"
                f"⏳ **Status**: Processing your biomedical research query..."
            )
            
            # Record start time for timeout handling
            start_time = time.time()
            
            # 🔧 CONFIGURE: Replace this with your actual agent call
            # The exact method name might be different - check your Biomni documentation
            
            # Example calls (replace with your actual method):
            # result = self.agent.go(research_query)
            # OR
            # result = self.agent.process_query(research_query)
            # OR 
            # result = self.agent.run(research_query)
            
            # For now, using a placeholder - REPLACE THIS:
            if hasattr(self.agent, 'go'):
                result = self.agent.go(research_query)
            else:
                # Fallback - replace with your actual method
                raise AttributeError("Agent method not found. Please configure the correct method call.")
            
            # Check execution time
            execution_time = time.time() - start_time
            
            # Format the result message
            if execution_time > max_execution_time:
                yield self.create_text_message(
                    f"⚠️ **Warning**: Execution took {execution_time:.1f} seconds "
                    f"(exceeded limit of {max_execution_time} seconds)"
                )
            
            # Send success result
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
                f"• Try simplifying your research question\n"
                f"• Check the logs for more detailed error information"
            )
    
    def _format_result(self, result: Any, include_citations: bool = True) -> str:
        """
        Format the result from Biomni agent for display
        🔧 CONFIGURE: Customize this method based on your agent's output format
        
        Args:
            result: The result from Biomni agent
            include_citations: Whether to include citations in the output
            
        Returns:
            str: Formatted result string
        """
        try:
            # 🔧 CONFIGURE: Customize result formatting based on your agent's output
            
            if isinstance(result, dict):
                # If result is a dictionary, format it nicely
                formatted_result = ""
                
                # Common fields you might want to extract and format
                if 'analysis' in result:
                    formatted_result += f"**Analysis**:\n{result['analysis']}\n\n"
                
                if 'conclusions' in result:
                    formatted_result += f"**Conclusions**:\n{result['conclusions']}\n\n"
                
                if 'recommendations' in result:
                    formatted_result += f"**Recommendations**:\n{result['recommendations']}\n\n"
                
                if include_citations and 'references' in result:
                    formatted_result += f"**References**:\n{result['references']}\n\n"
                
                # If no specific fields found, just stringify the dict
                if not formatted_result:
                    formatted_result = str(result)
                    
                return formatted_result
                
            elif isinstance(result, str):
                # If result is already a string, return as-is
                return result
                
            else:
                # For other types, convert to string
                return str(result)
                
        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            return f"Result: {str(result)}"

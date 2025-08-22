"""
Biomni Agent Tool Implementation with Subprocess Support
"""

import logging
import os
import sys
import time
import subprocess
import json
import tempfile
from typing import Any, Dict, Generator, Optional
from pathlib import Path

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)


class BiomniAgentTool(Tool):
    """
    Tool for executing biomedical research tasks using Biomni A1 agent
    Uses subprocess execution to avoid gevent/trio conflicts
    """

    def __init__(self, runtime=None, session=None):
        super().__init__(runtime=runtime, session=session)
        self.agent: Optional[Any] = None
        self.use_subprocess = True  # Default to subprocess mode
        self._setup_biomni_agent()

    def _setup_biomni_agent(self) -> None:
        """
        Setup Biomni agent with conflict detection and subprocess fallback
        """
        try:
            # Check if we should force subprocess mode
            force_subprocess = os.getenv("BIOMNI_USE_SUBPROCESS", "true").lower() == "true"
            
            if not force_subprocess:
                # Try direct import first
                try:
                    self._test_direct_import()
                    from biomni.agent import A1
                    from biomni.config import default_config
                    
                    llm_model = os.getenv('BIOMNI_LLM_MODEL', 'claude-sonnet-4-20250514')
                    data_path = os.getenv('BIOMNI_DATA_PATH', './data')
                    
                    default_config.llm = llm_model
                    self.agent = A1(path=data_path, llm=llm_model)
                    self.use_subprocess = False
                    
                    logger.info("Biomni agent initialized in direct mode")
                    return
                    
                except Exception as e:
                    logger.warning(f"Direct import failed, falling back to subprocess: {e}")
            
            # Use subprocess mode
            self.use_subprocess = True
            self.agent = None
            
            # Verify subprocess mode works
            if self._test_subprocess_mode():
                logger.info("Biomni agent configured for subprocess mode")
            else:
                logger.error("Subprocess mode test failed")
                raise RuntimeError("Biomni subprocess mode not working")

        except Exception as e:
            logger.error(f"Error setting up Biomni agent: {str(e)}")
            self.agent = None
            self.use_subprocess = False

    def _test_direct_import(self) -> bool:
        """Test if Biomni can be imported directly without conflicts"""
        try:
            # Quick import test
            import importlib
            spec = importlib.util.find_spec("biomni.agent")
            if spec is None:
                raise ImportError("Biomni not installed")
            
            from biomni.agent import A1
            from biomni.config import default_config
            
            # Quick initialization test (don't actually create agent)
            logger.info("Direct import test successful")
            return True
            
        except Exception as e:
            logger.warning(f"Direct import test failed: {e}")
            return False

    def _test_subprocess_mode(self) -> bool:
        """Test if subprocess mode works"""
        try:
            test_script = '''
import sys
try:
    from biomni.agent import A1
    print("SUBPROCESS_TEST_SUCCESS")
    sys.exit(0)
except Exception as e:
    print(f"SUBPROCESS_TEST_ERROR: {e}")
    sys.exit(1)
'''
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = "SUBPROCESS_TEST_SUCCESS" in result.stdout
            if not success:
                logger.error(f"Subprocess test failed: {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.error(f"Subprocess test exception: {e}")
            return False

    def _invoke(
        self,
        user_id: str,
        tool_parameters: Dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the Biomni agent with the given parameters
        """

        research_query = tool_parameters.get("research_query", "").strip()
        max_execution_time = int(tool_parameters.get("max_execution_time", 600) or 600)
        include_citations = bool(tool_parameters.get("include_citations", True))

        if not research_query:
            yield self.create_text_message("❌ **Error**: Please provide a research query")
            return

        # Check if Biomni is available
        if not self.use_subprocess and self.agent is None:
            yield self.create_text_message(
                "❌ **Error**: Biomni agent is not properly configured.\n\n"
                "**Setup Requirements**:\n"
                "1. Install Biomni: `pip install biomni`\n"
                "2. Set API keys (ANTHROPIC_API_KEY, etc.)\n"
                "3. Configure environment variables\n"
                "4. Ensure sufficient disk space (~11GB for data lake)"
            )
            return

        try:
            yield self.create_text_message(
                f"🧬 **Biomni A1 Agent Started**\n\n"
                f"**Query**: {research_query[:200]}{'...' if len(research_query) > 200 else ''}\n"
                f"**Mode**: {'Subprocess' if self.use_subprocess else 'Direct'}\n"
                f"**Max Time**: {max_execution_time} seconds\n"
                f"**Citations**: {'Enabled' if include_citations else 'Disabled'}\n\n"
                f"⏳ **Status**: Processing biomedical research query...\n"
                f"📥 **Note**: First run may take longer due to data lake download (~11GB)"
            )

            start_time = time.time()

            # Execute query based on mode
            if self.use_subprocess:
                result = self._execute_subprocess_query(research_query, max_execution_time)
            else:
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

            logger.info(f"Biomni agent completed successfully for user {user_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Biomni agent error for user {user_id}: {error_msg}")

            # Provide specific troubleshooting
            troubleshooting = self._get_troubleshooting_tips(error_msg)

            yield self.create_text_message(
                f"❌ **Biomni A1 Agent Error**\n\n"
                f"**Error**: {error_msg}\n"
                f"**Query**: {research_query}\n\n"
                f"**Troubleshooting Tips**:\n{troubleshooting}"
            )

    def _execute_subprocess_query(self, query: str, timeout: int) -> str:
        """Execute Biomni query in subprocess to avoid gevent conflicts"""
        
        # Prepare environment variables
        env_vars = os.environ.copy()
        required_vars = {
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
            'BIOMNI_DATA_PATH': os.getenv('BIOMNI_DATA_PATH', './data'),
            'BIOMNI_LLM_MODEL': os.getenv('BIOMNI_LLM_MODEL', 'claude-sonnet-4-20250514'),
        }
        
        # Only set non-empty values
        for key, value in required_vars.items():
            if value:
                env_vars[key] = value
        
        escaped_query = query.replace('"""', '\\"""')
        
        # Create subprocess script
        script = f'''
import os
import sys
import json

try:
    from biomni.agent import A1
    from biomni.config import default_config
    
    # Configuration
    llm_model = os.getenv("BIOMNI_LLM_MODEL", "claude-sonnet-4-20250514")
    data_path = os.getenv("BIOMNI_DATA_PATH", "./data")
    
    # Set global config
    default_config.llm = llm_model
    default_config.timeout_seconds = {timeout}
    
    # Initialize agent
    agent = A1(path=data_path, llm=llm_model)
    
    # Execute query
    result = agent.go("""{escaped_query}""")
    
    # Return result as JSON
    output = {{
        "success": True,
        "result": str(result),
        "model": llm_model
    }}
    
    print("BIOMNI_RESULT_START")
    print(json.dumps(output))
    print("BIOMNI_RESULT_END")
    
except Exception as e:
    import traceback
    error_output = {{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    
    print("BIOMNI_ERROR_START")
    print(json.dumps(error_output))
    print("BIOMNI_ERROR_END")
    sys.exit(1)
'''
        
        try:
            # Execute subprocess
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env_vars
            )
            
            # Parse output
            output = result.stdout
            error_output = result.stderr
            
            if result.returncode != 0:
                # Try to extract error information
                if "BIOMNI_ERROR_START" in output and "BIOMNI_ERROR_END" in output:
                    start_idx = output.find("BIOMNI_ERROR_START") + len("BIOMNI_ERROR_START")
                    end_idx = output.find("BIOMNI_ERROR_END")
                    error_json = output[start_idx:end_idx].strip()
                    
                    try:
                        error_data = json.loads(error_json)
                        raise RuntimeError(f"Biomni subprocess error: {error_data.get('error', 'Unknown error')}")
                    except json.JSONDecodeError:
                        pass
                
                raise RuntimeError(f"Subprocess failed with return code {result.returncode}: {error_output}")
            
            # Extract successful result
            if "BIOMNI_RESULT_START" in output and "BIOMNI_RESULT_END" in output:
                start_idx = output.find("BIOMNI_RESULT_START") + len("BIOMNI_RESULT_START")
                end_idx = output.find("BIOMNI_RESULT_END")
                result_json = output[start_idx:end_idx].strip()
                
                try:
                    result_data = json.loads(result_json)
                    if result_data.get("success"):
                        return result_data.get("result", "No result returned")
                    else:
                        raise RuntimeError(f"Biomni execution failed: {result_data.get('error', 'Unknown error')}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON result: {e}")
                    return result_json  # Return raw result
            
            # Fallback to raw output
            return output if output.strip() else "No output returned"
                
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Biomni query timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Subprocess execution failed: {e}")

    def _get_troubleshooting_tips(self, error_msg: str) -> str:
        """Provide specific troubleshooting tips based on error message"""
        if "api" in error_msg.lower() or "key" in error_msg.lower():
            return (
                "• Check API key configuration:\n"
                "  - ANTHROPIC_API_KEY for Claude models\n"
                "  - OPENAI_API_KEY for GPT models\n"
                "  - Ensure keys are valid and have credits"
            )
        elif "subprocess" in error_msg.lower():
            return (
                "• Subprocess execution issue:\n"
                "  - Check if Biomni is installed: pip install biomni\n"
                "  - Verify Python environment permissions\n"
                "  - Ensure sufficient system resources"
            )
        elif "timeout" in error_msg.lower():
            return (
                "• Increase timeout settings:\n"
                "  - Set max_execution_time to higher value\n"
                "  - Complex biomedical analyses need more time\n"
                "  - First run downloads ~11GB data lake"
            )
        elif "data" in error_msg.lower() or "path" in error_msg.lower():
            return (
                "• Data path issues:\n"
                "  - Check BIOMNI_DATA_PATH configuration\n"
                "  - Ensure ~11GB free disk space\n"
                "  - Verify read/write permissions"
            )
        else:
            return (
                "• General troubleshooting:\n"
                "  - Ensure biomni_e1 conda environment is active\n"
                "  - Check system resources (memory, disk space)\n"
                "  - Review logs for detailed error information\n"
                "  - Try setting BIOMNI_USE_SUBPROCESS=true"
            )

    def _format_result(self, result: Any, include_citations: bool = True) -> str:
        """Format the result from Biomni A1 agent for display"""
        try:
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
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

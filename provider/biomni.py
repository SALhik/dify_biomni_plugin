"""
Biomni Provider Implementation with Improved Conflict Handling
"""

import logging
import os
import subprocess
import sys
from typing import Any, Dict

from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from dify_plugin.interfaces.tool import ToolProvider

logger = logging.getLogger(__name__)


class BiomniProvider(ToolProvider):
    """
    Biomni tool provider for biomedical research tasks with gevent/trio conflict handling
    """

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Validate the credentials and environment for Biomni A1 agent
        Uses subprocess validation to avoid gevent/trio conflicts
        """
        try:
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
            
            # Use subprocess validation to avoid gevent/trio conflicts
            self._validate_biomni_subprocess()
            
            logger.info(f"Biomni A1 agent validation successful with model: {llm_model}")

        except ToolProviderCredentialValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Biomni validation failed: {str(e)}")
            raise ToolProviderCredentialValidationError(
                f"Biomni validation failed: {str(e)}"
            )

    def _validate_biomni_subprocess(self) -> None:
        """
        Validate Biomni using subprocess to avoid gevent/trio conflicts
        """
        validation_script = '''
import sys
import os
import json

try:
    # Test import
    from biomni.agent import A1
    from biomni.config import default_config
    
    # Test configuration
    llm_model = os.getenv("BIOMNI_LLM_MODEL", "claude-sonnet-4-20250514")
    data_path = os.getenv("BIOMNI_DATA_PATH", "./data")
    
    # Verify data path
    os.makedirs(data_path, exist_ok=True)
    
    # Test basic configuration (don't initialize full agent)
    default_config.llm = llm_model
    
    result = {
        "success": True,
        "message": "Biomni validation successful",
        "model": llm_model,
        "data_path": data_path
    }
    
    print("VALIDATION_SUCCESS")
    print(json.dumps(result))
    
except ImportError as e:
    error = {
        "success": False,
        "error": "ImportError",
        "message": f"Biomni not installed or accessible: {str(e)}",
        "fix": "Install with: pip install biomni"
    }
    print("VALIDATION_ERROR")
    print(json.dumps(error))
    sys.exit(1)
    
except Exception as e:
    error = {
        "success": False,
        "error": type(e).__name__,
        "message": str(e),
        "fix": "Check configuration and environment setup"
    }
    print("VALIDATION_ERROR") 
    print(json.dumps(error))
    sys.exit(1)
'''
        
        try:
            # Prepare environment variables
            env_vars = os.environ.copy()
            
            # Execute validation script
            result = subprocess.run(
                [sys.executable, '-c', validation_script],
                capture_output=True,
                text=True,
                timeout=60,
                env=env_vars
            )
            
            if result.returncode != 0:
                # Parse error from subprocess
                output = result.stdout
                stderr = result.stderr
                
                if "VALIDATION_ERROR" in output:
                    try:
                        lines = output.split('\n')
                        error_line = None
                        for i, line in enumerate(lines):
                            if "VALIDATION_ERROR" in line and i + 1 < len(lines):
                                error_line = lines[i + 1].strip()
                                break
                        
                        if error_line:
                            error_data = json.loads(error_line)
                        
                        error_msg = error_data.get("message", "Unknown validation error")
                        fix_msg = error_data.get("fix", "")
                        
                        raise ToolProviderCredentialValidationError(
                            f"{error_msg}. {fix_msg}"
                        )
                    except (json.JSONDecodeError, IndexError) as parse_error:
                        logger.warning(f"Failed to parse error JSON: {parse_error}")
                
                # Fallback error message with more context
                error_details = f"stdout: {output[:500]}, stderr: {stderr[:500]}" if (output or stderr) else "No output"
                raise ToolProviderCredentialValidationError(
                    f"Biomni validation failed. {error_details}"
                )
            
            # Success - parse result if available
            if result.returncode == 0:
                output = result.stdout
                if "VALIDATION_SUCCESS" in output:
                    try:
                        lines = output.split('\n')
                        success_line = None
                        for i, line in enumerate(lines):
                            if "VALIDATION_SUCCESS" in line and i + 1 < len(lines):
                                success_line = lines[i + 1].strip()
                                break
                        
                        if success_line:
                            success_data = json.loads(success_line)
                            logger.info(f"Biomni validation: {success_data}")
                        else:
                            logger.info("Biomni validation successful (no details)")
                    except (json.JSONDecodeError, IndexError) as parse_error:
                        logger.info(f"Biomni validation successful, parse warning: {parse_error}")
                else:
                    logger.info("Biomni validation completed successfully")
                    
        except subprocess.TimeoutExpired:
            raise ToolProviderCredentialValidationError(
                "Biomni validation timed out. Check installation and dependencies."
            )
        except FileNotFoundError:
            raise ToolProviderCredentialValidationError(
                "Python executable not found. Check environment setup."
            )
        except Exception as e:
            raise ToolProviderCredentialValidationError(
                f"Subprocess validation failed: {str(e)}"
            )

    def _get_tools(self) -> list:
        """
        Return a list of available tool names from this provider
        """
        return ["biomni_agent"]

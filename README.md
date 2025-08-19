# Biomni Dify Plugin - Complete Setup Guide

## 📁 Project Structure

Create this exact folder structure:

```
biomni_plugin/
├── manifest.json                 # Plugin manifest
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
├── _assets/
│   └── biomni_icon.png         # Plugin icon (add your icon here)
├── provider/
│   ├── __init__.py             # Empty file
│   ├── biomni.yaml             # Provider config
│   └── biomni.py               # Provider implementation
└── tools/
    ├── __init__.py             # Empty file
    ├── biomni_agent.yaml       # Tool config
    └── biomni_agent.py         # Tool implementation
```

## 🔧 Configuration Steps

### Step 1: Update Plugin Metadata
In **ALL** these files, replace `your-name` with your actual name:
- `provider/biomni.yaml`
- `tools/biomni_agent.yaml` 
- `manifest.json`

### Step 2: Add Your Icon
- Create or find a PNG icon for Biomni (recommended size: 256x256px)
- Place it at `_assets/biomni_icon.png`

### Step 3: Configure Biomni Agent Import
In `tools/biomni_agent.py`, update the `_setup_biomni_agent()` method:

```python
def _setup_biomni_agent(self):
    try:
        # 🔧 CONFIGURE: Update this path to your Biomni installation
        sys.path.append('/path/to/your/biomni')  # Change this path
        
        # 🔧 CONFIGURE: Update this import based on your Biomni structure
        # Option 1: If you have a global agent instance
        from your_biomni_module import agent
        self.agent = agent
        
        # Option 2: If you need to create an agent instance
        # from biomni import BiomniAgent
        # self.agent = BiomniAgent()
        
        # Option 3: If you have a different setup
        # import your_biomni_setup
        # self.agent = your_biomni_setup.create_agent()
        
        logger.info("Biomni agent setup completed")
    except Exception as e:
        logger.error(f"Error setting up Biomni agent: {str(e)}")
        self.agent = None
```

### Step 4: Configure Agent Method Call
In `tools/biomni_agent.py`, update the `_invoke()` method to use your agent's method:

```python
# Replace this section with your actual agent call:
if hasattr(self.agent, 'go'):
    result = self.agent.go(research_query)
else:
    # Update with your agent's actual method name:
    # result = self.agent.process_query(research_query)
    # result = self.agent.run(research_query)  
    # result = self.agent.analyze(research_query)
    raise AttributeError("Agent method not found. Please configure the correct method call.")
```

### Step 5: Configure Result Formatting (Optional)
In `tools/biomni_agent.py`, customize the `_format_result()` method based on your agent's output format.

### Step 6: Update Dependencies
In `requirements.txt`, add all dependencies your Biomni agent needs.

### Step 7: Create Empty __init__.py Files
Create empty `__init__.py` files:
```bash
touch provider/__init__.py
touch tools/__init__.py
```

## 🚀 Development and Testing

### Step 1: Install Dify CLI Tool
Download the Dify plugin CLI tool:
```bash
# Download from Dify's GitHub releases or documentation
# Follow Dify's official installation guide for the CLI tool
```

### Step 2: Set Up Development Environment
```bash
cd biomni_plugin
cp .env.example .env

# Get remote debugging credentials from your Dify instance:
# 1. Go to Dify admin panel → Plugin Management
# 2. Click "Get Debugging Key" 
# 3. Copy the host, port, and key values
# 4. Update your .env file with these values
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Test the Plugin Locally
```bash
# Run in development mode
python main.py

# Or use the CLI tool for debugging
dify plugin dev
```

### Step 5: Remote Debugging
With your `.env` file configured:
```bash
python -m main
```

You should see the plugin appear in your Dify workspace for testing.

## 📦 Packaging the Plugin

### Method 1: Using Dify CLI Tool (Recommended)
```bash
# In your plugin directory
dify plugin build

# This creates biomni.difypkg file
```

### Method 2: Manual Packaging
If CLI tool isn't available:
```bash
# Create a zip file with all plugin contents
zip -r biomni.difypkg \
    manifest.json \
    main.py \
    requirements.txt \
    _assets/ \
    provider/ \
    tools/

# Note: Don't include .env, __pycache__, or other development files
```

## 🔍 Testing Your Plugin

### Unit Testing
Create a simple test script:

```python
# test_plugin.py
import sys
sys.path.append('/path/to/your/biomni')

def test_agent_import():
    """Test if your agent can be imported"""
    try:
        # Use your actual import
        from your_biomni_module import agent
        print("✅ Agent import successful")
        return True
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        return False

def test_agent_call():
    """Test if your agent method works"""
    try:
        from your_biomni_module import agent
        result = agent.go("test query")
        print(f"✅ Agent call successful: {result[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Agent call failed: {e}")
        return False

if __name__ == "__main__":
    test_agent_import()
    test_agent_call()
```

### Integration Testing
1. Install the plugin in your Dify development environment
2. Create a simple Agent or Workflow
3. Add your Biomni tool
4. Test with simple queries first
5. Gradually test more complex biomedical queries

## 🚀 Deployment

### Development Environment
```bash
# Upload to your Dify development instance
# Use the plugin management interface to upload biomni.difypkg
```

### Production Environment
```bash
# For production, ensure:
# 1. All dependencies are properly configured
# 2. Biomni agent is installed and accessible
# 3. Sufficient system resources (memory, CPU)
# 4. Proper error handling and logging
```

## 🔧 Troubleshooting

### Common Issues:

1. **Import Errors**: Check your Biomni path and import statements
2. **Agent Not Found**: Verify your agent setup and method names  
3. **Timeout Issues**: Increase `max_execution_time` for complex queries
4. **Memory Issues**: Monitor resource usage, add cleanup if needed
5. **Permission Errors**: Ensure proper file permissions and paths

### Debug Logging:
Add more logging to troubleshoot:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add debug logs throughout your code
logger.debug(f"Agent setup status: {self.agent is not None}")
logger.debug(f"Processing query: {research_query[:50]}...")
```

## ✅ Final Checklist

Before packaging:
- [ ] Updated all `your-name` placeholders
- [ ] Added proper Biomni agent import and path
- [ ] Configured correct agent method call
- [ ] Added plugin icon to `_assets/`
- [ ] Updated `requirements.txt` with dependencies
- [ ] Created empty `__init__.py` files
- [ ] Tested agent import and method calls
- [ ] Tested plugin in development mode
- [ ] Verified remote debugging works

## 📚 Next Steps

After successful deployment:
1. Monitor plugin performance and resource usage
2. Collect user feedback on biomedical research capabilities
3. Consider adding more advanced features:
   - Progress streaming for long-running analyses
   - Result caching for common queries
   - Integration with biomedical databases
   - Batch processing capabilities
4. Submit to Dify Marketplace (optional)

Your Biomni plugin is now ready for use! 🧬✨

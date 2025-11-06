# Test Agent

A custom AgentCore application built from the healthcare and life sciences template.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r dev-requirements.txt
   ```

2. **Set up AWS infrastructure:**
   ```bash
   ./scripts/prereq.sh
   ```

3. **Deploy AgentCore components:**
   ```bash
   python scripts/agentcore_gateway.py
   python scripts/agentcore_memory.py
   python scripts/agentcore_agent_runtime.py
   ```

4. **Run the application:**
   ```bash
   streamlit run app_oauth.py  # For OAuth authentication
   # OR
   streamlit run app.py        # For IAM authentication
   ```

## Configuration

Edit `.agentcore.yaml` to customize your agent's behavior, tools, and deployment settings.

## Project Structure

- `agent/` - Agent configuration and custom tools
- `app_modules/` - Streamlit UI components
- `scripts/` - Deployment and management scripts
- `prerequisite/` - Infrastructure setup files
- `tests/` - Test files

## Documentation

See the original [AgentCore Template README](../agentcore_template/README.md) for detailed documentation.

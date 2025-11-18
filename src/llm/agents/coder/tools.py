"""Tools for the coder agent."""

import os
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv

load_dotenv()


def get_coder_tools():
    """Get coder tools from MCP server."""
    # Coder tool configuration
    coder_configs = {
        "coder": {
            "command": "python",
            "args": [
                "data/tools/coder/mcp_server.py",
            ],
            "env": {
                "BACKEND_URL": os.getenv("CODER_BACKEND"),
            },
            "transport": "stdio",
        }
    }
    
    coder_tools_client = MultiServerMCPClient(coder_configs)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coder_tools = loop.run_until_complete(coder_tools_client.get_tools())

    return coder_tools
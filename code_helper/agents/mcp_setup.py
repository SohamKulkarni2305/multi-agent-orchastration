"""
mcp_setup.py — Model Context Protocol (MCP) Filesystem server configuration.
"""

from pathlib import Path
from typing import Any
from mcp import StdioServerParameters

# Resilient import across google-adk versions (ADK 1.14+ uses google.adk.tools.mcp_tool.mcp_toolset.MCPToolset)
try:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset as McpToolset
except ImportError:
    try:
        from google.adk.tools.mcp_tool import McpToolset
    except ImportError:
        try:
            from google.adk.tools import McpToolset
        except ImportError:
            McpToolset = None


def build_mcp_server_params(target_dir: str = ".") -> StdioServerParameters:
    """
    Build cross-platform Stdio connection parameters for @modelcontextprotocol/server-filesystem,
    resolving the target directory to a canonical absolute path.
    """
    abs_path = str(Path(target_dir).resolve())
    return StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", abs_path],
    )


def get_filesystem_mcp_toolset(target_dir: str = ".") -> Any:
    """
    Instantiate and return the ADK McpToolset managing connection to Filesystem MCP server.
    Filters tools to read_file and list_directory.
    """
    if McpToolset is None:
        return None

    params = build_mcp_server_params(target_dir)
    try:
        return McpToolset(
            connection_params=params,
            tool_filter=["read_file", "list_directory"],
        )
    except Exception as e:
        print(f"[!] Warning: Could not initialize McpToolset: {e}")
        return None



"""
mcp_setup.py — Model Context Protocol (MCP) Filesystem server configuration.
"""

from pathlib import Path
from mcp import StdioServerParameters
from google.adk.tools import McpToolset


def build_mcp_server_params(target_dir: str = ".") -> StdioServerParameters:
    """
    Build cross-platform StdioServerParameters for @modelcontextprotocol/server-filesystem,
    resolving the target directory to a canonical absolute path.
    """
    abs_path = str(Path(target_dir).resolve())
    return StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", abs_path],
    )


def get_filesystem_mcp_toolset(target_dir: str = ".") -> McpToolset:
    """
    Instantiate and return the ADK McpToolset managing connection to Filesystem MCP server.
    Filters tools to read_file and list_directory.
    """
    params = build_mcp_server_params(target_dir)
    return McpToolset(
        connection_params=params,
        tool_filter=["read_file", "list_directory"],
    )

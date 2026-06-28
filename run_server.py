"""PyInstaller entry point -- dual transport.

Sets --http mode when MCP_PORT env var is set (Tauri spawn).
Defaults to stdio (Claude Desktop) when no port is configured.
"""
import sys
import os

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    sys.argv = [
        "run_server.py", "--http", "--port", str(port),
    ]
else:
    sys.argv = ["run_server.py"]

from glama_status_mcp.server import main
main()

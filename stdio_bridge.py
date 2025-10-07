#!/usr/bin/env python3
"""
Simple stdio bridge for ConPort FastMCP server.
This script acts as a stdio MCP server that forwards requests to the FastMCP HTTP server.
"""

import sys
import json
import asyncio
import aiohttp
import os
from typing import Dict, Any

class StdioBridge:
    def __init__(self, mcp_url: str = "http://localhost:8001/mcp"):
        self.mcp_url = mcp_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def forward_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Forward a request to the FastMCP HTTP server."""
        if not self.session:
            await self.__aenter__()

        try:
            async with self.session.post(self.mcp_url, json=request) as response:
                return await response.json()
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"HTTP request failed: {e}"
                },
                "id": request.get("id")
            }

async def main():
    """Main stdio loop."""
    bridge = StdioBridge()

    try:
        async with bridge:
            for line in sys.stdin:
                try:
                    request = json.loads(line.strip())
                    response = await bridge.forward_request(request)
                    print(json.dumps(response), flush=True)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {e}"
                        },
                        "id": None
                    }
                    print(json.dumps(error_response), flush=True)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
import requests
import json
import time

def test_mcp_http(url="http://localhost:8001/mcp"):
    """Test basic MCP HTTP endpoint"""

    # Test 1: tools/list
    print("🔧 Testing tools/list...")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False

        result = response.json()
        if "result" in result and "tools" in result["result"]:
            tools = result["result"]["tools"]
            print(f"✅ Found {len(tools)} tools")
            print("📋 Available tools:")
            for tool in tools[:5]:  # Show first 5
                print(f"  - {tool['name']}")
            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more")
            return True
        else:
            print(f"❌ Unexpected response: {result}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_simple_tool(url="http://localhost:8001/mcp"):
    """Test a simple tool call"""

    workspace_id = "/opt/projects/myconport"

    print(f"\n🔧 Testing get_product_context with workspace: {workspace_id}")
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_product_context",
            "arguments": {"workspace_id": workspace_id}
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False

        result = response.json()
        if "result" in result:
            print("✅ Tool call successful")
            return True
        else:
            print(f"❌ Tool call failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing ConPort MCP HTTP Transport")
    print("=" * 40)

    # First start server if needed
    print("Starting MCP server on HTTP...")
    import subprocess
    import time

    # Start the MCP server in HTTP mode
    cmd = [
        "python", "-m", "src.context_portal_mcp.main",
        "--mode", "http",
        "--port", "8001"
    ]

    try:
        server_process = subprocess.Popen(
            cmd,
            cwd="/opt/projects/myconport",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for startup
        print("Waiting for server to start...")
        time.sleep(5)

        # Test basic endpoint
        if test_mcp_http():
            # Test a simple tool
            if test_simple_tool():
                print("\n🎉 Basic HTTP transport test PASSED!")
            else:
                print("\n⚠️  Tool call failed")
        else:
            print("\n❌ Basic endpoint test failed")

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
    finally:
        if 'server_process' in locals():
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

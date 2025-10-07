#!/usr/bin/env python3
import json
import requests
import sys
import time

def make_mcp_call(url, method, params=None, request_id=1):
    """Make a JSON-RPC call over HTTP to the MCP server"""
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    if params:
        payload["params"] = params

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"HTTP Error calling {method}: {e}")
        return None

def test_conport_http_transport():
    """Test ConPort MCP server via HTTP transport"""

    base_url = "http://localhost:8001/mcp"  # Direct Python server MCP endpoint
    workspace_id = "/opt/projects/myconport"

    print("🚀 Testing ConPort MCP Server via HTTP Transport")
    print(f"📍 Server URL: {base_url}")
    print(f"📦 Workspace: {workspace_id}")
    print("=" * 50)

    try:
        # Initialize MCP protocol
        print("📡 Initializing MCP protocol...")
        init_response = make_mcp_call(base_url, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "http-test-client",
                "version": "1.0.0"
            }
        }, 1)

        if not init_response or "error" in init_response:
            print(f"❌ Failed to initialize: {init_response.get('error', 'Unknown error')}")
            return
        else:
            print("✅ MCP initialized")

        # Send initialized notification
        make_mcp_call(base_url, "notifications/initialized")
        print("✅ Initialized notification sent")

        # List tools
        print("\n📋 Listing available tools...")
        tools_response = make_mcp_call(base_url, "tools/list", {}, 2)

        if not tools_response or "error" in tools_response:
            print(f"❌ Failed to list tools: {tools_response.get('error', 'Unknown error')}")
            return

        tools = tools_response.get("result", {}).get("tools", [])
        print(f"✅ Found {len(tools)} tools")

        # Print available tools
        print("\n📋 Available Tools:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool['name']} - {tool.get('description', 'No description')}")

        # Test each tool systematically
        print("\n🎯 Testing all tools...")

        tool_tests = {
            "Context Management": [
                ("get_product_context", "Retrieve product context", {"workspace_id": workspace_id}),
                ("get_active_context", "Retrieve active context", {"workspace_id": workspace_id}),
                ("update_product_context", "Update product context", {
                    "workspace_id": workspace_id,
                    "content": {
                        "project_name": "HTTP Transport Test",
                        "description": "Testing ConPort MCP via HTTP"
                    }
                }),
                ("update_active_context", "Update active context", {
                    "workspace_id": workspace_id,
                    "content": {
                        "current_focus": "HTTP transport testing",
                        "open_issues": ["Verify all tools work"]
                    }
                }),
            ],
            "Decision Logging": [
                ("log_decision", "Log a test decision", {
                    "workspace_id": workspace_id,
                    "summary": "HTTP transport decision test",
                    "rationale": "Validating HTTP calls work correctly",
                    "tags": ["test", "http"]
                }),
                ("get_decisions", "Get logged decisions", {"workspace_id": workspace_id}),
                ("search_decisions_fts", "Search decisions", {
                    "workspace_id": workspace_id,
                    "query_term": "test"
                }),
            ],
            "Progress Tracking": [
                ("log_progress", "Log test progress", {
                    "workspace_id": workspace_id,
                    "status": "IN_PROGRESS",
                    "description": "Testing HTTP transport"
                }),
                ("get_progress", "Get progress entries", {"workspace_id": workspace_id}),
                ("update_progress", "Update progress entry", {
                    "workspace_id": workspace_id,
                    "progress_id": 1,
                    "status": "DONE"
                }),
            ],
            "System Patterns": [
                ("log_system_pattern", "Log test pattern", {
                    "workspace_id": workspace_id,
                    "name": "HTTP Transport Pattern",
                    "description": "Testing system pattern logging via HTTP",
                    "tags": ["test", "http"]
                }),
                ("get_system_patterns", "Get system patterns", {"workspace_id": workspace_id}),
            ],
            "Custom Data": [
                ("log_custom_data", "Log test custom data", {
                    "workspace_id": workspace_id,
                    "category": "http_test",
                    "key": "test_entry",
                    "value": {"transport": "HTTP", "test": True, "timestamp": time.time()}
                }),
                ("get_custom_data", "Get custom data", {"workspace_id": workspace_id}),
                ("search_custom_data_value_fts", "Search custom data", {
                    "workspace_id": workspace_id,
                    "query_term": "test"
                }),
            ],
            "Semantic & Search": [
                ("semantic_search_conport", "Test semantic search", {
                    "workspace_id": workspace_id,
                    "query_text": "testing http transport"
                }),
                ("get_recent_activity_summary", "Get recent activity", {"workspace_id": workspace_id}),
                ("get_workspace_detection_info", "Get workspace info", {}),
            ],
            "Schema & Utils": [
                ("get_conport_schema", "Get server schema", {"workspace_id": workspace_id}),
                ("export_conport_to_markdown", "Export to markdown", {"workspace_id": workspace_id}),
            ],
            "Item Relationships": [
                ("link_conport_items", "Link test items", {
                    "workspace_id": workspace_id,
                    "source_item_type": "decision",
                    "source_item_id": "1",
                    "target_item_type": "progress",
                    "target_item_id": "1",
                    "relationship_type": "tracks",
                    "description": "Linking test decision to progress"
                }),
                ("get_linked_items", "Get linked items", {
                    "workspace_id": workspace_id,
                    "item_type": "decision",
                    "item_id": "1"
                }),
                ("get_item_history", "Get item history", {
                    "workspace_id": workspace_id,
                    "item_type": "product_context"
                }),
            ],
            "Batch Operations": [
                ("batch_log_items", "Batch log items", {
                    "workspace_id": workspace_id,
                    "item_type": "custom_data",
                    "items": [
                        {"category": "batch_test", "key": "item1", "value": "first"},
                        {"category": "batch_test", "key": "item2", "value": "second"}
                    ]
                }),
            ],
        }

        total_tests = sum(len(tools) for tools in tool_tests.values())
        print(f"🎯 Running {total_tests} tests across {len(tool_tests)} categories...\n")

        passed = 0
        failed = 0
        request_id = 10  # Start after initial requests

        for category, tools in tool_tests.items():
            print(f"📁 {category}")
            print("-" * len(category))

            for tool_name, description, args in tools:
                try:
                    print(f"  🔧 Testing {tool_name}...", end=" ")

                    response = make_mcp_call(base_url, "tools/call", {
                        "name": tool_name,
                        "arguments": args
                    }, request_id)

                    request_id += 1

                    if not response:
                        print("❌ FAILED: No response")
                        failed += 1
                    elif "error" in response:
                        print(f"❌ FAILED: {response['error'].get('message', 'Unknown error')}")
                        failed += 1
                    else:
                        print("✅ PASSED")
                        passed += 1

                except Exception as e:
                    print(f"❌ FAILED: Exception - {e}")
                    failed += 1

            print()

        # Final summary
        print("🎯 COMPREHENSIVE HTTP TRANSPORT TEST RESULTS:")
        print("=" * 50)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total:  {passed + failed}")
        success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")

        if failed == 0:
            print("\n🎉 ALL TOOLS TESTED SUCCESSFULLY VIA HTTP TRANSPORT!")
            print("The ConPort MCP server with HTTP transport is working correctly.")
        else:
            print(f"\n⚠️  {failed} tools failed via HTTP transport.")

    except Exception as e:
        print(f"❌ Fatal error during HTTP testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conport_http_transport()

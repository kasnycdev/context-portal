#!/usr/bin/env python3
import json
import subprocess
import sys
import time
import threading
import queue

def send_request(process, request):
    """Send a request to the MCP server and return the response"""
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()
    return json.loads(process.stdout.readline().strip())

def test_conport_mcp():
    """Test ConPort MCP server by calling each available tool"""

    # Start the ConPort server process
    cmd = [
        "python", "-m", "src.context_portal_mcp.main",
        "--mode", "stdio",
        "--workspace_id", "/opt/projects/myconport",
        "--log-level", "ERROR"  # Reduce log noise
    ]

    print("Starting ConPort MCP server...")
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/opt/projects/myconport"
    )

    # MCP protocol messages
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }

    try:
        # Initialize MCP protocol
        print("Initializing MCP protocol...")
        init_response = send_request(process, initialize_request)
        print(f"✓ Initialize successful: {init_response['result']['serverInfo']['name']}")

        send_request(process, initialized_notification)
        print("✓ Initialized notification sent")

        # List tools first
        tools_response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })

        tools = tools_response["result"]["tools"]
        print(f"✓ Found {len(tools)} tools")

        # Now test each tool systematically
        workspace_id = "/opt/projects/myconport"
        tool_tests = []

        # Helper function to add test
        def add_test(name, description, tool_call):
            tool_tests.append((name, description, tool_call))

        # Get context tools
        add_test("get_product_context", "Retrieve empty product context", {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "get_product_context",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        add_test("get_active_context", "Retrieve empty active context", {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "get_active_context",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        # Update context tools
        add_test("update_product_context", "Set initial product context", {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "update_product_context",
                "arguments": {
                    "workspace_id": workspace_id,
                    "content": {
                        "project_name": "Test ConPort Project",
                        "description": "A test project for validating ConPort MCP tools"
                    }
                }
            }
        })

        add_test("update_active_context", "Set initial active context", {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {
                "name": "update_active_context",
                "arguments": {
                    "workspace_id": workspace_id,
                    "content": {
                        "current_focus": "Testing all MCP tools",
                        "open_issues": ["Tool validation"]
                    }
                }
            }
        })

        # Log decision
        add_test("log_decision", "Log a test decision", {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {
                "name": "log_decision",
                "arguments": {
                    "workspace_id": workspace_id,
                    "summary": "Test decision for tool validation",
                    "rationale": "Need to validate that decision logging works",
                    "tags": ["test", "validation"]
                }
            }
        })

        # Log progress
        add_test("log_progress", "Log test progress", {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "tools/call",
            "params": {
                "name": "log_progress",
                "arguments": {
                    "workspace_id": workspace_id,
                    "status": "IN_PROGRESS",
                    "description": "Testing ConPort MCP tools"
                }
            }
        })

        # Log system pattern
        add_test("log_system_pattern", "Log test pattern", {
            "jsonrpc": "2.0",
            "id": 16,
            "method": "tools/call",
            "params": {
                "name": "log_system_pattern",
                "arguments": {
                    "workspace_id": workspace_id,
                    "name": "Test Pattern",
                    "description": "A test system pattern",
                    "tags": ["test"]
                }
            }
        })

        # Log custom data
        add_test("log_custom_data", "Log test custom data", {
            "jsonrpc": "2.0",
            "id": 17,
            "method": "tools/call",
            "params": {
                "name": "log_custom_data",
                "arguments": {
                    "workspace_id": workspace_id,
                    "category": "test_data",
                    "key": "test_key",
                    "value": {"data": "test value", "number": 42}
                }
            }
        })

        # Retrieve data tools
        add_test("get_decisions", "Get logged decisions", {
            "jsonrpc": "2.0",
            "id": 18,
            "method": "tools/call",
            "params": {
                "name": "get_decisions",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        add_test("get_progress", "Get progress entries", {
            "jsonrpc": "2.0",
            "id": 19,
            "method": "tools/call",
            "params": {
                "name": "get_progress",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        add_test("get_system_patterns", "Get system patterns", {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {
                "name": "get_system_patterns",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        add_test("get_custom_data", "Get custom data", {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {
                "name": "get_custom_data",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        # Search tools
        add_test("search_decisions_fts", "Search decisions", {
            "jsonrpc": "2.0",
            "id": 22,
            "method": "tools/call",
            "params": {
                "name": "search_decisions_fts",
                "arguments": {
                    "workspace_id": workspace_id,
                    "query_term": "test"
                }
            }
        })

        add_test("search_custom_data_value_fts", "Search custom data", {
            "jsonrpc": "2.0",
            "id": 23,
            "method": "tools/call",
            "params": {
                "name": "search_custom_data_value_fts",
                "arguments": {
                    "workspace_id": workspace_id,
                    "query_term": "test"
                }
            }
        })

        # Utility tools
        add_test("get_conport_schema", "Get server schema", {
            "jsonrpc": "2.0",
            "id": 24,
            "method": "tools/call",
            "params": {
                "name": "get_conport_schema",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        add_test("get_recent_activity_summary", "Get recent activity", {
            "jsonrpc": "2.0",
            "id": 25,
            "method": "tools/call",
            "params": {
                "name": "get_recent_activity_summary",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        add_test("get_workspace_detection_info", "Get workspace detection info", {
            "jsonrpc": "2.0",
            "id": 26,
            "method": "tools/call",
            "params": {
                "name": "get_workspace_detection_info",
                "arguments": {}
            }
        })

        # Semantic search
        add_test("semantic_search_conport", "Test semantic search", {
            "jsonrpc": "2.0",
            "id": 27,
            "method": "tools/call",
            "params": {
                "name": "semantic_search_conport",
                "arguments": {
                    "workspace_id": workspace_id,
                    "query_text": "testing tools"
                }
            }
        })

        # Link tools (need to get created items first to link them)
        add_test("get_linked_items", "Get linked items (should be empty)", {
            "jsonrpc": "2.0",
            "id": 28,
            "method": "tools/call",
            "params": {
                "name": "get_linked_items",
                "arguments": {
                    "workspace_id": workspace_id,
                    "item_type": "decision",
                    "item_id": "1"  # Assuming we get decision ID 1
                }
            }
        })

        # Export/Import tools
        add_test("export_conport_to_markdown", "Export to markdown", {
            "jsonrpc": "2.0",
            "id": 29,
            "method": "tools/call",
            "params": {
                "name": "export_conport_to_markdown",
                "arguments": {"workspace_id": workspace_id}
            }
        })

        # Run all tests
        print(f"\n🚀 Running {len(tool_tests)} tool tests...")

        passed = 0
        failed = 0

        for i, (test_name, description, tool_call) in enumerate(tool_tests, 1):
            try:
                print(f"\n[{i}/{len(tool_tests)}] Testing {test_name}: {description}")
                response = send_request(process, tool_call)

                if "error" in response:
                    print(f"❌ FAILED: {response['error']['message']}")
                    failed += 1
                else:
                    print(f"✅ PASSED")
                    passed += 1

            except Exception as e:
                print(f"❌ FAILED: Exception - {e}")
                failed += 1

        # Final summary
        print(f"\n🎯 Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {passed + failed}")

        if failed == 0:
            print("\n🎉 All tools tested successfully!")
        else:
            print(f"\n⚠️  {failed} tools need attention.")

    except Exception as e:
        print(f"❌ Fatal error during testing: {e}")

    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    test_conport_mcp()

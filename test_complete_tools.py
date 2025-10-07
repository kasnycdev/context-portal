#!/usr/bin/env python3
"""
Complete tool test that verifies ALL 30 registered MCP tools are working.
This test systematically validates each tool according to the comprehensive test categories.
"""

import json
import subprocess
import sys
import time

def send_request(process, request):
    """Send a request to the MCP server and return the response"""
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()
    return json.loads(process.stdout.readline().strip())

def run_complete_tool_test():
    """Run complete test of all 30 registered ConPort MCP tools"""

    # Start fresh MCP server
    cmd = [
        "python", "-m", "src.context_portal_mcp.main",
        "--mode", "stdio",
        "--workspace_id", "/opt/projects/myconport",
        "--log-level", "ERROR"
    ]

    print("🚀 Starting ConPort MCP Server for complete verification...")
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/opt/projects/myconport"
    )

    workspace_id = "/opt/projects/myconport"
    total_tools_tested = 0
    passed = 0
    failed = 0

    try:
        # Initialize MCP protocol
        print("📡 Initializing MCP protocol...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "clientInfo": {"name": "complete-test-client", "version": "1.0.0"}
            }
        }

        init_response = send_request(process, init_request)
        if "error" in init_response:
            print(f"❌ MCP initialization failed: {init_response['error']}")
            return
        print("✅ MCP protocol initialized")

        # Send initialized notification
        send_request(process, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # Verify all 30 registered tools exist
        tools_response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })

        if "error" in tools_response:
            print(f"❌ Failed to list tools: {tools_response['error']}")
            return

        available_tools = tools_response.get("result", {}).get("tools", [])
        print(f"✅ Server reports {len(available_tools)} tools available")

        # Expected tool names (from source code grep)
        expected_tools = {
            "get_product_context", "update_product_context",
            "get_active_context", "update_active_context",
            "log_decision", "get_decisions", "search_decisions_fts", "delete_decision_by_id",
            "log_progress", "get_progress", "update_progress", "delete_progress_by_id",
            "log_system_pattern", "get_system_patterns", "delete_system_pattern_by_id",
            "log_custom_data", "get_custom_data", "delete_custom_data",
            "search_project_glossary_fts", "search_custom_data_value_fts",
            "batch_log_items", "link_conport_items", "get_linked_items", "get_item_history",
            "semantic_search_conport", "get_recent_activity_summary", "get_workspace_detection_info",
            "get_conport_schema", "export_conport_to_markdown", "import_markdown_to_conport"
        }

        actual_tool_names = {tool['name'] for tool in available_tools}
        missing_tools = expected_tools - actual_tool_names
        extra_tools = actual_tool_names - expected_tools

        if missing_tools:
            print(f"⚠️  Missing tools ({len(missing_tools)}): {', '.join(sorted(missing_tools))}")
        if extra_tools:
            print(f"ℹ️  Extra tools ({len(extra_tools)}): {', '.join(sorted(extra_tools))}")

        if len(actual_tool_names) != 30:
            print(f"❌ Expected 30 tools, but found {len(actual_tool_names)}")
            return

        # Test categories mapping all 30 tools
        test_scenarios = {
            "Context Management (4 tools)": [
                "get_product_context",
                "get_active_context",
                "update_product_context",
                "update_active_context"
            ],
            "Decision Management (4 tools)": [
                "log_decision",
                "get_decisions",
                "search_decisions_fts",
                "delete_decision_by_id"
            ],
            "Progress Tracking (4 tools)": [
                "log_progress",
                "get_progress",
                "update_progress",
                "delete_progress_by_id"
            ],
            "System Patterns (3 tools)": [
                "log_system_pattern",
                "get_system_patterns",
                "delete_system_pattern_by_id"
            ],
            "Custom Data Management (5 tools)": [
                "log_custom_data",
                "get_custom_data",
                "delete_custom_data",
                "search_custom_data_value_fts",
                "search_project_glossary_fts"
            ],
            "Search & Semantic (4 tools)": [
                "semantic_search_conport",
                "get_recent_activity_summary",
                "get_workspace_detection_info",
                "get_conport_schema"
            ],
            "Data Import/Export (3 tools)": [
                "export_conport_to_markdown",
                "import_markdown_to_conport",
                "batch_log_items"
            ],
            "Item Relationships (3 tools)": [
                "link_conport_items",
                "get_linked_items",
                "get_item_history"
            ]
        }

        print(f"\n🎯 Testing ALL {len(expected_tools)} tools systematically:")
        print("=" * 60)

        request_id = 10

        for category, tool_names in test_scenarios.items():
            print(f"\n📁 {category}")
            print("-" * len(category))

            for tool_name in tool_names:
                total_tools_tested += 1

                try:
                    print(f"  🔧 {tool_name}...", end=" ")
                    sys.stdout.flush()

                    # Use simple test arguments for each tool
                    test_args = {"workspace_id": workspace_id}

                    if tool_name in ["delete_decision_by_id", "delete_progress_by_id", "delete_system_pattern_by_id"]:
                        test_args["decision_id" if "decision" in tool_name else "progress_id" if "progress" in tool_name else "pattern_id"] = "999"
                    elif tool_name == "delete_custom_data":
                        test_args.update({"category": "test", "key": "test_key"})
                    elif tool_name.startswith("search_"):
                        test_args["query_term"] = "test"
                    elif tool_name == "semantic_search_conport":
                        test_args["query_text"] = "testing"
                    elif tool_name == "link_conport_items":
                        test_args.update({
                            "source_item_type": "decision",
                            "source_item_id": "999",
                            "target_item_type": "progress",
                            "target_item_id": "999",
                            "relationship_type": "test",
                            "description": "Test link"
                        })
                    elif tool_name == "get_linked_items":
                        test_args.update({"item_type": "decision", "item_id": "999"})
                    elif tool_name == "get_item_history":
                        test_args["item_type"] = "product_context"
                    elif tool_name == "batch_log_items":
                        test_args.update({
                            "item_type": "custom_data",
                            "items": [{"category": "test", "key": "test", "value": "test"}]
                        })

                    response = send_request(process, {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": test_args}
                    })

                    request_id += 1

                    if "error" in response:
                        error_msg = response["error"].get("message", "Unknown error")
                        print(f"❌ FAILED: {error_msg}")
                        failed += 1
                    else:
                        print("✅ PASSED")
                        passed += 1

                except Exception as e:
                    print(f"❌ EXCEPTION: {e}")
                    failed += 1

        # Final comprehensive report
        print(f"\n🎯 COMPLETE TOOL VALIDATION RESULTS:")
        print("=" * 60)
        print(f"📊 Total tools tested: {total_tools_tested}")
        print(f"✅ Tools passed: {passed}")
        print(f"❌ Tools failed: {failed}")

        if total_tools_tested == 30 and failed == 0:
            success_rate = 100.0
            print(f"📈 Success rate: {success_rate:.1f}%")
            print("\n🎉 SUCCESS: All 30 ConPort MCP tools validated successfully!")
            print("The complete MCP server implementation is working correctly.")
        else:
            success_rate = (passed / total_tools_tested * 100) if total_tools_tested > 0 else 0
            print(f"📈 Success rate: {success_rate:.1f}%")
            print(f"\n⚠️ VERIFICATION: {passed}/{total_tools_tested} tools working correctly.")
            if total_tools_tested < 30:
                print(f"Missing {30 - total_tools_tested} tool tests.")

    except Exception as e:
        print(f"❌ CRITICAL: Complete tool test failed with exception: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()

if __name__ == "__main__":
    run_complete_tool_test()

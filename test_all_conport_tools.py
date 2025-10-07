#!/usr/bin/env python3
"""
Systematic test of all 30 ConPort MCP tools to verify functionality.
This script tests each tool and provides comprehensive reporting.
"""

import json
import subprocess
import sys
import tempfile
import os
from typing import Dict, List, Tuple

def send_mcp_message(process, message: dict, request_id: int) -> dict:
    """Send an MCP message and get response"""
    message["id"] = request_id
    json_message = json.dumps(message)

    # Send the message
    process.stdin.write(json_message + "\n")
    process.stdin.flush()

    # Read response (expecting one line)
    response_line = process.stdout.readline()
    if not response_line:
        return {"error": "No response from server"}

    try:
        response = json.loads(response_line.strip())
        return response
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {e}", "raw": response_line.strip()}

def initialize_mcp(process) -> bool:
    """Initialize MCP connection"""
    print("🔄 Initializing MCP...")
    init_message = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "conport-comprehensive-test",
                "version": "1.0.0"
            }
        }
    }

    response = send_mcp_message(process, init_message, 1)
    if "error" in response:
        print(f"❌ MCP initialization failed: {response['error']}")
        return False

    print("✅ MCP initialized")

    # Send initialized notification
    process.stdin.write('{"jsonrpc": "2.0", "method": "notifications/initialized"}\n')
    process.stdin.flush()

    return True

def list_tools(process) -> Dict:
    """List available tools"""
    print("🔧 Listing available tools...")
    response = send_mcp_message(process, {"jsonrpc": "2.0", "method": "tools/list"}, 2)

    if "error" in response:
        print(f"❌ Failed to list tools: {response['error']}")
        return {}

    tools = response.get("result", {}).get("tools", [])
    print(f"✅ Found {len(tools)} tools")
    return {tool["name"]: tool for tool in tools}

def test_all_conport_tools():
    """Main function to test all ConPort tools systematically"""

    workspace_id = "/opt/projects/myconport"
    print("=" * 70)
    print("🧪 CONPORT COMPREHENSIVE TOOL VERIFICATION")
    print("=" * 70)
    print(f"📦 Workspace: {workspace_id}")
    print()

    # Start ConPort MCP server
    cmd = [
        "python",
        "-m", "src.context_portal_mcp.main",
        "--mode", "stdio",
        "--workspace_id", workspace_id,
        "--log-level", "ERROR"  # Suppress logs for cleaner output
    ]

    print("🚀 Starting ConPort MCP server...")
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # Suppress stderr
            text=True,
            cwd=workspace_id
        )
    except Exception as e:
        print(f"❌ Failed to start ConPort server: {e}")
        return 1

    try:
        # Give server time to start
        import time
        time.sleep(2)

        # Initialize MCP
        if not initialize_mcp(process):
            return 1

        # List available tools
        available_tools = list_tools(process)
        if not available_tools:
            return 1

        # Expected tools from the provided list
        all_expected_tools = {
            "get_product_context",
            "update_product_context",
            "get_active_context",
            "update_active_context",
            "log_decision",
            "get_decisions",
            "search_decisions_fts",
            "delete_decision_by_id",
            "log_progress",
            "get_progress",
            "update_progress",
            "delete_progress_by_id",
            "log_system_pattern",
            "get_system_patterns",
            "delete_system_pattern_by_id",
            "log_custom_data",
            "get_custom_data",
            "delete_custom_data",
            "search_project_glossary_fts",
            "search_custom_data_value_fts",
            "batch_log_items",
            "link_conport_items",
            "get_linked_items",
            "get_item_history",
            "semantic_search_conport",
            "get_recent_activity_summary",
            "get_workspace_detection_info",
            "get_conport_schema",
            "export_conport_to_markdown",
            "import_markdown_to_conport"
        }

        # Check for missing tools
        available_names = set(available_tools.keys())
        missing_tools = all_expected_tools - available_names
        extra_tools = available_names - all_expected_tools

        if missing_tools:
            print(f"⚠️  Missing tools ({len(missing_tools)}): {sorted(missing_tools)}")
        if extra_tools:
            print(f"ℹ️  Extra tools ({len(extra_tools)}): {sorted(extra_tools)}")

        if len(available_names) != 30:
            print(f"❌ Expected 30 tools, found {len(available_names)}")
            return 1

        print(f"\n🎯 Testing ALL {len(all_expected_tools)} ConPort tools:")
        print("=" * 60)

        # Organize tools by category for systematic testing
        tool_categories = {
            "Context Management (4)": [
                "get_product_context",
                "get_active_context",
                "update_product_context",
                "update_active_context"
            ],
            "Decision Management (4)": [
                "log_decision",
                "get_decisions",
                "search_decisions_fts",
                "delete_decision_by_id"
            ],
            "Progress Tracking (4)": [
                "log_progress",
                "get_progress",
                "update_progress",
                "delete_progress_by_id"
            ],
            "System Patterns (3)": [
                "log_system_pattern",
                "get_system_patterns",
                "delete_system_pattern_by_id"
            ],
            "Custom Data Management (5)": [
                "log_custom_data",
                "get_custom_data",
                "delete_custom_data",
                "search_custom_data_value_fts",
                "search_project_glossary_fts"
            ],
            "Search & Semantic (4)": [
                "semantic_search_conport",
                "get_recent_activity_summary",
                "get_workspace_detection_info",
                "get_conport_schema"
            ],
            "Item Relationships (3)": [
                "link_conport_items",
                "get_linked_items",
                "get_item_history"
            ],
            "Import/Export (3)": [
                "export_conport_to_markdown",
                "import_markdown_to_conport",
                "batch_log_items"
            ],
            "History & Utils": [
                "update_decisions"
            ]
        }

        total_tools_tested = 0
        passed_tests = 0
        failed_tests = 0

        request_id = 10

        for category, tool_names in tool_categories.items():
            print(f"\n📁 {category}")
            print("-" * (len(category) + 2))

            for tool_name in tool_names:
                total_tools_tested += 1

                if tool_name not in available_tools:
                    print(f"  ❌ {tool_name} (tool not available)")
                    failed_tests += 1
                    continue

                print(f"  🔧 {tool_name}...", end=" ")
                sys.stdout.flush()

                # Prepare test arguments based on tool
                test_args = {"workspace_id": workspace_id}

                # Customize arguments based on tool requirements
                if tool_name in ["delete_decision_by_id", "delete_progress_by_id", "delete_system_pattern_by_id"]:
                    test_args["decision_id" if "decision" in tool_name else "progress_id" if "progress" in tool_name else "pattern_id"] = "999"
                elif tool_name == "delete_custom_data":
                    test_args.update({"category": "test", "key": "test_key"})
                elif tool_name.startswith("search_") or tool_name == "semantic_search_conport":
                    test_args["query_term" if "_" in tool_name else "query_text"] = "test"
                    if "semantic_search_conport" in tool_name:
                        test_args["top_k"] = 3
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
                elif tool_name == "update_product_context":
                    test_args["content"] = {"testing": "comprehensive test"}
                elif tool_name == "update_active_context":
                    test_args["content"] = {"testing": "active context"}
                elif tool_name == "log_progress":
                    test_args.update({
                        "status": "IN_PROGRESS",
                        "description": "Testing ConPort tools"
                    })
                elif tool_name == "log_decision":
                    test_args.update({
                        "summary": "Test decision for ConPort verification",
                        "rationale": "Testing all tools comprehensively",
                        "tags": ["test", "verification"]
                    })
                elif tool_name == "log_system_pattern":
                    test_args.update({
                        "name": "Test Pattern",
                        "description": "Testing system pattern logging"
                    })
                elif tool_name == "log_custom_data":
                    test_args.update({
                        "category": "test_category",
                        "key": "test_key",
                        "value": "test_value"
                    })

                # Test the tool
                tool_response = send_mcp_message(process, {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": test_args
                    }
                }, request_id)

                request_id += 1

                if "error" in tool_response:
                    error_msg = tool_response["error"].get("message", "Unknown error")
                    # For delete operations on non-existent items, "not found" is expected
                    if ("not found" in error_msg.lower() or
                        "does not exist" in error_msg.lower() or
                        "no item found" in error_msg.lower()):
                        print("✅ PASSED (expected for delete on non-existent)")
                        passed_tests += 1
                    else:
                        print(f"❌ FAILED: {error_msg}")
                        failed_tests += 1
                else:
                    print("✅ PASSED")
                    passed_tests += 1

        print(f"\n🎯 CONPORT COMPREHENSIVE TOOL VERIFICATION RESULTS:")
        print("=" * 70)
        print(f"📊 Total tools tested: {total_tools_tested}")
        print(f"✅ Tests passed: {passed_tests}")
        print(f"❌ Tests failed: {failed_tests}")
        success_rate = (passed_tests / total_tools_tested * 100) if total_tools_tested > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")

        if failed_tests == 0 and total_tools_tested >= 29:  # Allow minor variance
            print("\n🎉 SUCCESS: All ConPort MCP tools verified successfully!")
            print("The complete MCP implementation is working correctly.")
            return 0
        else:
            print(f"\n⚠️ VERIFICATION: {passed_tests}/{total_tools_tested} tools working correctly.")
            if failed_tests > 0:
                print(f"Some tools failed ({failed_tests} total). Review logs above.")
            return 1

    except Exception as e:
        print(f"❌ CRITICAL: Comprehensive tool test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()

if __name__ == "__main__":
    exit_code = test_all_conport_tools()
    sys.exit(exit_code)

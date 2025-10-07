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

def test_conport_tools():
    """Test ConPort MCP server by calling key tools systematically"""

    # Start the ConPort server process
    cmd = [
        "python", "-m", "src.context_portal_mcp.main",
        "--mode", "stdio",
        "--workspace_id", "/opt/projects/myconport",
        "--log-level", "ERROR"  # Reduce log noise
    ]

    print("🚀 Starting ConPort MCP Server for comprehensive testing...")
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/opt/projects/myconport"
    )

    try:
        # Initialize MCP protocol
        print("📡 Initializing MCP protocol...")
        init_response = send_request(process, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        })
        print("✅ MCP initialized")

        send_request(process, {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })

        workspace_id = "/opt/projects/myconport"

        # Key categories of tools to test
        test_groups = {
            "Context Management": [
                ("get_product_context", {"workspace_id": workspace_id}),
                ("get_active_context", {"workspace_id": workspace_id}),
                ("update_product_context", {
                    "workspace_id": workspace_id,
                    "content": {"name": "Test Project", "version": "1.0"}
                }),
                ("update_active_context", {
                    "workspace_id": workspace_id,
                    "content": {"focus": "Testing", "open_issues": ["Tool validation"]}
                }),
            ],
            "Decision Logging": [
                ("get_decisions", {"workspace_id": workspace_id}),
                ("log_decision", {
                    "workspace_id": workspace_id,
                    "summary": "Test decision",
                    "rationale": "For testing purposes",
                    "tags": ["test"]
                }),
                ("get_decisions", {"workspace_id": workspace_id}),
                ("search_decisions_fts", {
                    "workspace_id": workspace_id,
                    "query_term": "test"
                }),
                ("delete_decision_by_id", {
                    "workspace_id": workspace_id,
                    "decision_id": 1
                }),
            ],
            "Progress Tracking": [
                ("get_progress", {"workspace_id": workspace_id}),
                ("log_progress", {
                    "workspace_id": workspace_id,
                    "status": "IN_PROGRESS",
                    "description": "Testing progress logging"
                }),
                ("get_progress", {"workspace_id": workspace_id}),
                ("update_progress", {
                    "workspace_id": workspace_id,
                    "progress_id": 1,
                    "status": "DONE"
                }),
                ("delete_progress_by_id", {
                    "workspace_id": workspace_id,
                    "progress_id": 1
                }),
            ],
            "System Patterns": [
                ("get_system_patterns", {"workspace_id": workspace_id}),
                ("log_system_pattern", {
                    "workspace_id": workspace_id,
                    "name": "Test Pattern",
                    "description": "A test system pattern",
                    "tags": ["test"]
                }),
                ("get_system_patterns", {"workspace_id": workspace_id}),
                ("delete_system_pattern_by_id", {
                    "workspace_id": workspace_id,
                    "pattern_id": 1
                }),
            ],
            "Custom Data": [
                ("get_custom_data", {"workspace_id": workspace_id}),
                ("log_custom_data", {
                    "workspace_id": workspace_id,
                    "category": "test_data",
                    "key": "test_key",
                    "value": {"test": "value", "number": 42}
                }),
                ("get_custom_data", {"workspace_id": workspace_id}),
                ("search_custom_data_value_fts", {
                    "workspace_id": workspace_id,
                    "query_term": "test"
                }),
                ("search_project_glossary_fts", {
                    "workspace_id": workspace_id,
                    "query_term": "test"
                }),
                ("delete_custom_data", {
                    "workspace_id": workspace_id,
                    "category": "test_data",
                    "key": "test_key"
                }),
            ],
            "Semantic & Search": [
                ("semantic_search_conport", {
                    "workspace_id": workspace_id,
                    "query_text": "testing tools"
                }),
                ("get_recent_activity_summary", {"workspace_id": workspace_id}),
                ("get_workspace_detection_info", {}),
            ],
            "Schema & Utils": [
                ("get_conport_schema", {"workspace_id": workspace_id}),
                ("export_conport_to_markdown", {"workspace_id": workspace_id}),
                ("import_markdown_to_conport", {"workspace_id": workspace_id}),
            ],
            "Item Relationships": [
                ("link_conport_items", {
                    "workspace_id": workspace_id,
                    "source_item_type": "decision",
                    "source_item_id": "1",
                    "target_item_type": "progress",
                    "target_item_id": "1",
                    "relationship_type": "tracks",
                    "description": "Linking test decision to progress"
                }),
                ("get_linked_items", {
                    "workspace_id": workspace_id,
                    "item_type": "decision",
                    "item_id": "1"
                }),
                ("get_item_history", {
                    "workspace_id": workspace_id,
                    "item_type": "product_context"
                }),
            ],
            "Batch Operations": [
                ("batch_log_items", {
                    "workspace_id": workspace_id,
                    "item_type": "custom_data",
                    "items": [
                        {"category": "batch_test", "key": "item1", "value": "first"},
                        {"category": "batch_test", "key": "item2", "value": "second"}
                    ]
                }),
            ],
        }

        total_tests = sum(len(tools) for tools in test_groups.values())
        print(f"🎯 Running {total_tests} tests across {len(test_groups)} categories...\n")

        passed = 0
        failed = 0

        for category, tools in test_groups.items():
            print(f"📁 {category}")
            print("-" * len(category))

            for tool_name, args in tools:
                try:
                    print(f"  🔧 Testing {tool_name}...", end=" ")

                    request = {
                        "jsonrpc": "2.0",
                        "id": 100 + passed + failed,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": args}
                    }

                    response = send_request(process, request)

                    if "error" in response:
                        print(f"❌ FAILED: {response['error']['message']}")
                        failed += 1
                    else:
                        print("✅ PASSED")
                        passed += 1

                except Exception as e:
                    print(f"❌ FAILED: Exception - {e}")
                    failed += 1

            print()

        # Summary
        print("🎯 COMPREHENSIVE TEST RESULTS:")
        print("=" * 40)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total:  {passed + failed}")
        print(".1f")

        if failed == 0:
            print(f"\n🎉 ALL {passed + failed} CONPORT TOOLS TESTED SUCCESSFULLY!")
            print("The full MCP server is working correctly.")
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
    test_conport_tools()

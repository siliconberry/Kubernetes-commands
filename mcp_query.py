import asyncio
import json
import os
from mcp_use import MCPClient

# --- Configuration ---
# Assuming your mcp-atlassian server is running locally on port 8080
MCP_SERVER_HOST = "localhost"
MCP_SERVER_PORT = 8080
MCP_SERVICE_NAME = "atlassian" # This is the default service name for mcp-atlassian

# You can get your MCP server's exact SSE endpoint from its logs or configuration
# It's usually /mcp/<service_name>/sse
MCP_SERVER_SSE_PATH = f"/mcp/{MCP_SERVICE_NAME}/sse"

async def query_mcp_jira():
    """
    Connects to the MCP Atlassian server and queries a Jira ticket.
    """
    client = MCPClient(host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)

    try:
        # Establish connection. MCPClient handles SSE under the hood.
        await client.connect()
        print(f"Connected to MCP server at ws://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}{MCP_SERVER_SSE_PATH}")

        # --- Example: Get Jira Ticket Details ---
        print("\n--- Invoking jira_get_issue tool ---")
        tool_name = "jira_get_issue"
        params = {
            "issue_key": "YOUR_JIRA_TICKET_KEY" # Replace with an actual Jira ticket key (e.g., "PROJ-123")
        }

        print(f"Requesting tool: {tool_name} with params: {params}")
        response = await client.invoke_tool(
            tool_name=tool_name,
            params=params
        )

        print("\n--- Response from jira_get_issue ---")
        # MCP responses are typically JSON. Parse it for better readability.
        try:
            parsed_response = json.loads(response)
            print(json.dumps(parsed_response, indent=2))
        except json.JSONDecodeError:
            print(f"Raw response (not JSON): {response}")

        # --- Example: Search Confluence Pages ---
        print("\n--- Invoking confluence_search tool ---")
        tool_name = "confluence_search"
        params = {
            "query": "title ~ 'API Documentation' AND space = 'DEV'", # Replace with your CQL query
            "limit": 5
        }

        print(f"Requesting tool: {tool_name} with params: {params}")
        response = await client.invoke_tool(
            tool_name=tool_name,
            params=params
        )

        print("\n--- Response from confluence_search ---")
        try:
            parsed_response = json.loads(response)
            print(json.dumps(parsed_response, indent=2))
        except json.JSONDecodeError:
            print(f"Raw response (not JSON): {response}")

    except ConnectionRefusedError:
        print(f"Error: Connection refused. Is the MCP server running at {MCP_SERVER_HOST}:{MCP_SERVER_PORT}?")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.disconnect()
        print("\nDisconnected from MCP server.")

if __name__ == "__main__":
    # Make sure to replace "YOUR_JIRA_TICKET_KEY" in the script
    # and ensure your mcp-atlassian server is running and configured correctly.
    asyncio.run(query_mcp_jira())

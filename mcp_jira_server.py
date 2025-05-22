#!/usr/bin/env python3
"""
MCP Server for Jira Integration
Provides tools to fetch projects, epics, and user stories from Jira
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth
import logging

# MCP SDK imports (you'll need to install mcp package)
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraClient:
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Jira API"""
        url = f"{self.base_url}/rest/api/3/{endpoint}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API request failed: {e}")
            raise
    
    def get_projects(self) -> List[Dict]:
        """Fetch all accessible projects"""
        return self._make_request("project")
    
    def get_project_details(self, project_key: str) -> Dict:
        """Get detailed information about a specific project"""
        return self._make_request(f"project/{project_key}")
    
    def search_issues(self, jql: str, fields: List[str] = None, max_results: int = 50) -> Dict:
        """Search for issues using JQL"""
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': ','.join(fields) if fields else 'summary,status,assignee,priority,issuetype,created,updated'
        }
        return self._make_request("search", params)
    
    def get_epics(self, project_key: str) -> List[Dict]:
        """Fetch epics for a project"""
        jql = f'project = "{project_key}" AND issuetype = Epic'
        result = self.search_issues(jql)
        return result.get('issues', [])
    
    def get_user_stories(self, project_key: str, epic_key: str = None) -> List[Dict]:
        """Fetch user stories, optionally filtered by epic"""
        if epic_key:
            jql = f'project = "{project_key}" AND issuetype = Story AND "Epic Link" = "{epic_key}"'
        else:
            jql = f'project = "{project_key}" AND issuetype = Story'
        result = self.search_issues(jql)
        return result.get('issues', [])

# Initialize Jira client
jira_client = None

def init_jira_client():
    """Initialize Jira client with environment variables"""
    global jira_client
    base_url = os.getenv('JIRA_BASE_URL')
    username = os.getenv('JIRA_USERNAME')
    api_token = os.getenv('JIRA_API_TOKEN')
    
    if not all([base_url, username, api_token]):
        raise ValueError("Missing required environment variables: JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN")
    
    jira_client = JiraClient(base_url, username, api_token)

# Create MCP server
server = Server("jira-mcp-server")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Jira tools"""
    return [
        Tool(
            name="get_projects",
            description="Fetch all accessible Jira projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_project_details",
            description="Get detailed information about a specific Jira project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "The project key (e.g., 'PROJ')"
                    }
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="get_epics",
            description="Fetch all epics for a specific project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "The project key (e.g., 'PROJ')"
                    }
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="get_user_stories",
            description="Fetch user stories, optionally filtered by epic",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "The project key (e.g., 'PROJ')"
                    },
                    "epic_key": {
                        "type": "string",
                        "description": "Optional epic key to filter stories"
                    }
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="search_issues",
            description="Search for issues using JQL (Jira Query Language)",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                },
                "required": ["jql"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    if not jira_client:
        return [TextContent(
            type="text",
            text="Jira client not initialized. Please check environment variables."
        )]
    
    try:
        if name == "get_projects":
            projects = jira_client.get_projects()
            return [TextContent(
                type="text",
                text=json.dumps(projects, indent=2)
            )]
        
        elif name == "get_project_details":
            project_key = arguments.get("project_key")
            project = jira_client.get_project_details(project_key)
            return [TextContent(
                type="text",
                text=json.dumps(project, indent=2)
            )]
        
        elif name == "get_epics":
            project_key = arguments.get("project_key")
            epics = jira_client.get_epics(project_key)
            return [TextContent(
                type="text",
                text=json.dumps(epics, indent=2)
            )]
        
        elif name == "get_user_stories":
            project_key = arguments.get("project_key")
            epic_key = arguments.get("epic_key")
            stories = jira_client.get_user_stories(project_key, epic_key)
            return [TextContent(
                type="text",
                text=json.dumps(stories, indent=2)
            )]
        
        elif name == "search_issues":
            jql = arguments.get("jql")
            max_results = arguments.get("max_results", 50)
            results = jira_client.search_issues(jql, max_results=max_results)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Main server function"""
    try:
        init_jira_client()
        logger.info("Jira MCP Server starting...")
        
        async with stdio_server(server) as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="jira-mcp-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
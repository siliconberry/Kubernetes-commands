import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="Jirabot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class JiraAPI:
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
            st.error(f"Jira API request failed: {e}")
            return {}
    
    def get_projects(self) -> List[Dict]:
        """Fetch all accessible projects"""
        result = self._make_request("project")
        return result if isinstance(result, list) else []
    
    def search_issues(self, jql: str, fields: List[str] = None, max_results: int = 100) -> Dict:
        """Search for issues using JQL"""
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': ','.join(fields) if fields else 'summary,status,assignee,priority,issuetype,created,updated,description'
        }
        return self._make_request("search", params)
    
    def get_epics(self, project_key: str) -> List[Dict]:
        """Fetch epics for a project"""
        jql = f'project = "{project_key}" AND issuetype = Epic ORDER BY created DESC'
        result = self.search_issues(jql)
        return result.get('issues', [])
    
    def get_user_stories(self, project_key: str, epic_key: str = None) -> List[Dict]:
        """Fetch user stories"""
        if epic_key:
            jql = f'project = "{project_key}" AND issuetype = Story AND "Epic Link" = "{epic_key}" ORDER BY created DESC'
        else:
            jql = f'project = "{project_key}" AND issuetype = Story ORDER BY created DESC'
        result = self.search_issues(jql)
        return result.get('issues', [])

@st.cache_data
def load_jira_data(_jira_client, project_key):
    """Load and cache Jira data"""
    epics = _jira_client.get_epics(project_key)
    stories = _jira_client.get_user_stories(project_key)
    return epics, stories

def format_issue_data(issues: List[Dict]) -> pd.DataFrame:
    """Convert issues to DataFrame for display"""
    if not issues:
        return pd.DataFrame()
    
    data = []
    for issue in issues:
        fields = issue.get('fields', {})
        assignee = fields.get('assignee')
        assignee_name = assignee.get('displayName') if assignee else 'Unassigned'
        
        data.append({
            'Key': issue.get('key', ''),
            'Summary': fields.get('summary', ''),
            'Status': fields.get('status', {}).get('name', ''),
            'Type': fields.get('issuetype', {}).get('name', ''),
            'Priority': fields.get('priority', {}).get('name', ''),
            'Assignee': assignee_name,
            'Created': fields.get('created', ''),
            'Updated': fields.get('updated', '')
        })
    
    df = pd.DataFrame(data)
    if not df.empty:
        df['Created'] = pd.to_datetime(df['Created']).dt.strftime('%Y-%m-%d')
        df['Updated'] = pd.to_datetime(df['Updated']).dt.strftime('%Y-%m-%d')
    
    return df

def create_status_chart(df: pd.DataFrame, title: str):
    """Create status distribution chart"""
    if df.empty:
        return None
    
    status_counts = df['Status'].value_counts()
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(height=400)
    return fig

def main():
    st.title("🤖 Jirabot Dashboard")
    st.markdown("Connect to your Jira instance and explore projects, epics, and user stories")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Jira Configuration")
        
        # Connection settings
        jira_url = st.text_input(
            "Jira Base URL",
            placeholder="https://your-domain.atlassian.net",
            help="Your Jira instance URL"
        )
        
        username = st.text_input(
            "Username/Email",
            placeholder="your-email@company.com"
        )
        
        api_token = st.text_input(
            "API Token",
            type="password",
            help="Create an API token from your Jira account settings"
        )
        
        if st.button("Test Connection"):
            if all([jira_url, username, api_token]):
                try:
                    jira_client = JiraAPI(jira_url, username, api_token)
                    projects = jira_client.get_projects()
                    if projects:
                        st.success(f"✅ Connected! Found {len(projects)} projects")
                        st.session_state['jira_client'] = jira_client
                        st.session_state['projects'] = projects
                    else:
                        st.error("❌ Connection failed or no projects found")
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
            else:
                st.warning("Please fill in all connection details")
    
    # Main content area
    if 'jira_client' in st.session_state and 'projects' in st.session_state:
        jira_client = st.session_state['jira_client']
        projects = st.session_state['projects']
        
        # Project selection
        col1, col2 = st.columns([2, 1])
        with col1:
            project_options = {f"{p['key']} - {p['name']}": p['key'] for p in projects}
            selected_project = st.selectbox(
                "Select Project",
                options=list(project_options.keys()),
                index=0 if project_options else None
            )
        
        with col2:
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.rerun()
        
        if selected_project:
            project_key = project_options[selected_project]
            
            # Load data
            with st.spinner("Loading Jira data..."):
                epics, stories = load_jira_data(jira_client, project_key)
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Epics", "📝 User Stories", "🔍 Search"])
            
            with tab1:
                st.subheader(f"Project Overview: {project_key}")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Epics", len(epics))
                with col2:
                    st.metric("Total Stories", len(stories))
                with col3:
                    epic_df = format_issue_data(epics)
                    done_epics = len(epic_df[epic_df['Status'].str.contains('Done|Closed', case=False, na=False)]) if not epic_df.empty else 0
                    st.metric("Completed Epics", done_epics)
                with col4:
                    story_df = format_issue_data(stories)
                    done_stories = len(story_df[story_df['Status'].str.contains('Done|Closed', case=False, na=False)]) if not story_df.empty else 0
                    st.metric("Completed Stories", done_stories)
                
                # Charts
                col1, col2 = st.columns(2)
                with col1:
                    epic_chart = create_status_chart(epic_df, "Epic Status Distribution")
                    if epic_chart:
                        st.plotly_chart(epic_chart, use_container_width=True)
                
                with col2:
                    story_chart = create_status_chart(story_df, "Story Status Distribution")
                    if story_chart:
                        st.plotly_chart(story_chart, use_container_width=True)
            
            with tab2:
                st.subheader("🎯 Epics")
                epic_df = format_issue_data(epics)
                
                if not epic_df.empty:
                    # Filters
                    col1, col2 = st.columns(2)
                    with col1:
                        status_filter = st.multiselect(
                            "Filter by Status",
                            options=epic_df['Status'].unique(),
                            default=epic_df['Status'].unique()
                        )
                    with col2:
                        assignee_filter = st.multiselect(
                            "Filter by Assignee",
                            options=epic_df['Assignee'].unique(),
                            default=epic_df['Assignee'].unique()
                        )
                    
                    # Apply filters
                    filtered_df = epic_df[
                        (epic_df['Status'].isin(status_filter)) &
                        (epic_df['Assignee'].isin(assignee_filter))
                    ]
                    
                    st.dataframe(filtered_df, use_container_width=True)
                    
                    # Epic details
                    if st.checkbox("Show Epic Details"):
                        selected_epic = st.selectbox(
                            "Select Epic for Details",
                            options=filtered_df['Key'].tolist()
                        )
                        if selected_epic:
                            epic_stories = jira_client.get_user_stories(project_key, selected_epic)
                            st.write(f"**Stories in {selected_epic}:**")
                            if epic_stories:
                                story_df = format_issue_data(epic_stories)
                                st.dataframe(story_df, use_container_width=True)
                            else:
                                st.info("No stories found for this epic")
                else:
                    st.info("No epics found for this project")
            
            with tab3:
                st.subheader("📝 User Stories")
                story_df = format_issue_data(stories)
                
                if not story_df.empty:
                    # Filters
                    col1, col2 = st.columns(2)
                    with col1:
                        status_filter = st.multiselect(
                            "Filter by Status",
                            options=story_df['Status'].unique(),
                            default=story_df['Status'].unique(),
                            key="story_status"
                        )
                    with col2:
                        assignee_filter = st.multiselect(
                            "Filter by Assignee",
                            options=story_df['Assignee'].unique(),
                            default=story_df['Assignee'].unique(),
                            key="story_assignee"
                        )
                    
                    # Apply filters
                    filtered_df = story_df[
                        (story_df['Status'].isin(status_filter)) &
                        (story_df['Assignee'].isin(assignee_filter))
                    ]
                    
                    st.dataframe(filtered_df, use_container_width=True)
                else:
                    st.info("No user stories found for this project")
            
            with tab4:
                st.subheader("🔍 Advanced Search")
                st.markdown("Use JQL (Jira Query Language) to search for specific issues")
                
                # JQL examples
                with st.expander("JQL Examples"):
                    st.code(f'project = "{project_key}" AND status = "In Progress"')
                    st.code(f'project = "{project_key}" AND assignee = currentUser()')
                    st.code(f'project = "{project_key}" AND created >= -7d')
                    st.code(f'project = "{project_key}" AND priority = High')
                
                jql_query = st.text_area(
                    "JQL Query",
                    value=f'project = "{project_key}"',
                    height=100
                )
                
                max_results = st.slider("Max Results", 10, 500, 50)
                
                if st.button("Execute Search"):
                    if jql_query:
                        with st.spinner("Searching..."):
                            results = jira_client.search_issues(jql_query, max_results=max_results)
                            issues = results.get('issues', [])
                            
                        if issues:
                            search_df = format_issue_data(issues)
                            st.success(f"Found {len(issues)} issues")
                            st.dataframe(search_df, use_container_width=True)
                            
                            # Download option
                            csv = search_df.to_csv(index=False)
                            st.download_button(
                                "Download Results as CSV",
                                csv,
                                f"jira_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                "text/csv"
                            )
                        else:
                            st.info("No issues found matching your query")
                    else:
                        st.warning("Please enter a JQL query")
    
    else:
        # Welcome screen
        st.markdown("""
        ### Welcome to Jirabot! 🤖
        
        To get started:
        1. Enter your Jira connection details in the sidebar
        2. Click "Test Connection" to verify your credentials
        3. Select a project to explore epics and user stories
        
        #### Features:
        - 📊 **Project Overview**: Get insights into your project's progress
        - 🎯 **Epic Management**: View and filter epics
        - 📝 **User Stories**: Browse and manage user stories
        - 🔍 **Advanced Search**: Use JQL for custom queries
        
        #### Setup Requirements:
        - Jira Cloud instance URL
        - Valid username/email
        - API token (generated from Jira account settings)
        """)

if __name__ == "__main__":
    main()
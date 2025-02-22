import requests
import json
import os

# Configuration
source_url = "http://source-grafana:3000"
target_url = "http://target-grafana:3000"
source_api_key = "YOUR_SOURCE_API_KEY"  # Admin API key from source
target_api_key = "YOUR_TARGET_API_KEY"  # Admin API key from target

# Headers for API requests
source_headers = {
    "Authorization": f"Bearer {source_api_key}",
    "Content-Type": "application/json"
}

target_headers = {
    "Authorization": f"Bearer {target_api_key}",
    "Content-Type": "application/json"
}

# Create directory for exported dashboards
if not os.path.exists("exported_dashboards"):
    os.makedirs("exported_dashboards")

# Step 1: Get all folders from source
def get_all_folders():
    response = requests.get(f"{source_url}/api/folders", headers=source_headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get folders: {response.text}")
        return []

# Step 2: Create folders on target
def create_folder(folder):
    # Skip the General folder (it always exists)
    if folder['title'] == 'General':
        return folder['id']
    
    payload = {
        "title": folder['title'],
        "uid": folder['uid']
    }
    response = requests.post(f"{target_url}/api/folders", headers=target_headers, json=payload)
    if response.status_code == 200:
        print(f"Created folder: {folder['title']}")
        return response.json()['id']
    else:
        print(f"Failed to create folder: {response.text}")
        return None

# Step 3: Get dashboards in a folder
def get_dashboards_in_folder(folder_id):
    response = requests.get(f"{source_url}/api/search?folderIds={folder_id}&type=dash-db", headers=source_headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get dashboards in folder {folder_id}: {response.text}")
        return []

# Step 4: Export a dashboard
def export_dashboard(dashboard_uid):
    response = requests.get(f"{source_url}/api/dashboards/uid/{dashboard_uid}", headers=source_headers)
    if response.status_code == 200:
        dashboard_data = response.json()
        # Remove fields that shouldn't be included in import
        dashboard_data['dashboard']['id'] = None
        dashboard_data['dashboard']['version'] = None
        
        # Save to file (optional)
        with open(f"exported_dashboards/{dashboard_uid}.json", 'w') as f:
            json.dump(dashboard_data, f, indent=2)
            
        return dashboard_data
    else:
        print(f"Failed to export dashboard {dashboard_uid}: {response.text}")
        return None

# Step 5: Import dashboard to target
def import_dashboard(dashboard_data, folder_id):
    payload = {
        "dashboard": dashboard_data['dashboard'],
        "overwrite": True,
        "folderId": folder_id,
        "message": "Migrated from source Grafana"
    }
    
    response = requests.post(f"{target_url}/api/dashboards/db", headers=target_headers, json=payload)
    if response.status_code == 200:
        print(f"Imported dashboard: {dashboard_data['dashboard']['title']}")
        return True
    else:
        print(f"Failed to import dashboard: {response.text}")
        return False

# Main migration process
def migrate_all():
    # Get and create folders
    folders = get_all_folders()
    folder_id_mapping = {}  # Maps source folder IDs to target folder IDs
    
    # General folder is always available
    general_folder_info = next((f for f in folders if f['title'] == 'General'), {'id': 0})
    folder_id_mapping[general_folder_info['id']] = 0
    
    # Process other folders
    for folder in folders:
        if folder['title'] != 'General':
            target_folder_id = create_folder(folder)
            if target_folder_id:
                folder_id_mapping[folder['id']] = target_folder_id
    
    # Migrate dashboards in each folder
    for source_folder_id, target_folder_id in folder_id_mapping.items():
        dashboards = get_dashboards_in_folder(source_folder_id)
        for dashboard in dashboards:
            dashboard_data = export_dashboard(dashboard['uid'])
            if dashboard_data:
                import_dashboard(dashboard_data, target_folder_id)

# Run the migration
if __name__ == "__main__":
    print("Starting Grafana migration...")
    migrate_all()
    print("Migration completed.")

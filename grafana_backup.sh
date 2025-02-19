./configure \
    --prefix=$HOME/php82 \
    --with-config-file-path=$HOME/php82/etc \
    --with-config-file-scan-dir=$HOME/php82/etc/conf.d \
    --enable-bcmath \
    --enable-mbstring \
    --enable-zip \
    --with-openssl \
    --with-curl \
    --with-sodium \
    --enable-fpm \
    --with-zlib

#!/bin/bash

# Configuration
API_KEY="<YOUR_GRAFANA_API_KEY>"
GRAFANA_HOST="http://<YOUR_GRAFANA_HOST>"  # Replace with your Grafana host (e.g., http://localhost:3000)
OUTPUT_DIR="./grafana_backup"             # Directory to store JSON files

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Step 1: Query all folders
echo "Fetching folders..."
folders=$(curl -s -H "Authorization: Bearer $API_KEY" \
          -X GET "$GRAFANA_HOST/api/folders")

# Check if folders were retrieved successfully
if [[ -z "$folders" || "$folders" == "[]" ]]; then
  echo "No folders found or failed to fetch folders."
  exit 1
fi

# Step 2: Loop through each folder and query its dashboards
echo "$folders" | jq -c '.[]' | while IFS= read -r folder; do
  folder_uid=$(echo "$folder" | jq -r '.uid')
  folder_title=$(echo "$folder" | jq -r '.title')

  echo "Processing folder: $folder_title (UID: $folder_uid)"

  # Save folder metadata to a JSON file
  folder_file="$OUTPUT_DIR/folder_$folder_uid.json"
  echo "$folder" > "$folder_file"
  echo "  Folder metadata saved to $folder_file"

  # Query dashboards in the folder
  dashboards=$(curl -s -H "Authorization: Bearer $API_KEY" \
               -X GET "$GRAFANA_HOST/api/search?folderIds=$folder_uid")

  # Check if dashboards exist in the folder
  if [[ "$dashboards" == "[]" ]]; then
    echo "  No dashboards found in this folder."
    continue
  fi

  # Process each dashboard
  echo "$dashboards" | jq -c '.[]' | while IFS= read -r dashboard; do
    dashboard_uid=$(echo "$dashboard" | jq -r '.uid')
    dashboard_title=$(echo "$dashboard" | jq -r '.title')

    echo "  Processing dashboard: $dashboard_title (UID: $dashboard_uid)"

    # Fetch the full dashboard JSON
    dashboard_json=$(curl -s -H "Authorization: Bearer $API_KEY" \
                    -X GET "$GRAFANA_HOST/api/dashboards/uid/$dashboard_uid")

    # Save the dashboard JSON to a file
    dashboard_file="$OUTPUT_DIR/dashboard_$dashboard_uid.json"
    echo "$dashboard_json" > "$dashboard_file"
    echo "    Dashboard saved to $dashboard_file"
  done
done

echo "Backup completed. All folders and dashboards are saved in the '$OUTPUT_DIR' directory."

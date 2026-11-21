#!/bin/bash
#
# Grafana Dashboard Export/Import Script
# Exports or imports all dashboards from/to Grafana
#
# Usage:
#   Export: ./grafana-dashboard-backup.sh export <GRAFANA_URL> <API_KEY> [BACKUP_DIR] [OPTIONS]
#   Import: ./grafana-dashboard-backup.sh import <GRAFANA_URL> <API_KEY> <BACKUP_DIR> [OPTIONS]
#
# Options:
#   --exclude-folders "Folder1,Folder2"   Exclude specific folders
#   --include-folders "Folder1,Folder2"   Include only specific folders (excludes all others)
#
# Examples:
#   ./grafana-dashboard-backup.sh export https://grafana.example.com <api-key>
#   ./grafana-dashboard-backup.sh export https://grafana.example.com <api-key> ./backup --exclude-folders "General"
#   ./grafana-dashboard-backup.sh import https://grafana.example.com <api-key> ./backup
#   ./grafana-dashboard-backup.sh import https://grafana.example.com <api-key> ./backup --exclude-folders "General"
#   ./grafana-dashboard-backup.sh import https://grafana.example.com <api-key> ./backup --include-folders "Production,Alerts"
#

set -e

ACTION="${1:-}"
GRAFANA_URL="${2:-}"
API_KEY="${3:-}"
BACKUP_DIR="${4:-}"
EXCLUDE_FOLDERS=""
INCLUDE_FOLDERS=""

# Parse additional options
shift 4 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --exclude-folders)
            EXCLUDE_FOLDERS="$2"
            shift 2
            ;;
        --include-folders)
            INCLUDE_FOLDERS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

usage() {
    echo "Grafana Dashboard Export/Import Script"
    echo ""
    echo "Usage:"
    echo "  Export: $0 export <GRAFANA_URL> <API_KEY> [BACKUP_DIR] [OPTIONS]"
    echo "  Import: $0 import <GRAFANA_URL> <API_KEY> <BACKUP_DIR> [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --exclude-folders \"Folder1,Folder2\"   Exclude specific folders"
    echo "  --include-folders \"Folder1,Folder2\"   Include only specific folders"
    echo ""
    echo "Examples:"
    echo "  $0 export https://grafana.example.com <api-key>"
    echo "  $0 export https://grafana.example.com <api-key> ./backup --exclude-folders \"General\""
    echo "  $0 import https://grafana.example.com <api-key> ./backup"
    echo "  $0 import https://grafana.example.com <api-key> ./backup --exclude-folders \"General\""
    echo "  $0 import https://grafana.example.com <api-key> ./backup --include-folders \"Production,Alerts\""
    echo ""
    echo "To get API key:"
    echo "  1. Go to Grafana > Administration > Service accounts"
    echo "  2. Create a service account with Admin role"
    echo "  3. Generate a token"
    exit 1
}

if [[ -z "$ACTION" || -z "$GRAFANA_URL" || -z "$API_KEY" ]]; then
    usage
fi

# Remove trailing slash from URL
GRAFANA_URL="${GRAFANA_URL%/}"

# Function to check if folder should be skipped
should_skip_folder() {
    local folder_name="$1"

    # If include list is specified, skip folders not in the list
    if [[ -n "$INCLUDE_FOLDERS" ]]; then
        if ! echo ",$INCLUDE_FOLDERS," | grep -qi ",$folder_name,"; then
            return 0  # Skip
        fi
    fi

    # If exclude list is specified, skip folders in the list
    if [[ -n "$EXCLUDE_FOLDERS" ]]; then
        if echo ",$EXCLUDE_FOLDERS," | grep -qi ",$folder_name,"; then
            return 0  # Skip
        fi
    fi

    return 1  # Don't skip
}

#######################################
# EXPORT FUNCTION
#######################################
do_export() {
    local backup_dir="${BACKUP_DIR:-.}"

    echo "=== Grafana Dashboard Export ==="
    echo "URL: $GRAFANA_URL"
    echo "Backup directory: $backup_dir"
    [[ -n "$EXCLUDE_FOLDERS" ]] && echo "Excluding folders: $EXCLUDE_FOLDERS"
    [[ -n "$INCLUDE_FOLDERS" ]] && echo "Including only folders: $INCLUDE_FOLDERS"
    echo ""

    mkdir -p "$backup_dir/dashboards"

    # Get all folders
    echo "Fetching folders..."
    curl -sf -H "Authorization: Bearer $API_KEY" \
        "$GRAFANA_URL/api/folders" > "$backup_dir/folders.json"

    FOLDER_COUNT=$(jq length "$backup_dir/folders.json")
    echo "Found $FOLDER_COUNT folders"

    # Create folder structure (only for non-skipped folders)
    jq -r '.[] | "\(.uid)|\(.title)"' "$backup_dir/folders.json" | while IFS='|' read -r uid title; do
        if should_skip_folder "$title"; then
            continue
        fi
        safe_title=$(echo "$title" | tr '/' '_' | tr ' ' '_')
        mkdir -p "$backup_dir/dashboards/$safe_title"
        # Save folder metadata
        curl -sf -H "Authorization: Bearer $API_KEY" \
            "$GRAFANA_URL/api/folders/$uid" > "$backup_dir/dashboards/$safe_title/_folder.json" 2>/dev/null || true
    done

    # Create General folder for dashboards without folder (if not excluded)
    if ! should_skip_folder "General"; then
        mkdir -p "$backup_dir/dashboards/General"
    fi

    # Get all dashboards
    echo "Fetching dashboard list..."
    curl -sf -H "Authorization: Bearer $API_KEY" \
        "$GRAFANA_URL/api/search?type=dash-db&limit=5000" > "$backup_dir/dashboard-list.json"

    DASHBOARD_COUNT=$(jq length "$backup_dir/dashboard-list.json")
    echo "Found $DASHBOARD_COUNT dashboards"
    echo ""

    # Export each dashboard
    echo "Exporting dashboards..."
    local exported=0
    local skipped=0

    jq -r '.[] | "\(.uid)|\(.title)|\(.folderTitle // "General")"' "$backup_dir/dashboard-list.json" | while IFS='|' read -r uid title folder; do
        # Check if folder should be skipped
        if should_skip_folder "$folder"; then
            echo "  ⊘ $folder / $title (skipped)"
            continue
        fi

        safe_folder=$(echo "$folder" | tr '/' '_' | tr ' ' '_')
        safe_title=$(echo "$title" | tr '/' '_' | tr ' ' '_' | tr -d '"' | tr -d "'" | cut -c1-100)

        mkdir -p "$backup_dir/dashboards/$safe_folder"

        if curl -sf -H "Authorization: Bearer $API_KEY" \
            "$GRAFANA_URL/api/dashboards/uid/$uid" > "$backup_dir/dashboards/$safe_folder/${safe_title}.json" 2>/dev/null; then
            echo "  ✓ $folder / $title"
        else
            echo "  ✗ $folder / $title (failed)"
        fi
    done

    # Summary
    echo ""
    echo "=== Export Complete ==="
    echo "Location: $backup_dir"
    echo ""
    echo "To import: $0 import <GRAFANA_URL> <API_KEY> $backup_dir"
}

#######################################
# IMPORT FUNCTION
#######################################
do_import() {
    if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
        echo "Error: Backup directory not specified or doesn't exist"
        usage
    fi

    echo "=== Grafana Dashboard Import ==="
    echo "URL: $GRAFANA_URL"
    echo "Source directory: $BACKUP_DIR"
    [[ -n "$EXCLUDE_FOLDERS" ]] && echo "Excluding folders: $EXCLUDE_FOLDERS"
    [[ -n "$INCLUDE_FOLDERS" ]] && echo "Including only folders: $INCLUDE_FOLDERS"
    echo ""

    # Import folders first (skip excluded/non-included)
    if [[ -f "$BACKUP_DIR/folders.json" ]]; then
        echo "Importing folders..."
        jq -c '.[]' "$BACKUP_DIR/folders.json" | while read -r folder; do
            title=$(echo "$folder" | jq -r '.title')
            uid=$(echo "$folder" | jq -r '.uid')

            # Check if folder should be skipped
            if should_skip_folder "$title"; then
                echo "  ⊘ $title (skipped by filter)"
                continue
            fi

            # Check if folder exists
            if curl -sf -H "Authorization: Bearer $API_KEY" "$GRAFANA_URL/api/folders/$uid" > /dev/null 2>&1; then
                echo "  - $title (exists)"
            else
                # Create folder
                payload=$(echo "$folder" | jq '{uid: .uid, title: .title}')
                if curl -sf -X POST -H "Authorization: Bearer $API_KEY" \
                    -H "Content-Type: application/json" \
                    -d "$payload" \
                    "$GRAFANA_URL/api/folders" > /dev/null 2>&1; then
                    echo "  ✓ $title (created)"
                else
                    echo "  ✗ $title (failed)"
                fi
            fi
        done
        echo ""
    fi

    # Import dashboards
    echo "Importing dashboards..."

    # Get list of dashboard folders in backup
    for folder_dir in "$BACKUP_DIR/dashboards"/*/; do
        [[ -d "$folder_dir" ]] || continue

        folder_name=$(basename "$folder_dir" | tr '_' ' ')

        # Check if folder should be skipped
        if should_skip_folder "$folder_name"; then
            echo "  ⊘ Skipping folder: $folder_name"
            continue
        fi

        echo "  Processing folder: $folder_name"

        for file in "$folder_dir"*.json; do
            [[ -f "$file" ]] || continue
            [[ "$(basename "$file")" == "_folder.json" ]] && continue

            # Skip if not a valid dashboard file
            if ! jq -e '.dashboard' "$file" > /dev/null 2>&1; then
                continue
            fi

            title=$(jq -r '.dashboard.title // "unknown"' "$file")

            # Prepare import payload
            payload=$(jq '{
                dashboard: (.dashboard | del(.id) | .version = null),
                folderUid: .meta.folderUid,
                overwrite: true,
                message: "Imported from backup"
            }' "$file")

            response=$(curl -sf -X POST -H "Authorization: Bearer $API_KEY" \
                -H "Content-Type: application/json" \
                -d "$payload" \
                "$GRAFANA_URL/api/dashboards/db" 2>&1) || true

            if echo "$response" | jq -e '.status == "success"' > /dev/null 2>&1; then
                echo "    ✓ $title"
            elif echo "$response" | grep -q "name-exists\|uid-exists"; then
                echo "    - $title (exists)"
            else
                echo "    ✗ $title ($(echo "$response" | jq -r '.message // "failed"' 2>/dev/null))"
            fi
        done
    done

    echo ""
    echo "=== Import Complete ==="
}

#######################################
# MAIN
#######################################
case "$ACTION" in
    export)
        do_export
        ;;
    import)
        do_import
        ;;
    *)
        echo "Error: Unknown action '$ACTION'"
        usage
        ;;
esac

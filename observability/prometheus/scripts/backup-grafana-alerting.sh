#!/bin/bash
#
# Grafana Alerting Export/Import Script
# Exports or imports all alerting configuration (rules, contact points, policies, etc.)
#
# Usage:
#   Export: ./grafana-alerting-backup.sh export <GRAFANA_URL> <API_KEY> [BACKUP_DIR]
#   Import: ./grafana-alerting-backup.sh import <GRAFANA_URL> <API_KEY> <BACKUP_DIR>
#
# Examples:
#   ./grafana-alerting-backup.sh export https://grafana.example.com <api-key>
#   ./grafana-alerting-backup.sh import https://grafana.example.com <api-key> ./grafana-alerting-backup-20260220
#

set -e

ACTION="${1:-}"
GRAFANA_URL="${2:-}"
API_KEY="${3:-}"
BACKUP_DIR="${4:-}"

usage() {
    echo "Grafana Alerting Export/Import Script"
    echo ""
    echo "Usage:"
    echo "  Export: $0 export <GRAFANA_URL> <API_KEY> [BACKUP_DIR]"
    echo "  Import: $0 import <GRAFANA_URL> <API_KEY> <BACKUP_DIR>"
    echo ""
    echo "Examples:"
    echo "  $0 export https://grafana.example.com <api-key>"
    echo "  $0 import https://grafana.example.com <api-key> ./backup-dir"
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

# Common headers
AUTH_HEADER="Authorization: Bearer $API_KEY"

#######################################
# EXPORT FUNCTION
#######################################
do_export() {
    local backup_dir="${BACKUP_DIR:-.}"

    echo "=== Grafana Alerting Export ==="
    echo "URL: $GRAFANA_URL"
    echo "Backup directory: $backup_dir"
    echo ""

    mkdir -p "$backup_dir/alert-rules-by-folder"

    # Function to export with error handling
    export_resource() {
        local name="$1"
        local endpoint="$2"
        local output="$3"

        echo -n "Exporting $name... "
        local response
        response=$(curl -s -w "\n%{http_code}" -H "$AUTH_HEADER" "$GRAFANA_URL$endpoint" 2>/dev/null)
        local http_code=$(echo "$response" | tail -1)
        local body=$(echo "$response" | sed '$d')

        if [[ "$http_code" == "200" ]]; then
            echo "$body" > "$output"
            # Check if response is empty array or object
            local count=$(echo "$body" | jq 'if type == "array" then length elif type == "object" then (if . == {} then 0 else 1 end) else 1 end' 2>/dev/null || echo "0")
            if [[ "$count" == "0" ]]; then
                echo "✓ (empty - no items found)"
            else
                echo "✓ ($count items)"
            fi
            return 0
        elif [[ "$http_code" == "404" ]]; then
            echo "⊘ (not found - feature may not be enabled)"
            echo "[]" > "$output"
            return 0
        else
            echo "✗ (HTTP $http_code)"
            echo "[]" > "$output"
            return 1
        fi
    }

    # Export all alert rules
    export_resource "Alert Rules" "/api/v1/provisioning/alert-rules" "$backup_dir/alert-rules.json"

    # Also try ruler API (alternative endpoint)
    echo -n "Exporting Alert Rules (ruler API)... "
    if curl -sf -H "$AUTH_HEADER" "$GRAFANA_URL/api/ruler/grafana/api/v1/rules" > "$backup_dir/alert-rules-ruler.json" 2>/dev/null; then
        local ruler_count=$(jq 'to_entries | map(.value | length) | add // 0' "$backup_dir/alert-rules-ruler.json" 2>/dev/null || echo "0")
        echo "✓ ($ruler_count rule groups)"
    else
        echo "⊘ (not available)"
        echo "{}" > "$backup_dir/alert-rules-ruler.json"
    fi

    # Export alert rules by folder (preserves group structure)
    echo "Exporting Alert Rules by folder..."
    curl -sf -H "$AUTH_HEADER" "$GRAFANA_URL/api/folders" 2>/dev/null | \
        jq -r '.[] | "\(.uid)|\(.title)"' | while IFS='|' read -r folder_uid folder_title; do
        safe_title=$(echo "$folder_title" | tr '/' '_' | tr ' ' '_')
        if curl -sf -H "$AUTH_HEADER" \
            "$GRAFANA_URL/api/v1/provisioning/folder/$folder_uid/rule-groups" > "$backup_dir/alert-rules-by-folder/${safe_title}.json" 2>/dev/null; then
            count=$(jq 'if type == "array" then length else 0 end' "$backup_dir/alert-rules-by-folder/${safe_title}.json" 2>/dev/null || echo "0")
            if [[ "$count" -gt 0 ]]; then
                echo "  ✓ $folder_title ($count groups)"
            fi
        fi
    done

    # Export contact points
    export_resource "Contact Points" "/api/v1/provisioning/contact-points" "$backup_dir/contact-points.json"

    # Export notification policies
    export_resource "Notification Policies" "/api/v1/provisioning/policies" "$backup_dir/notification-policies.json"

    # Export mute timings
    export_resource "Mute Timings" "/api/v1/provisioning/mute-timings" "$backup_dir/mute-timings.json"

    # Export notification templates
    export_resource "Notification Templates" "/api/v1/provisioning/templates" "$backup_dir/templates.json"

    # Export legacy alert notifications (Grafana < 9.0)
    export_resource "Legacy Alert Notifications" "/api/alert-notifications" "$backup_dir/legacy-alert-notifications.json"

    # Create combined backup file
    echo ""
    echo "Creating combined backup file..."
    jq -n \
        --arg url "$GRAFANA_URL" \
        --arg date "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --slurpfile rules "$backup_dir/alert-rules.json" \
        --slurpfile contacts "$backup_dir/contact-points.json" \
        --slurpfile policies "$backup_dir/notification-policies.json" \
        --slurpfile mute "$backup_dir/mute-timings.json" \
        --slurpfile templates "$backup_dir/templates.json" \
        '{
            exportDate: $date,
            grafanaUrl: $url,
            alertRules: $rules[0],
            contactPoints: $contacts[0],
            notificationPolicies: $policies[0],
            muteTimings: $mute[0],
            templates: $templates[0]
        }' > "$backup_dir/complete-alerting-backup.json"

    # Summary
    echo ""
    echo "=== Export Complete ==="
    echo "Location: $backup_dir"
    echo ""
    echo "Files:"
    ls -la "$backup_dir"/*.json 2>/dev/null | awk '{print "  " $NF ": " $5 " bytes"}'
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

    echo "=== Grafana Alerting Import ==="
    echo "URL: $GRAFANA_URL"
    echo "Source directory: $BACKUP_DIR"
    echo ""
    echo "WARNING: This will overwrite existing alerting configuration!"
    echo "Press Ctrl+C to cancel, or Enter to continue..."
    read -r

    # Import mute timings first (dependencies for policies)
    if [[ -f "$BACKUP_DIR/mute-timings.json" ]]; then
        echo "Importing Mute Timings..."
        jq -c '.[]' "$BACKUP_DIR/mute-timings.json" 2>/dev/null | while read -r timing; do
            name=$(echo "$timing" | jq -r '.name')

            # Try to update, if fails try to create
            response=$(curl -sf -X PUT -H "$AUTH_HEADER" \
                -H "Content-Type: application/json" \
                -H "X-Disable-Provenance: true" \
                -d "$timing" \
                "$GRAFANA_URL/api/v1/provisioning/mute-timings/$name" 2>&1) || \
            response=$(curl -sf -X POST -H "$AUTH_HEADER" \
                -H "Content-Type: application/json" \
                -H "X-Disable-Provenance: true" \
                -d "$timing" \
                "$GRAFANA_URL/api/v1/provisioning/mute-timings" 2>&1) || true

            if [[ -n "$response" ]] && ! echo "$response" | grep -q "error"; then
                echo "  ✓ $name"
            else
                echo "  ✗ $name"
            fi
        done
        echo ""
    fi

    # Import notification templates
    if [[ -f "$BACKUP_DIR/templates.json" ]]; then
        echo "Importing Notification Templates..."
        jq -c '.[]' "$BACKUP_DIR/templates.json" 2>/dev/null | while read -r template; do
            name=$(echo "$template" | jq -r '.name')

            response=$(curl -sf -X PUT -H "$AUTH_HEADER" \
                -H "Content-Type: application/json" \
                -H "X-Disable-Provenance: true" \
                -d "$template" \
                "$GRAFANA_URL/api/v1/provisioning/templates/$name" 2>&1) || \
            response=$(curl -sf -X POST -H "$AUTH_HEADER" \
                -H "Content-Type: application/json" \
                -H "X-Disable-Provenance: true" \
                -d "$template" \
                "$GRAFANA_URL/api/v1/provisioning/templates" 2>&1) || true

            if [[ -n "$response" ]] && ! echo "$response" | grep -q "error"; then
                echo "  ✓ $name"
            else
                echo "  ✗ $name"
            fi
        done
        echo ""
    fi

    # Import contact points
    if [[ -f "$BACKUP_DIR/contact-points.json" ]]; then
        echo "Importing Contact Points..."
        jq -c '.[]' "$BACKUP_DIR/contact-points.json" 2>/dev/null | while read -r contact; do
            name=$(echo "$contact" | jq -r '.name')
            uid=$(echo "$contact" | jq -r '.uid // empty')

            # Remove uid for creation, use name for identification
            contact_clean=$(echo "$contact" | jq 'del(.uid)')

            # Try to create (will fail if exists with same name)
            response=$(curl -sf -X POST -H "$AUTH_HEADER" \
                -H "Content-Type: application/json" \
                -H "X-Disable-Provenance: true" \
                -d "$contact_clean" \
                "$GRAFANA_URL/api/v1/provisioning/contact-points" 2>&1) || true

            if echo "$response" | grep -q "uid\|created"; then
                echo "  ✓ $name (created)"
            elif echo "$response" | grep -q "already exists"; then
                echo "  - $name (exists)"
            else
                echo "  ✗ $name ($(echo "$response" | jq -r '.message // "failed"' 2>/dev/null))"
            fi
        done
        echo ""
    fi

    # Import notification policies
    if [[ -f "$BACKUP_DIR/notification-policies.json" ]]; then
        echo "Importing Notification Policies..."
        policy=$(cat "$BACKUP_DIR/notification-policies.json")

        response=$(curl -sf -X PUT -H "$AUTH_HEADER" \
            -H "Content-Type: application/json" \
            -H "X-Disable-Provenance: true" \
            -d "$policy" \
            "$GRAFANA_URL/api/v1/provisioning/policies" 2>&1) || true

        if [[ -n "$response" ]] && ! echo "$response" | grep -q "error"; then
            echo "  ✓ Notification policies imported"
        else
            echo "  ✗ Failed to import notification policies"
        fi
        echo ""
    fi

    # Import alert rules by folder (preserves group structure)
    if [[ -d "$BACKUP_DIR/alert-rules-by-folder" ]]; then
        echo "Importing Alert Rules by folder..."

        for file in "$BACKUP_DIR/alert-rules-by-folder"/*.json; do
            [[ -f "$file" ]] || continue

            folder_name=$(basename "$file" .json | tr '_' ' ')

            # Get folder UID from Grafana
            folder_uid=$(curl -sf -H "$AUTH_HEADER" "$GRAFANA_URL/api/folders" 2>/dev/null | \
                jq -r --arg name "$folder_name" '.[] | select(.title == $name) | .uid' | head -1)

            if [[ -z "$folder_uid" ]]; then
                echo "  ✗ Folder '$folder_name' not found, skipping"
                continue
            fi

            # Import each rule group
            jq -c '.[]' "$file" 2>/dev/null | while read -r group; do
                group_name=$(echo "$group" | jq -r '.name')

                response=$(curl -sf -X PUT -H "$AUTH_HEADER" \
                    -H "Content-Type: application/json" \
                    -H "X-Disable-Provenance: true" \
                    -d "$group" \
                    "$GRAFANA_URL/api/v1/provisioning/folder/$folder_uid/rule-groups/$group_name" 2>&1) || true

                if [[ -n "$response" ]] && ! echo "$response" | grep -q "error"; then
                    echo "  ✓ $folder_name / $group_name"
                else
                    echo "  ✗ $folder_name / $group_name"
                fi
            done
        done
        echo ""
    # Fallback: Import individual alert rules
    elif [[ -f "$BACKUP_DIR/alert-rules.json" ]]; then
        echo "Importing Alert Rules (individual)..."
        jq -c '.[]' "$BACKUP_DIR/alert-rules.json" 2>/dev/null | while read -r rule; do
            title=$(echo "$rule" | jq -r '.title')

            # Remove uid and provenance for clean import
            rule_clean=$(echo "$rule" | jq 'del(.uid, .provenance, .updated)')

            response=$(curl -sf -X POST -H "$AUTH_HEADER" \
                -H "Content-Type: application/json" \
                -H "X-Disable-Provenance: true" \
                -d "$rule_clean" \
                "$GRAFANA_URL/api/v1/provisioning/alert-rules" 2>&1) || true

            if echo "$response" | grep -q "uid"; then
                echo "  ✓ $title"
            else
                echo "  ✗ $title ($(echo "$response" | jq -r '.message // "failed"' 2>/dev/null))"
            fi
        done
        echo ""
    fi

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

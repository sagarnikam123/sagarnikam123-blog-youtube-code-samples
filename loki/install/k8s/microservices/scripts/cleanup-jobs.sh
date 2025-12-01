#!/bin/bash
set -e

echo "🧹 Cleaning up completed setup jobs..."

# Delete completed MinIO setup job
if kubectl get job minio-setup -n loki >/dev/null 2>&1; then
    JOB_STATUS=$(kubectl get job minio-setup -n loki -o jsonpath='{.status.conditions[0].type}')
    if [[ "$JOB_STATUS" == "Complete" ]]; then
        echo "✅ Deleting completed MinIO setup job..."
        kubectl delete job minio-setup -n loki
        echo "🗑️  MinIO setup job deleted"
    else
        echo "⏳ MinIO setup job still running, skipping deletion"
    fi
else
    echo "ℹ️  MinIO setup job not found"
fi

echo "✅ Cleanup complete!"

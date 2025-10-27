#!/bin/bash

# Loki Monolithic Stack Cleanup Script
# Stops all processes and cleans up temporary files

echo "🧹 Stopping all Loki stack processes..."

# Stop all running processes
echo "  Stopping Loki processes..."
ps aux | grep loki | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping log generators..."
ps aux | grep fake-log-generator | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep fuzzy-train | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep "python.*fuzzy-train" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping log collectors..."
ps aux | grep fluent-bit | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep vector | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep alloy | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping storage and monitoring..."
ps aux | grep minio | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep prometheus | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep grafana | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "🗑️  Cleaning up temporary files and directories..."

# Delete temporary files and directories
rm -rf /tmp/loki
rm -rf /tmp/prometheus
rm -rf $HOME/data/{loki,minio,loki-canary,log/logger}
rm -rf $HOME/data/prometheus/{data,wal}
rm -rf $HOME/data/fluent-bit/{flb-storage,fluent_bit.log,fluent-bit-loki.db,fluent-bit-loki.db-shm,fluent-bit-loki.db-wal}
rm -rf $HOME/data/vector/{buffer,data}
rm -rf $HOME/data/alloy/{data,wal}

echo "📁 Recreating directory structure..."

# Recreate directory structure
mkdir -p /tmp/loki/{chunks,compactor,index,index_cache,tsdb-cache,tsdb-index,wal,rules,bloom}
mkdir -p /tmp/prometheus/data
mkdir -p $HOME/data/{loki,minio,loki-canary}
mkdir -p $HOME/data/prometheus/{data,wal}
mkdir -p $HOME/data/{fluent-bit/flb-storage,log/logger}
mkdir -p $HOME/data/vector/{buffer,data}
mkdir -p $HOME/data/alloy/{data,wal}

echo "✅ Cleanup complete!"
echo ""
echo "📋 Next steps:"
echo "  • Run ./install.sh to reinstall components"
echo "  • Use ./start-loki.sh to start Loki"
echo "  • Check ./quick-start.sh for full stack startup"

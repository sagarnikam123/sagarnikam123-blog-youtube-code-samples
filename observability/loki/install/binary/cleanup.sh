#!/bin/bash

# Loki Monolithic Stack Cleanup Script
# Stops all processes and cleans up temporary files

echo "🧹 Loki Monolithic Stack Cleanup"
echo ""

# ============================================================================
# 🛑 Process Termination
# ============================================================================
echo "🛑 Stopping all Loki stack processes..."
echo "  Stopping Loki..."
ps aux | grep loki | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping Fake Log Generator..."
ps aux | grep fake-log-generator | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "  Stopping Fuzzy Train..."
ps aux | grep fuzzy-train | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep "python.*fuzzy-train" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping Fluent Bit..."
ps aux | grep fluent-bit | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "  Stopping Vector..."
ps aux | grep vector | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "  Stopping Alloy..."
ps aux | grep alloy | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping MinIO..."
ps aux | grep minio | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "  Stopping Prometheus..."
ps aux | grep prometheus | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "  Stopping Grafana..."
ps aux | grep grafana | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo ""

# ============================================================================
# 🗑️ Directory Cleanup
# ============================================================================
echo "🗑️ Cleaning up temporary files and directories..."
echo "  Removing /tmp/loki"
rm -rf /tmp/loki
echo "  Removing /tmp/prometheus"
rm -rf /tmp/prometheus
echo "  Removing $HOME/data/{loki,minio,loki-canary,log/logger}"
rm -rf $HOME/data/{loki,minio,loki-canary,log/logger}
echo "  Removing $HOME/data/prometheus/{data,wal}"
rm -rf $HOME/data/prometheus/{data,wal}
echo "  Removing $HOME/data/fluent-bit/{flb-storage,fluent_bit.log,flb_kube.db,fluent-bit-loki.db,fluent-bit-loki.db-shm,fluent-bit-loki.db-wal}"
rm -rf $HOME/data/fluent-bit/{flb-storage,fluent_bit.log,flb_kube.db,fluent-bit-loki.db,fluent-bit-loki.db-shm,fluent-bit-loki.db-wal}
echo "  Removing /tmp/fluent-bit-*.db (tail position tracking)"
rm -f /tmp/fluent-bit-*.db
echo "  Removing $HOME/data/vector/{buffer,data}"
rm -rf $HOME/data/vector/{buffer,data}
echo "  Removing $HOME/data/alloy/{data,wal}"
rm -rf $HOME/data/alloy/{data,wal}
echo ""

# ============================================================================
# 📁 Directory Recreation
# ============================================================================
echo "📁 Recreating directory structure..."
echo "  Creating /tmp/loki/{chunks,compactor,index,index_cache,tsdb-cache,tsdb-index,wal,rules,bloom}"
mkdir -p /tmp/loki/{chunks,compactor,index,index_cache,tsdb-cache,tsdb-index,wal,rules,bloom}
echo "  Creating /tmp/prometheus/data"
mkdir -p /tmp/prometheus/data
echo "  Creating $HOME/data/{loki,minio,loki-canary}"
mkdir -p $HOME/data/{loki,minio,loki-canary}
echo "  Creating $HOME/data/prometheus/{data,wal}"
mkdir -p $HOME/data/prometheus/{data,wal}
echo "  Creating $HOME/data/{fluent-bit/flb-storage,log/logger}"
mkdir -p $HOME/data/{fluent-bit/flb-storage,log/logger}
echo "  Creating $HOME/data/vector/{buffer,data}"
mkdir -p $HOME/data/vector/{buffer,data}
echo "  Creating $HOME/data/alloy/{data,wal}"
mkdir -p $HOME/data/alloy/{data,wal}
echo ""

echo "✅ Cleanup complete!"
echo ""
echo "📋 Next steps:"
echo "  • Run ./install.sh to reinstall components"
echo "  • Use ./start-loki.sh to start Loki"
echo "  • Check ./quick-start.sh for full stack startup"

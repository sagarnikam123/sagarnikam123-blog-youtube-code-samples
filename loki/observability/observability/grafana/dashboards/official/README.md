# Official Loki Grafana Dashboards

## 📊 Dashboard Collection

Downloaded from: https://github.com/grafana/loki/tree/main/production/loki-mixin-compiled/dashboards

**Total Dashboards**: 13 official production-ready dashboards

---

## 📁 Dashboard Categories

### **🔍 Core Monitoring**

#### **1. loki-operational.json** (238KB)
- **Purpose**: Overall Loki cluster health and performance
- **Key Metrics**: Request rates, latency, error rates, resource usage
- **Best For**: Primary monitoring dashboard
- **Monolithic Relevance**: ⭐⭐⭐⭐⭐ Essential

#### **2. loki-reads.json** (134KB)
- **Purpose**: Query performance and read path monitoring
- **Key Metrics**: Query latency, QPS, cache hit rates, query errors
- **Best For**: Query performance optimization
- **Monolithic Relevance**: ⭐⭐⭐⭐⭐ Essential

#### **3. loki-writes.json** (78KB)
- **Purpose**: Ingestion performance and write path monitoring
- **Key Metrics**: Ingestion rates, distributor performance, ingester health
- **Best For**: Ingestion troubleshooting
- **Monolithic Relevance**: ⭐⭐⭐⭐⭐ Essential

### **💾 Storage & Performance**

#### **4. loki-chunks.json** (45KB)
- **Purpose**: Chunk store performance and storage efficiency
- **Key Metrics**: Chunks per query, storage latency, deduplication
- **Best For**: Storage optimization
- **Monolithic Relevance**: ⭐⭐⭐⭐ Important

#### **5. loki-retention.json** (55KB)
- **Purpose**: Data retention and compaction monitoring
- **Key Metrics**: Compaction status, retention policies, storage cleanup
- **Best For**: Storage lifecycle management
- **Monolithic Relevance**: ⭐⭐⭐⭐ Important

### **📈 Resource Monitoring**

#### **6. loki-reads-resources.json** (97KB)
- **Purpose**: Resource usage for read components (querier, query-frontend)
- **Key Metrics**: CPU, memory, network usage for read path
- **Best For**: Capacity planning for queries
- **Monolithic Relevance**: ⭐⭐⭐ Useful

#### **7. loki-writes-resources.json** (32KB)
- **Purpose**: Resource usage for write components (distributor, ingester)
- **Key Metrics**: CPU, memory, network usage for write path
- **Best For**: Capacity planning for ingestion
- **Monolithic Relevance**: ⭐⭐⭐ Useful

### **🔧 Advanced Features**

#### **8. loki-bloom-build.json** (260KB)
- **Purpose**: Bloom filter build process monitoring (Loki 3.0+)
- **Key Metrics**: Bloom build performance, filter effectiveness
- **Best For**: Advanced query optimization
- **Monolithic Relevance**: ⭐⭐ Advanced

#### **9. loki-bloom-gateway.json** (239KB)
- **Purpose**: Bloom gateway performance monitoring (Loki 3.0+)
- **Key Metrics**: Bloom filter queries, cache performance
- **Best For**: Query acceleration monitoring
- **Monolithic Relevance**: ⭐⭐ Advanced

#### **10. loki-deletion.json** (27KB)
- **Purpose**: Log deletion and data management
- **Key Metrics**: Deletion requests, cleanup status
- **Best For**: Data compliance and cleanup
- **Monolithic Relevance**: ⭐⭐ Specialized

### **📊 Meta & Storage**

#### **11. loki-logs.json** (30KB)
- **Purpose**: Loki's own internal logs analysis
- **Key Metrics**: Internal log patterns, error analysis
- **Best For**: Troubleshooting Loki itself
- **Monolithic Relevance**: ⭐⭐⭐ Debugging

#### **12. loki-mixin-recording-rules.json** (23KB)
- **Purpose**: Recording rules performance monitoring
- **Key Metrics**: Rule evaluation, recording rule health
- **Best For**: Monitoring recording rules we created
- **Monolithic Relevance**: ⭐⭐⭐⭐ Important

#### **13. loki-thanos-object-storage.json** (31KB)
- **Purpose**: Thanos object storage integration monitoring
- **Key Metrics**: Object storage performance with Thanos
- **Best For**: Thanos integration environments
- **Monolithic Relevance**: ⭐ Specialized

---

## 🎯 Recommended Dashboard Priority for Monolithic

### **Phase 1: Essential (Start Here)**
1. **loki-operational.json** - Overall health
2. **loki-reads.json** - Query performance
3. **loki-writes.json** - Ingestion performance
4. **loki-chunks.json** - Storage efficiency

### **Phase 2: Important (Week 2)**
5. **loki-retention.json** - Data lifecycle
6. **loki-mixin-recording-rules.json** - Recording rules health
7. **loki-logs.json** - Internal troubleshooting

### **Phase 3: Advanced (Month 1)**
8. **loki-reads-resources.json** - Resource monitoring
9. **loki-writes-resources.json** - Capacity planning
10. **loki-bloom-*.json** - Advanced features (if using Loki 3.0+)

### **Phase 4: Specialized (As Needed)**
11. **loki-deletion.json** - Data compliance
12. **loki-thanos-object-storage.json** - If using Thanos

---

## 🔧 Integration Steps

### **1. Grafana Dashboard Import**
```bash
# Method 1: Manual Import
# 1. Open Grafana UI (http://localhost:3000)
# 2. Go to Dashboards > Import
# 3. Upload JSON files from this directory

# Method 2: Automated Import (if using Grafana provisioning)
# Copy dashboards to Grafana provisioning directory
```

### **2. Variable Configuration**
Most dashboards use these variables that need configuration:
- `$cluster` - Set to your cluster name (e.g., "local")
- `$namespace` - Set to your namespace (e.g., "default")
- `$datasource` - Set to your Prometheus datasource

### **3. Label Adaptation**
Dashboards expect distributed Loki labels. For monolithic, you may need to:
- Remove `cluster` and `namespace` filters
- Simplify job selectors (e.g., `job=~"loki.*"`)
- Adjust component-specific queries

---

## 📊 Dashboard Customization Tips

### **For Monolithic Setup**
```json
// Original distributed query:
{cluster=~"$cluster",job=~"($namespace)/query-frontend"}

// Monolithic adaptation:
{job=~"loki.*"}
```

### **Variable Simplification**
```json
// Remove cluster/namespace variables
// Keep only: datasource, job, instance
```

### **Panel Modifications**
- Remove cluster/namespace grouping in queries
- Simplify component selectors
- Focus on single-instance metrics

---

## 🚀 Quick Start

### **Import Priority Order**
1. Start with `loki-operational.json` for overview
2. Add `loki-reads.json` and `loki-writes.json` for detailed monitoring
3. Import others based on specific needs

### **Expected Adaptations**
- **Variables**: Simplify cluster/namespace variables
- **Queries**: Remove distributed-specific labels
- **Panels**: Focus on monolithic-relevant metrics

### **Validation**
- Check all panels load without errors
- Verify metrics are populated
- Adjust time ranges and refresh intervals

---

## 💡 Benefits

✅ **Production-Ready**: Battle-tested in production environments
✅ **Comprehensive**: Covers all Loki components and use cases
✅ **Best Practices**: Follows Grafana dashboard design principles
✅ **Maintained**: Kept up-to-date with latest Loki features
✅ **Professional**: High-quality visualizations and layouts

These official dashboards provide enterprise-grade monitoring capabilities for your Loki monolithic setup! 🎯

# MinIO Installation Guide

MinIO is a high-performance S3-compatible object storage.

## Installation Methods

### macOS

**Binary Download (ARM64):**
```bash
curl --progress-bar -O https://dl.min.io/aistor/minio/release/darwin-arm64/minio
chmod +x minio
./minio --version
```

**Binary Download (AMD64):**
```bash
curl --progress-bar -O https://dl.min.io/aistor/minio/release/darwin-amd64/minio
chmod +x minio
./minio --version
```

**Homebrew:**
```bash
brew install minio/stable/minio
```

### Linux

**Binary Download (AMD64):**
```bash
wget https://dl.min.io/aistor/minio/release/linux-amd64/minio
chmod +x minio
./minio --version
```

**Debian Package:**
```bash
wget https://dl.min.io/aistor/minio/release/linux-amd64/minio_20251017061741.0.0_amd64.deb
sudo dpkg -i minio_20251017061741.0.0_amd64.deb
minio --version
```

**RPM Package:**
```bash
sudo dnf install https://dl.min.io/aistor/minio/release/linux-amd64/minio-20251017061741.0.0-1.x86_64.rpm
minio --version
```

### Windows

**Binary Download:**
```powershell
Invoke-WebRequest -Uri "https://dl.min.io/aistor/minio/release/windows-amd64/minio.exe" -OutFile "minio.exe"
.\minio.exe --version
```

### Docker

```bash
docker pull minio/minio:latest
```

**Run MinIO Server:**
```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

### Kubernetes

**Helm:**
```bash
helm repo add minio https://charts.min.io/
helm install minio minio/minio
```

**Operator:**
```bash
kubectl apply -k "github.com/minio/operator?ref=v5.0.0"
```

## Quick Start

After installation, start MinIO server:

```bash
# Create data directory
mkdir -p ~/minio-data

# Start MinIO server
minio server ~/minio-data --console-address ":9001"
```

**Access URLs:**
- **API**: http://localhost:9000
- **Console**: http://localhost:9001
- **Credentials**: minioadmin / minioadmin

## MinIO Client (mc)

**Install mc:**
```bash
# macOS
brew install minio/stable/mc

# Linux
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc

# Windows
Invoke-WebRequest -Uri "https://dl.min.io/client/mc/release/windows-amd64/mc.exe" -OutFile "mc.exe"
```

**Configure mc:**
```bash
mc alias set myminio http://localhost:9000 minioadmin minioadmin
mc mb myminio/loki-data
```

## Platform-Specific Downloads

- **Kubernetes**: https://www.min.io/download?platform=kubernetes&installer=helm
- **Linux**: https://www.min.io/download?platform=linux&arch=amd64
- **Docker**: https://www.min.io/download?platform=docker
- **Windows**: https://www.min.io/download?platform=windows
- **macOS**: https://www.min.io/download?platform=macos

## Resources

- **Official Download**: https://www.min.io/download
- **GitHub Releases**: https://github.com/minio/minio/releases
- **Documentation**: https://docs.min.io/
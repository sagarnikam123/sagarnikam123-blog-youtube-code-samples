# Vector Installation Guide

Vector is a high-performance observability data pipeline.

## Installation Methods

### macOS

**Homebrew:**
```bash
brew install vector
```

**Binary Download:**
```bash
curl -sSL https://sh.vector.dev | bash
```

### Linux

**Ubuntu/Debian:**
```bash
curl -1sLf 'https://repositories.timber.io/public/vector/cfg/setup/bash.deb.sh' | sudo -E bash
sudo apt install vector
```

**RHEL/CentOS:**
```bash
curl -1sLf 'https://repositories.timber.io/public/vector/cfg/setup/bash.rpm.sh' | sudo -E bash
sudo yum install vector
```

**Binary Download:**
```bash
curl -sSL https://sh.vector.dev | bash
```

### Windows

**PowerShell:**
```powershell
iwr https://sh.vector.dev -useb | iex
```

### Docker

```bash
docker pull timberio/vector:latest
```

### Kubernetes

**Helm:**
```bash
helm repo add vector https://helm.vector.dev
helm install vector vector/vector
```

## Verification

```bash
vector --version
```

## Resources

- **Official Installation**: https://vector.dev/docs/setup/installation/
- **GitHub Releases**: https://github.com/vectordotdev/vector/releases
- **Documentation**: https://vector.dev/docs/
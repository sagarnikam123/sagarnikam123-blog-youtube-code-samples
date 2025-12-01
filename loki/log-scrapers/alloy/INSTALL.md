# Grafana Alloy Installation Guide

Grafana Alloy is an OpenTelemetry collector distribution.

## Installation Methods

### macOS

**Homebrew:**
```bash
brew install grafana/grafana/alloy
```

**Binary Download:**
```bash
curl -fsSL https://github.com/grafana/alloy/releases/latest/download/alloy-darwin-amd64.zip -o alloy.zip
unzip alloy.zip
chmod +x alloy-darwin-amd64
sudo mv alloy-darwin-amd64 /usr/local/bin/alloy
```

### Linux

**Ubuntu/Debian:**
```bash
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install alloy
```

**RHEL/CentOS:**
```bash
sudo wget -O /etc/yum.repos.d/grafana.repo https://rpm.grafana.com/grafana.repo
sudo yum install alloy
```

**Binary Download:**
```bash
curl -fsSL https://github.com/grafana/alloy/releases/latest/download/alloy-linux-amd64.zip -o alloy.zip
unzip alloy.zip
chmod +x alloy-linux-amd64
sudo mv alloy-linux-amd64 /usr/local/bin/alloy
```

### Windows

**Binary Download:**
```powershell
Invoke-WebRequest -Uri "https://github.com/grafana/alloy/releases/latest/download/alloy-windows-amd64.zip" -OutFile "alloy.zip"
Expand-Archive -Path "alloy.zip" -DestinationPath "."
```

### Docker

```bash
docker pull grafana/alloy:latest
```

### Kubernetes

**Helm:**
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install alloy grafana/alloy
```

## Verification

```bash
alloy --version
```

## Resources

- **Official Installation**: https://grafana.com/docs/alloy/latest/set-up/install/
- **GitHub Releases**: https://github.com/grafana/alloy/releases
- **Documentation**: https://grafana.com/docs/alloy/
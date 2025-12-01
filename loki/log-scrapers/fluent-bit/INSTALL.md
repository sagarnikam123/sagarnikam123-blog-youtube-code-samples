# Fluent Bit Installation Guide

Fluent Bit is a lightweight log processor and forwarder.

## Installation Methods

### macOS

**Homebrew:**
```bash
brew install fluent-bit
```

**Binary Download:**
```bash
curl -LO https://github.com/fluent/fluent-bit/releases/latest/download/fluent-bit-3.0.0-darwin-amd64.tar.gz
tar -xzf fluent-bit-3.0.0-darwin-amd64.tar.gz
sudo cp fluent-bit-3.0.0-darwin-amd64/bin/fluent-bit /usr/local/bin/
```

### Linux

**Ubuntu/Debian:**
```bash
curl https://raw.githubusercontent.com/fluent/fluent-bit/master/install.sh | sh
```

**Or via package manager:**
```bash
curl -fsSL https://packages.fluentbit.io/fluentbit.key | sudo gpg --dearmor -o /usr/share/keyrings/fluentbit-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/fluentbit-keyring.gpg] https://packages.fluentbit.io/ubuntu/jammy jammy main" | sudo tee /etc/apt/sources.list.d/fluent-bit.list
sudo apt-get update
sudo apt-get install fluent-bit
```

**RHEL/CentOS:**
```bash
curl -fsSL https://packages.fluentbit.io/fluentbit.key | sudo gpg --import -
sudo tee /etc/yum.repos.d/fluent-bit.repo << 'EOF'
[fluent-bit]
name = Fluent Bit
baseurl = https://packages.fluentbit.io/centos/8/
gpgcheck = 1
gpgkey = https://packages.fluentbit.io/fluentbit.key
enabled = 1
EOF
sudo yum install fluent-bit
```

**Binary Download:**
```bash
curl -LO https://github.com/fluent/fluent-bit/releases/latest/download/fluent-bit-3.0.0-linux-amd64.tar.gz
tar -xzf fluent-bit-3.0.0-linux-amd64.tar.gz
sudo cp fluent-bit-3.0.0-linux-amd64/bin/fluent-bit /usr/local/bin/
```

### Windows

**MSI Installer:**
```powershell
Invoke-WebRequest -Uri "https://github.com/fluent/fluent-bit/releases/latest/download/fluent-bit-3.0.0-win64.msi" -OutFile "fluent-bit.msi"
Start-Process msiexec.exe -Wait -ArgumentList '/I fluent-bit.msi /quiet'
```

**Binary Download:**
```powershell
Invoke-WebRequest -Uri "https://github.com/fluent/fluent-bit/releases/latest/download/fluent-bit-3.0.0-win64.zip" -OutFile "fluent-bit.zip"
Expand-Archive -Path "fluent-bit.zip" -DestinationPath "."
```

### Docker

```bash
docker pull fluent/fluent-bit:latest
```

### Kubernetes

**Helm:**
```bash
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluent-bit fluent/fluent-bit
```

**DaemonSet:**
```bash
kubectl apply -f https://raw.githubusercontent.com/fluent/fluent-bit-kubernetes-logging/master/fluent-bit-daemonset.yaml
```

## Verification

```bash
fluent-bit --version
```

## Resources

- **Official Installation**: https://docs.fluentbit.io/manual/installation/getting-started-with-fluent-bit
- **GitHub Releases**: https://github.com/fluent/fluent-bit/releases
- **Documentation**: https://docs.fluentbit.io/
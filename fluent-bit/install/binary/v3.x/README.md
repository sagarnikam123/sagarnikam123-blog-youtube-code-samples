# Fluent Bit - Binary Install - v3.x

## Version
- **Latest patch**: v3.0.4
- **Docs**: https://docs.fluentbit.io/manual/v/3.0

## Install

### Linux (Debian/Ubuntu)
```bash
curl https://raw.githubusercontent.com/fluent/fluent-bit/master/install.sh | sh
```

### Linux (RHEL/CentOS)
```bash
curl https://packages.fluentbit.io/fluentbit.key | sudo gpg --dearmor -o /usr/share/keyrings/fluentbit-keyring.gpg
```

### macOS (Homebrew)
```bash
brew install fluent-bit
```

## Upgrade

### macOS (Homebrew)
```bash
brew upgrade fluent-bit

# Verify version after upgrade
fluent-bit --version
```

### Linux (Debian/Ubuntu)
```bash
sudo apt-get update && sudo apt-get install --only-upgrade fluent-bit
```

### Linux (RHEL/CentOS)
```bash
sudo yum update fluent-bit
# or
sudo dnf upgrade fluent-bit
```

### Manual (re-download)
```bash
# Stop service first
sudo systemctl stop fluent-bit

# Download new version and replace binary
wget https://github.com/fluent/fluent-bit/releases/download/v3.0.4/fluent-bit-3.0.4-linux-<arch>.tar.gz
tar -xzf fluent-bit-3.0.4-linux-<arch>.tar.gz
sudo cp fluent-bit-3.0.4-linux-<arch>/bin/fluent-bit /usr/local/bin/fluent-bit

# Restart service
sudo systemctl start fluent-bit
fluent-bit --version
```

### Manual Download
```bash
# Replace <arch> with: x86_64 | aarch64
wget https://github.com/fluent/fluent-bit/releases/download/v3.0.4/fluent-bit-3.0.4-linux-<arch>.tar.gz
tar -xzf fluent-bit-3.0.4-linux-<arch>.tar.gz
cd fluent-bit-3.0.4-linux-<arch>/bin
./fluent-bit --version
```

## Run

```bash
fluent-bit -c /etc/fluent-bit/fluent-bit.conf
```

## Config Location
- Default: `/etc/fluent-bit/fluent-bit.conf`
- Logs: `/var/log/fluent-bit.log`

## Systemd Service
```bash
sudo systemctl enable fluent-bit
sudo systemctl start fluent-bit
sudo systemctl status fluent-bit
```

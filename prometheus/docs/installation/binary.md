# Binary Installation Guide

Install Prometheus directly from pre-compiled binaries on Linux, macOS, or Windows.

## Overview

Binary installation is ideal for:
- Bare-metal servers and VMs
- Environments without container support
- Full control over configuration and service management
- Air-gapped environments (with manual download)

## Prerequisites

### All Platforms
- Network access to download binaries (or pre-downloaded archive)
- Port 9090 available
- Sufficient disk space for data storage

### Linux
- systemd (most modern distributions)
- curl or wget
- tar
- Root/sudo access

### macOS
- macOS 10.15+ (Catalina or later)
- curl or wget
- tar

### Windows
- Windows 10/11 or Windows Server 2016+
- PowerShell 5.1+
- Administrator access

## Quick Start

### Linux

```bash
# Download and run installer
curl -fsSL https://raw.githubusercontent.com/your-repo/prometheus/main/install/binary/install-linux.sh -o install-linux.sh
chmod +x install-linux.sh
sudo ./install-linux.sh --version 2.54.1
```

### macOS

```bash
# Download and run installer
curl -fsSL https://raw.githubusercontent.com/your-repo/prometheus/main/install/binary/install-macos.sh -o install-macos.sh
chmod +x install-macos.sh
./install-macos.sh --version 2.54.1
```

### Windows (PowerShell as Administrator)

```powershell
# Download and run installer
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/prometheus/main/install/binary/install-windows.ps1" -OutFile "install-windows.ps1"
.\install-windows.ps1 -Version 2.54.1
```

## Installation Options

### Linux Installer Options

```bash
./install-linux.sh [OPTIONS]

Options:
    --version VERSION    Prometheus version (default: 2.54.1)
    --data-dir PATH      Data directory (default: /var/lib/prometheus)
    --config PATH        Custom prometheus.yml path
    --help, -h           Show help
```

**Examples:**

```bash
# Install specific version
sudo ./install-linux.sh --version 2.53.0

# Custom data directory
sudo ./install-linux.sh --data-dir /data/prometheus

# Use existing configuration
sudo ./install-linux.sh --config /path/to/prometheus.yml
```

### macOS Installer Options

```bash
./install-macos.sh [OPTIONS]

Options:
    --version VERSION    Prometheus version (default: 2.54.1)
    --data-dir PATH      Data directory (default: /usr/local/var/prometheus)
    --config PATH        Custom prometheus.yml path
    --system             Install as system-wide daemon (requires sudo)
    --help, -h           Show help
```

**Examples:**

```bash
# User-level installation (default, binds to 127.0.0.1)
./install-macos.sh --version 2.54.1

# System-wide installation (binds to 0.0.0.0)
sudo ./install-macos.sh --system --version 2.54.1
```

### Windows Installer Options

```powershell
.\install-windows.ps1 [OPTIONS]

Options:
    -Version VERSION     Prometheus version (default: 2.54.1)
    -DataDir PATH        Data directory (default: C:\ProgramData\prometheus)
    -Config PATH         Custom prometheus.yml path
    -InstallDir PATH     Installation directory (default: C:\Program Files\prometheus)
```

**Examples:**

```powershell
# Install specific version
.\install-windows.ps1 -Version 2.53.0

# Custom directories
.\install-windows.ps1 -DataDir D:\prometheus\data -InstallDir D:\prometheus
```

## Directory Structure

### Linux

| Path | Description |
|------|-------------|
| `/usr/local/bin/prometheus` | Prometheus binary |
| `/usr/local/bin/promtool` | Configuration validation tool |
| `/etc/prometheus/prometheus.yml` | Configuration file |
| `/etc/prometheus/consoles/` | Console templates |
| `/etc/prometheus/console_libraries/` | Console libraries |
| `/var/lib/prometheus/` | Data directory (TSDB) |
| `/etc/systemd/system/prometheus.service` | Systemd service unit |

### macOS

| Path | Description |
|------|-------------|
| `/usr/local/bin/prometheus` | Prometheus binary |
| `/usr/local/bin/promtool` | Configuration validation tool |
| `/usr/local/etc/prometheus/prometheus.yml` | Configuration file |
| `/usr/local/var/prometheus/` | Data directory |
| `/usr/local/var/log/prometheus/` | Log files |
| `~/Library/LaunchAgents/io.prometheus.prometheus.plist` | User launchd plist |
| `/Library/LaunchDaemons/io.prometheus.prometheus.plist` | System launchd plist (--system) |

### Windows

| Path | Description |
|------|-------------|
| `C:\Program Files\prometheus\prometheus.exe` | Prometheus binary |
| `C:\Program Files\prometheus\promtool.exe` | Configuration validation tool |
| `C:\Program Files\prometheus\prometheus.yml` | Configuration file |
| `C:\ProgramData\prometheus\` | Data directory |

## Service Management

### Linux (systemd)

```bash
# Check status
sudo systemctl status prometheus

# Start/Stop/Restart
sudo systemctl start prometheus
sudo systemctl stop prometheus
sudo systemctl restart prometheus

# Enable/Disable auto-start
sudo systemctl enable prometheus
sudo systemctl disable prometheus

# Reload configuration (without restart)
sudo systemctl reload prometheus

# View logs
sudo journalctl -u prometheus -f
sudo journalctl -u prometheus --since "1 hour ago"
```

### macOS (launchd)

```bash
# Check status
launchctl list | grep prometheus

# Start service
launchctl load ~/Library/LaunchAgents/io.prometheus.prometheus.plist

# Stop service
launchctl unload ~/Library/LaunchAgents/io.prometheus.prometheus.plist

# Restart service
launchctl unload ~/Library/LaunchAgents/io.prometheus.prometheus.plist
launchctl load ~/Library/LaunchAgents/io.prometheus.prometheus.plist

# View logs
tail -f /usr/local/var/log/prometheus/prometheus.log
tail -f /usr/local/var/log/prometheus/prometheus.error.log
```

### Windows (Services)

```powershell
# Check status
Get-Service prometheus

# Start/Stop/Restart
Start-Service prometheus
Stop-Service prometheus
Restart-Service prometheus

# Enable/Disable auto-start
Set-Service prometheus -StartupType Automatic
Set-Service prometheus -StartupType Disabled

# View logs (Event Viewer)
Get-EventLog -LogName Application -Source prometheus -Newest 50
```

## Configuration

### Default Configuration

The installer creates a default `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

rule_files:
  # - "first_rules.yml"

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

### Validate Configuration

Always validate before applying changes:

```bash
# Linux/macOS
promtool check config /etc/prometheus/prometheus.yml

# Windows
& "C:\Program Files\prometheus\promtool.exe" check config "C:\Program Files\prometheus\prometheus.yml"
```

### Apply Configuration Changes

```bash
# Linux - reload without restart
sudo systemctl reload prometheus

# Or send SIGHUP
kill -HUP $(pgrep prometheus)

# Or use lifecycle API (if enabled)
curl -X POST http://localhost:9090/-/reload
```

## Verification

### Check Installation

```bash
# Verify binary version
prometheus --version

# Check if service is running
# Linux
systemctl is-active prometheus

# macOS
pgrep -f "prometheus.*--config.file"

# Windows
(Get-Service prometheus).Status
```

### Test API Access

```bash
# Check API
curl http://localhost:9090/api/v1/status/config

# Check self-monitoring
curl 'http://localhost:9090/api/v1/query?query=up{job="prometheus"}'

# Expected: {"status":"success","data":{"resultType":"vector","result":[{"metric":{"job":"prometheus"},"value":[...,"1"]}]}}
```

### Access Web UI

Open http://localhost:9090 in your browser.

## Upgrade

### Linux

```bash
# Stop service
sudo systemctl stop prometheus

# Backup current installation
sudo cp /usr/local/bin/prometheus /usr/local/bin/prometheus.bak
sudo cp /etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml.bak

# Run installer with new version
sudo ./install-linux.sh --version 2.55.0

# Verify
prometheus --version
```

### macOS

```bash
# Stop service
launchctl unload ~/Library/LaunchAgents/io.prometheus.prometheus.plist

# Backup
cp /usr/local/bin/prometheus /usr/local/bin/prometheus.bak

# Run installer with new version
./install-macos.sh --version 2.55.0

# Start service
launchctl load ~/Library/LaunchAgents/io.prometheus.prometheus.plist
```

### Windows

```powershell
# Stop service
Stop-Service prometheus

# Backup
Copy-Item "C:\Program Files\prometheus\prometheus.exe" "C:\Program Files\prometheus\prometheus.exe.bak"

# Run installer with new version
.\install-windows.ps1 -Version 2.55.0

# Start service
Start-Service prometheus
```

## Uninstall

### Linux

```bash
# Stop and disable service
sudo systemctl stop prometheus
sudo systemctl disable prometheus

# Remove service file
sudo rm /etc/systemd/system/prometheus.service
sudo systemctl daemon-reload

# Remove binaries
sudo rm /usr/local/bin/prometheus
sudo rm /usr/local/bin/promtool

# Remove configuration (optional)
sudo rm -rf /etc/prometheus

# Remove data (optional - WARNING: deletes all metrics)
sudo rm -rf /var/lib/prometheus

# Remove user (optional)
sudo userdel prometheus
sudo groupdel prometheus
```

### macOS

```bash
# Stop service
launchctl unload ~/Library/LaunchAgents/io.prometheus.prometheus.plist

# Remove plist
rm ~/Library/LaunchAgents/io.prometheus.prometheus.plist

# Remove binaries
rm /usr/local/bin/prometheus
rm /usr/local/bin/promtool

# Remove configuration (optional)
rm -rf /usr/local/etc/prometheus

# Remove data (optional)
rm -rf /usr/local/var/prometheus
rm -rf /usr/local/var/log/prometheus
```

### Windows

```powershell
# Stop and remove service
Stop-Service prometheus
sc.exe delete prometheus

# Remove firewall rule
Remove-NetFirewallRule -DisplayName "Prometheus"

# Remove installation directory
Remove-Item -Recurse -Force "C:\Program Files\prometheus"

# Remove data directory (optional)
Remove-Item -Recurse -Force "C:\ProgramData\prometheus"
```

## Troubleshooting

### Service Won't Start

**Linux:**
```bash
# Check service status
sudo systemctl status prometheus

# Check logs
sudo journalctl -u prometheus -n 100 --no-pager

# Common issues:
# - Port 9090 already in use
# - Invalid configuration
# - Permission issues on data directory
```

**macOS:**
```bash
# Check logs
cat /usr/local/var/log/prometheus/prometheus.error.log

# Check if port is in use
lsof -i :9090
```

**Windows:**
```powershell
# Check Event Viewer
Get-EventLog -LogName Application -Source prometheus -Newest 20

# Check if port is in use
Get-NetTCPConnection -LocalPort 9090
```

### Configuration Errors

```bash
# Validate configuration
promtool check config /path/to/prometheus.yml

# Common errors:
# - YAML syntax errors (indentation)
# - Invalid scrape_interval format
# - Missing required fields
```

### Permission Denied

**Linux:**
```bash
# Fix data directory permissions
sudo chown -R prometheus:prometheus /var/lib/prometheus
sudo chmod 755 /var/lib/prometheus

# Fix config permissions
sudo chown prometheus:prometheus /etc/prometheus/prometheus.yml
sudo chmod 644 /etc/prometheus/prometheus.yml
```

### High Memory Usage

```bash
# Check active series count
curl -s 'http://localhost:9090/api/v1/query?query=prometheus_tsdb_head_series' | jq '.data.result[0].value[1]'

# Reduce retention if needed
# Edit prometheus.yml or service arguments:
# --storage.tsdb.retention.time=7d
```

### Port Already in Use

```bash
# Find process using port 9090
# Linux
sudo ss -tlnp | grep 9090
sudo lsof -i :9090

# macOS
lsof -i :9090

# Windows
Get-NetTCPConnection -LocalPort 9090 | Select-Object OwningProcess
Get-Process -Id <PID>
```

## Security Considerations

### Network Binding

By default:
- Linux: Binds to `0.0.0.0:9090` (all interfaces)
- macOS (user): Binds to `127.0.0.1:9090` (localhost only)
- macOS (system): Binds to `0.0.0.0:9090`
- Windows: Binds to `0.0.0.0:9090`

To restrict access, modify the `--web.listen-address` flag in the service configuration.

### Firewall

**Linux (firewalld):**
```bash
sudo firewall-cmd --add-port=9090/tcp --permanent
sudo firewall-cmd --reload
```

**Linux (ufw):**
```bash
sudo ufw allow 9090/tcp
```

**Windows:**
The installer automatically adds a firewall rule. To remove:
```powershell
Remove-NetFirewallRule -DisplayName "Prometheus"
```

### TLS/Authentication

For production, consider:
1. Enabling TLS with `--web.config.file`
2. Using a reverse proxy (nginx, traefik) for authentication
3. Network segmentation

See [Prometheus Security](https://prometheus.io/docs/prometheus/latest/configuration/https/) for details.

## Next Steps

1. [Configure scrape targets](../configuration/README.md)
2. [Set up alerting rules](../configuration/alerting.md)
3. [Run validation tests](../testing/README.md)

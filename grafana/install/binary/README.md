# Grafana — binary/package standalone

Grafana is available as standalone binaries and native packages for Linux, macOS, and Windows.

## Linux — tarball

```bash
VERSION=13.2.0
wget "https://dl.grafana.com/oss/release/grafana-${VERSION}.linux-amd64.tar.gz"
tar -zxvf "grafana-${VERSION}.linux-amd64.tar.gz"
cd "grafana-v${VERSION}"
./bin/grafana server
```

## Linux — APT (Debian/Ubuntu)

```bash
sudo apt install -y apt-transport-https software-properties-common wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install grafana
sudo systemctl enable --now grafana-server
```

## Linux — RPM (RHEL/CentOS/Fedora)

```bash
sudo cat <<'EOF' > /etc/yum.repos.d/grafana.repo
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

sudo dnf install grafana
sudo systemctl enable --now grafana-server
```

## macOS — Homebrew

```bash
brew install grafana
brew services start grafana
```

## Windows

Download the MSI or standalone binary from [grafana.com/grafana/download](https://grafana.com/grafana/download?platform=windows). Run `grafana-server.exe` from the `bin/` directory or install as a Windows service via NSSM.

## Access

Open <http://localhost:3000>. Default credentials: `admin` / `admin`.

Official sources:
- [Install Grafana](https://grafana.com/docs/grafana/latest/setup-grafana/installation/)
- [Downloads page](https://grafana.com/grafana/download)

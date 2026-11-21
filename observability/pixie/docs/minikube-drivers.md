# Minikube Drivers for Pixie

Pixie requires a VM-based minikube driver (not Docker/none). Supported drivers:
- **macOS (Apple Silicon)**: `qemu2` (hyperkit is x86-only and removed from Homebrew)
- **macOS (Intel)**: `qemu2` or `hyperkit` (if you have it already)
- **Linux**: `kvm2`

## Detect current driver

```bash
# Show the driver used by existing profile
minikube profile list

# Or check a specific profile
minikube config get driver
```

If no profile exists, minikube defaults to `docker` — which does NOT work with Pixie.

## Check if a driver is installed

```bash
# macOS — hyperkit
which hyperkit && echo "hyperkit available" || echo "hyperkit NOT found"

# macOS — check via brew
brew list --formula | grep hyperkit

# Linux — kvm2 (needs libvirt + QEMU)
which virsh && virsh list --all &>/dev/null && echo "kvm2 ready" || echo "kvm2 NOT ready"

# Linux — check KVM kernel module
lsmod | grep kvm
```

## Install missing driver

### macOS (Apple Silicon — M1/M2/M3/M4)

hyperkit is **x86-only and removed from Homebrew**. Use `qemu`:

```bash
brew install qemu
brew install socket_vmnet  # needed for network access from VMs

# Verify
qemu-system-aarch64 --version

# Start minikube with qemu2
minikube start --driver=qemu2 --cpus=4 --memory=8192 -p pixie-dev
```

If you need bridged networking (pods reachable from host):

```bash
# socket_vmnet is keg-only — requires one-time root setup
brew install socket_vmnet

# Start as a background service (runs at startup)
sudo brew services start socket_vmnet

# Or run manually (one-off, no persistence):
# /opt/homebrew/opt/socket_vmnet/bin/socket_vmnet --vmnet-gateway=192.168.105.1 /opt/homebrew/var/run/socket_vmnet

# Now start minikube with socket_vmnet networking
minikube start --driver=qemu2 --network=socket_vmnet --cpus=4 --memory=8192 -p pixie-dev
```

> **Note**: socket_vmnet is keg-only (not symlinked into /opt/homebrew/bin).
> If you need it in PATH: `echo 'export PATH="/opt/homebrew/opt/socket_vmnet/bin:$PATH"' >> ~/.zshrc`

### macOS (Intel — legacy)

If you already have hyperkit installed it still works, but it's no longer in Homebrew.
Prefer `qemu` (same steps as above) for a supported path.

### Linux: kvm2

```bash
# Debian/Ubuntu
sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils

# RHEL/CentOS/Fedora
sudo dnf install -y @virtualization

# Add user to libvirt group
sudo usermod -aG libvirt $(whoami)
newgrp libvirt

# Install the minikube KVM2 driver
minikube config set driver kvm2

# Verify
virsh list --all
```

## Set the driver and create cluster

```bash
# Set as default (persists across restarts)
minikube config set driver qemu2      # macOS (Apple Silicon)
minikube config set driver kvm2       # Linux

# Or specify per-start
minikube start --driver=qemu2 --cpus=4 --memory=8192 -p pixie-dev   # macOS
minikube start --driver=kvm2 --cpus=4 --memory=8192 -p pixie-dev    # Linux
```

## Troubleshooting

| Problem | Fix |
|:--------|:----|
| `hyperkit` not in Homebrew | It's x86-only and removed — use `qemu` on Apple Silicon |
| `qemu` network issues | Install `socket_vmnet`: `brew install socket_vmnet` |
| `kvm2` permission denied | Run `sudo usermod -aG libvirt $USER` then re-login |
| Apple Silicon Mac | Use `--driver=qemu2` (only supported VM driver) |
| minikube stuck on docker driver | Explicitly pass `--driver=qemu` or `--driver=kvm2` |
| `machine does not exist` on start | Delete stale profile: `minikube delete -p <name>` |

## Quick one-liner: detect + start

```bash
# Picks correct driver for your OS, fails fast if missing
OS=$(uname -s)
if [[ "$OS" == "Darwin" ]]; then
  DRIVER=qemu2
  command -v qemu-system-aarch64 &>/dev/null || command -v qemu-system-x86_64 &>/dev/null || { echo "Install qemu: brew install qemu"; exit 1; }
else
  DRIVER=kvm2
  command -v virsh &>/dev/null || { echo "Install kvm2 (see above)"; exit 1; }
fi
minikube start --driver="$DRIVER" --cpus=4 --memory=8192 -p pixie-dev
```

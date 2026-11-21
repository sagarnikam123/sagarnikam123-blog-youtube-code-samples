# Gatus — binary (build from source) standalone

Gatus does **not** publish prebuilt release binaries. Build it from source with Go, or install it directly with `go install`.

## Requirements

- **Go** 1.21+ (a recent toolchain; Gatus tracks current Go releases)
- **Git** (for the source build)

## Install with `go install`

```bash
go install github.com/TwiN/gatus@latest
# binary lands in $(go env GOPATH)/bin/gatus
```

## Or build from source

```bash
git clone https://github.com/TwiN/gatus.git
cd gatus
make build          # produces ./gatus
# or: go build -o gatus .
```

## Run

Gatus reads `config.yaml` from the current directory (or the path in `GATUS_CONFIG_PATH`):

```bash
export GATUS_CONFIG_PATH="$(git rev-parse --show-toplevel)/gatus/configs/config.yaml"
./gatus
```

Open <http://localhost:8080>.

## Run in the background (systemd sketch)

```ini
# /etc/systemd/system/gatus.service
[Unit]
Description=Gatus health dashboard
After=network-online.target

[Service]
Environment=GATUS_CONFIG_PATH=/etc/gatus/config.yaml
ExecStart=/usr/local/bin/gatus
Restart=on-failure
User=gatus

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now gatus
```

## Notes

- Default storage is in-memory. Add a `storage:` block (SQLite/PostgreSQL) for persistent history.
- Pin a tag with `go install github.com/TwiN/gatus@v5.37.0` for reproducibility.

Official source: [Gatus README — deployment](https://github.com/TwiN/gatus#deployment).

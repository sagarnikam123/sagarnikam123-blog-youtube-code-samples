# Vector — binary / package installation

## Install script (recommended for quick start)

```bash
curl --proto '=https' --tlsv1.2 -sSfL https://sh.vector.dev | bash
```

## APT (Debian/Ubuntu)

```bash
bash -c "$(curl -L https://setup.vector.dev)"
apt install vector
```

## RPM (RHEL/CentOS/Fedora)

```bash
bash -c "$(curl -L https://setup.vector.dev)"
yum install vector
```

## Homebrew (macOS)

```bash
brew install vector
```

## Run

```bash
vector --config /etc/vector/vector.yaml
```

## Validate config

```bash
vector validate --config vector.yaml
```

Official docs: [vector.dev/docs/setup/installation](https://vector.dev/docs/setup/installation/).

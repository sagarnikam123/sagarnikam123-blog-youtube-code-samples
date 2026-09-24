# OneUptime — Docker Compose standalone

OneUptime officially supports a single-server Docker Compose deployment. The repository's `scripts/setup.sh` downloads the upstream release bundle into this directory because the generated Compose project contains many services and changes independently of this guide.

See the [OneUptime installation guide](../../../README.md) for setup and health-check commands.

Official source: [Docker Compose installation](https://oneuptime.com/docs/installation/docker-compose).

```bash
# Clone this repo with just the release branch and cd into it.
git clone --depth 1 --single-branch --branch release https://github.com/OneUptime/oneuptime.git
cd oneuptime

# Copy config.example.env to config.env
cp config.example.env config.env

# IMPORTANT: Edit config.env file. Please make sure you have random secrets.

npm start
```

---

If you don't like to use npm or do not have it installed, run this instead:

```bash
# Read env vars from config.env file and run docker compose up.
(export $(grep -v '^#' config.env | xargs) && docker compose up --remove-orphans -d)

# Use sudo if you're having permission issues with binding ports.
sudo bash -c "(export $(grep -v '^#' config.env | xargs) && docker compose up --remove-orphans -d)"
```

# MySQL — Homebrew (macOS)

The simplest native install on macOS. Homebrew builds arm64/x64 bottles and manages the service via `brew services` (launchd). This is the macOS equivalent of the DEB/RPM package modes.

## Install

```bash
brew install mysql
```

> `mysql` tracks the latest MySQL Innovation release. For the LTS line use `brew install mysql@8.4`.

## Start

```bash
# As a background service (starts now + at login)
brew services start mysql

# Or run in the foreground (no auto-start)
/opt/homebrew/opt/mysql/bin/mysqld_safe --datadir=/opt/homebrew/var/mysql
```

Homebrew installs MySQL with **no root password**. Secure it:

```bash
mysql_secure_installation
```

## Connect

```bash
mysql -u root            # fresh install: no password
```

## Verify

```sql
SELECT VERSION();
```

## Manage

```bash
brew services list                 # show status
brew services restart mysql        # apply config changes
brew services stop mysql           # stop
```

## Notes

- Config: `/opt/homebrew/etc/my.cnf`
- Data: `/opt/homebrew/var/mysql/`
- Logs: `/opt/homebrew/var/mysql/*.err`
- Listens on `127.0.0.1:3306` by default.
- Apple Silicon uses the `/opt/homebrew` prefix; Intel Macs use `/usr/local`.

Official source: [Homebrew formula: mysql](https://formulae.brew.sh/formula/mysql).

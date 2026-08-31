# MySQL — DEB/APT (Debian/Ubuntu)

## Install

```bash
# Add the official MySQL APT repository
MYSQL_APT_VERSION="0.8.34-1"
curl -L -O "https://dev.mysql.com/get/mysql-apt-config_${MYSQL_APT_VERSION}_all.deb"
sudo DEBIAN_FRONTEND=noninteractive dpkg -i mysql-apt-config_${MYSQL_APT_VERSION}_all.deb

sudo apt-get update
sudo apt-get install -y mysql-server mysql-client
```

## Start

```bash
sudo systemctl enable --now mysql
sudo mysql_secure_installation      # set root password, remove test DB, etc.
mysql -u root -p
```

## Verify

```sql
SELECT VERSION();
```

## Notes

- Installs server + client.
- Config at `/etc/mysql/` (main file `/etc/mysql/my.cnf`).
- Data at `/var/lib/mysql/`.
- Logs at `/var/log/mysql/`.
- Ubuntu also ships MySQL in its default repos (`apt-get install mysql-server`) — the MySQL APT repo just tracks newer upstream versions.

Official guide: [APT repository quick guide](https://dev.mysql.com/doc/mysql-apt-repo-quick-guide/en/).

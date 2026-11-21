# MySQL — RPM (RHEL/CentOS/Fedora/Amazon Linux)

## Install

```bash
# Add the official MySQL Yum repository (EL9 example)
sudo dnf install -y "https://dev.mysql.com/get/mysql84-community-release-el9-1.noarch.rpm"
sudo dnf install -y mysql-community-server mysql-community-client
```

## Start

```bash
sudo systemctl enable --now mysqld

# A temporary root password is generated on first start — read it:
sudo grep 'temporary password' /var/log/mysqld.log

sudo mysql_secure_installation
mysql -u root -p
```

## Verify

```sql
SELECT VERSION();
```

## Notes

- Installs server + client.
- Config at `/etc/my.cnf`.
- Data at `/var/lib/mysql/`.
- Logs at `/var/log/mysqld.log`.
- For EL8 use `mysql84-community-release-el8-1.noarch.rpm`; for Fedora use the matching `fcNN` release RPM.
- Amazon Linux 2023: use the EL9 release RPM.

Official guide: [Yum repository quick guide](https://dev.mysql.com/doc/mysql-yum-repo-quick-guide/en/).

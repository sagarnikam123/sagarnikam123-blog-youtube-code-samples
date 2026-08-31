# MySQL — generic binary tarball

Self-contained tarball install. No package manager, no root repo — runs from the extracted directory. Useful when you can't add system packages.

## Install

```bash
# Prerequisite: libaio (Debian/Ubuntu: libaio1, RHEL: libaio)
MYSQL_VERSION="8.4.3"
curl -L -O "https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-${MYSQL_VERSION}-linux-glibc2.28-x86_64.tar.xz"
tar xf mysql-${MYSQL_VERSION}-linux-glibc2.28-x86_64.tar.xz
mv mysql-${MYSQL_VERSION}-linux-glibc2.28-x86_64 mysql
cd mysql
```

## Initialize & start

```bash
# Initialize the data directory (prints a temporary root password)
./bin/mysqld --initialize --basedir=$PWD --datadir=$PWD/data

# Start the server
./bin/mysqld --basedir=$PWD --datadir=$PWD/data --port=3306 &

# Connect (use the temp password printed above; you'll be forced to change it)
./bin/mysql -u root -p
```

## Verify

```sql
SELECT VERSION();
SELECT 1;
```

## Notes

- Grab the correct `linux-glibc2.28` (or `-minimal`) tarball for your CPU (`x86_64` / `aarch64`).
- No systemd — manage the process yourself or wrap it in a unit file.
- Data lives in `./data` by default. Use `--datadir` for a custom path.
- For production, prefer DEB/RPM packages with proper systemd management.

Official guide: [Generic binary installation](https://dev.mysql.com/doc/refman/8.4/en/binary-installation.html).

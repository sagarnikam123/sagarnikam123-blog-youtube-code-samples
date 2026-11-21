# MySQL — Docker standalone

## Run (single-node)

```bash
docker run -d --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=changeme \
  -e MYSQL_DATABASE=appdb \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=apppass \
  -v mysql-data:/var/lib/mysql \
  mysql:8.4
```

## Access

```bash
# Client inside the container
docker exec -it mysql mysql -u root -p

# From the host (needs a mysql client)
mysql -h 127.0.0.1 -P 3306 -u appuser -p appdb
```

## Ports

| Port | Purpose |
|:-----|:--------|
| 3306 | Client protocol (classic) |
| 33060 | X Protocol (MySQL Shell / document store) |

## Notes

- Pin the image tag (`8.4`, `8.0`) for reproducibility.
- Mount `/var/lib/mysql` for persistent data.
- `MYSQL_ROOT_PASSWORD` is required; `MYSQL_DATABASE`/`MYSQL_USER`/`MYSQL_PASSWORD` are optional bootstrap creds.
- Put custom config in `/etc/mysql/conf.d/*.cnf` via a mount.
- A single-service Compose equivalent is in [`docker-compose.yml`](docker-compose.yml).

Official guide: [MySQL Docker](https://dev.mysql.com/doc/refman/8.4/en/docker-mysql-getting-started.html).

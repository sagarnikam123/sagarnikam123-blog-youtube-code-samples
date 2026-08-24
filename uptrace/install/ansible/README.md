# Uptrace — Ansible deployment (bare-metal/VM)

Uptrace maintains official Ansible playbooks for deploying the full stack (Uptrace + ClickHouse + PostgreSQL + Redis + OTel Collector) on bare-metal servers or VMs.

## Prerequisites

- Ansible installed on the control machine
- SSH access with sudo to target servers
- Ubuntu 24.04 (recommended)
- Minimum per host: 2+ CPU, 4 GB RAM, 20 GB disk

## Install

```bash
git clone https://github.com/uptrace/ansible.git
cd ansible

cp inventory.sample.yml inventory.yml
# Edit inventory.yml with your server IPs

cp group_vars/all.sample.yml group_vars/all.yml
# Edit group_vars/all.yml with database passwords and settings

# Step 1: Bootstrap servers (installs common deps + OTel Collector)
ansible-playbook -i inventory.yml bootstrap.yml

# Step 2: Deploy ClickHouse
ansible-playbook -i inventory.yml ch_server.yml

# Step 3: Deploy PostgreSQL
ansible-playbook -i inventory.yml postgresql.yml

# Step 4: Deploy Redis
ansible-playbook -i inventory.yml redis.yml

# Step 5 (optional): Deploy Kafka for high-volume buffering
ansible-playbook -i inventory.yml kafka.yml

# Step 6: Deploy Uptrace
ansible-playbook -i inventory.yml uptrace.yml
```

## Inventory example (single-node)

```yaml
uptrace:
  hosts:
    10.10.1.1: { primary: true }
postgresql:
  hosts:
    10.10.1.1:
clickhouse_server:
  hosts:
    10.10.1.1: { ch_cluster: uptrace1, ch_shard: shard1, ch_replica: replica1 }
clickhouse_keeper:
  hosts:
    10.10.1.1: { keeper_id: 1 }
redis_cache:
  hosts:
    10.10.1.1: { redis_node_id: alpha, redis_maxmemory_mb: 128 }
```

## Notes

- Scale by splitting groups onto dedicated hosts.
- Use Ansible Vault to encrypt `group_vars/all.yml` for production.
- Kafka is optional — adds buffering for high-volume ingestion.
- For Kubernetes deployments, use the [Helm chart](../helm/) instead.

Official guide: [Deploying Uptrace with Ansible](https://uptrace.dev/get/hosted/ansible).

# Grafana Resource Management Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ansible Collection](https://img.shields.io/badge/collection-grafana.grafana-blue)](https://galaxy.ansible.com/ui/repo/published/grafana/grafana/)
[![Ansible](https://img.shields.io/badge/ansible-%3E%3D2.12.0-red)](https://docs.ansible.com/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.6-blue)](https://www.python.org/)

Complete Ansible automation for managing Grafana resources across multiple environments using the official [`grafana.grafana`](https://galaxy.ansible.com/ui/repo/published/grafana/grafana/) collection.

This automation framework provides production-ready playbooks with full CRUD operations for Grafana, Grafana Cloud, Azure Managed Grafana, and Amazon Managed Grafana.

## 📋 Requirements

### Version Compatibility

| Component | Minimum Version | Recommended | Tested With |
|-----------|----------------|-------------|-------------|
| **Ansible Core** | 2.12.0 | 2.15.0+ | 2.17.13     |
| **Python** | 3.6 | 3.8+ | 3.13.5      |
| **grafana.grafana Collection** | 5.0.0 | 6.0.4+ | 6.0.5       |
| **requests Library** | 2.20.0 | Latest | 2.32.5     |

### System Requirements
- **Operating System**: Linux, macOS, Windows (WSL)
- **Network**: HTTPS access to Grafana instances
- **Permissions**: Grafana Admin or Service Account with appropriate permissions

## 🚀 Getting Started

### Prerequisites Installation

```bash
# 1. Install Ansible and Python dependencies
pip3 install ansible>=2.12.0 requests

# 2. Verify Ansible installation
ansible --version

# 3. Install Grafana collection
ansible-galaxy collection install grafana.grafana

# 4. Verify collection installation
ansible-galaxy collection list | grep grafana
```

### Quick Setup (5 Minutes)

1. **Clone or Download Framework:**
   ```bash
   # Option 1: Clone entire repository
   git clone https://github.com/sagarnikam123/sagarnikam123-blog-youtube-code-samples.git
   cd sagarnikam123-blog-youtube-code-samples/grafana-automation/ansible

   # Option 2: Download just the ansible folder
   # Download from: https://github.com/sagarnikam123/sagarnikam123-blog-youtube-code-samples/tree/main/grafana-automation/ansible
   ```

2. **Configure Your Grafana Instance:**
   ```bash
   # Edit inventory with your Grafana URL
   nano inventory.ini

   # Update credentials (replace <placeholders>)
   nano host_vars/grafana-local.yml
   ```

3. **Test Connection:**
   ```bash
   # Verify connectivity and authentication
   ansible-playbook -i inventory.ini grafana_info.yml -e target_hosts=grafana_local
   ```

4. **Run Your First Automation:**
   ```bash
   # Create a test folder
   ansible-playbook -i inventory.ini operations/folder/folder_create.yml -e target_hosts=grafana_local

   # View created folder in Grafana UI
   ```



## 📁 Structure

```
ansible/
├── README.md                 # This file
├── inventory.ini             # Grafana instances inventory
├── grafana_info.yml          # System information playbook
├── host_vars/                # Host-specific variables
│   ├── grafana-local.yml     # Local development
│   ├── grafana-cloud.yml     # Grafana Cloud
│   ├── grafana-prod-*.yml    # Production instances
│   ├── grafana-staging-*.yml # Staging instances
│   └── grafana-dev-*.yml     # Development instances
├── group_vars/               # Environment-specific settings
└── operations/               # CRUD operations
    ├── folder/               # Folder management
    ├── datasource/           # Datasource management
    ├── dashboard/            # Dashboard management
    ├── user/                 # User management
    ├── alert_contact_point/  # Alert contact points
    ├── alert_notification_policy/  # Alert policies
    ├── cloud_api_key/        # Cloud API keys
    ├── cloud_plugin/         # Cloud plugins
    └── cloud_stack/          # Cloud stacks
```

## 🎯 Resource Status Overview

| Resource                | Create | Read | Update | Delete | CRUD Workflow | Status |
|-------------------------|:------:|:----:|:------:|:------:|:-------------:|:------:|
| Folder                  | ✅ | ✅ | ✅ | ✅ | ✅             | ✅ Working |
| Datasource              | ✅ | ✅ | ✅ | ✅ | ✅             | ✅ Working |
| Dashboard               | ✅ | ✅ | ✅ | ✅ | ✅             | ✅ Working |
| User                    | ✅ | ✅ | ✅ | ✅ | ✅             | ✅ Working |
| Alert Contact Point     | ✅ | ✅ | ✅ | ✅ | ✅             | ✅ Working |
| Alert Notification Policy | ✅ | ✅ | ✅ | ✅ | ✅             | ✅ Working |
| Cloud API Key           | ❌ | ✅ | ❌ | ❌ | ❌             | ❌ Not Functional |
| Cloud Plugin            | ❌ | ✅ | ❌ | ❌ | ❌             | 🔶 Read Only |
| Cloud Stack             | ❌ | ✅ | ❌ | ❌ | ❌             | 🔶 Limited by Tier |

**Status Legend:**
- ✅ **Working**: All CRUD operations function correctly
- 🔶 **Limited**: Some operations work, others restricted by permissions/tier
- ❌ **Not Functional**: Module has issues preventing normal operation

**Cloud Limitations:**
- **API Keys**: Endpoint not available in Grafana Cloud API
- **Plugins**: Module parameter issues and permission restrictions
- **Stacks**: Free tier allows only 1 stack, preventing create/update operations

## 📖 Usage Examples

### Basic Operations
```bash
# Get system information
ansible-playbook -i inventory.ini grafana_info.yml -e target_hosts=grafana_local

# Create folders
ansible-playbook -i inventory.ini operations/folder/folder_create.yml -e target_hosts=grafana_local

# Create data-sources
ansible-playbook -i inventory.ini operations/datasource/datasource_create.yml -e target_hosts=grafana_local

# Import dashboards
ansible-playbook -i inventory.ini operations/dashboard/dashboard_create.yml -e target_hosts=grafana_local
```

### Multi-Environment
```bash
# Deploy to production
ansible-playbook -i inventory.ini operations/folder/folder_create.yml -e target_hosts=grafana_prod

# Deploy to all environments
ansible-playbook -i inventory.ini operations/datasource/datasource_create.yml -e target_hosts=all_grafana
```

### With Vault (Production)
```bash
ansible-playbook -i inventory.ini grafana_info.yml --ask-vault-pass -e target_hosts=grafana_prod
```

## 🔧 Production Configuration

### Security (Production)

Encrypt sensitive files:
```bash
ansible-vault encrypt host_vars/grafana-prod-*.yml
ansible-vault encrypt host_vars/grafana-cloud.yml
```

## 🔐 Security Best Practices

1. **Never commit real credentials** - Use placeholders in version control
2. **Use Ansible Vault** for production environments
3. **Rotate API tokens** regularly
4. **Use least privilege** - Create service accounts with minimal required permissions
5. **Test in development** before applying to production

## ❓ FAQ & Troubleshooting

### General Questions

**Q: Can I use this with Grafana Cloud?**
A: Yes! Update the `grafana_url` in your host_vars to point to your Grafana Cloud instance and use a Cloud API token.

**Q: Do I need to install Grafana first?**
A: No, this framework manages existing Grafana instances. For Grafana installation, use the official collection's roles.

**Q: Can I manage multiple Grafana instances?**
A: Yes, define multiple hosts in `inventory.ini` and create corresponding `host_vars` files.

### Technical Questions

**Q: Why use `ansible_connection=local`?**
A: These playbooks make API calls to Grafana, not SSH connections to servers. The `local` connection runs on your control machine.

**Q: How do I handle SSL certificates?**
A: For self-signed certificates, add `grafana_validate_certs: false` to your host_vars. For production, use proper certificates.

**Q: Can I run this in CI/CD pipelines?**
A: Yes! Use service accounts, store credentials in CI secrets, and run with `--vault-password-file` for encrypted vars.

### Common Issues & Solutions

**Q: Getting "Module not found" errors?**
A: Run `ansible-galaxy collection install grafana.grafana` and verify with `ansible-galaxy collection list`.

**Q: Authentication Failed?**
A: Verify API token is valid and has correct permissions. Check Grafana URL is accessible.

**Q: Connection Issues?**
A: Ensure `ansible_connection=local` is set in inventory. Verify Grafana URLs are accessible from your machine.

## 📚 Related Resources

### Official Documentation
- [Grafana Ansible Collection Repository](https://github.com/grafana/grafana-ansible-collection) - Official Grafana Ansible Collection source code
- [Grafana Ansible Collection Documentation](https://docs.ansible.com/ansible/latest/collections/grafana/grafana/)
- [Grafana API Documentation](https://grafana.com/docs/grafana/latest/developers/http_api/)
- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/user_guide/vault.html)

### Community Resources
- [Grafana Community Forum](https://community.grafana.com/) - Get help from the Grafana community
- [Ansible Community](https://docs.ansible.com/ansible/latest/community/) - Ansible best practices and support
- [Blog Post: Complete Guide](https://sagarnikam123.github.io/posts/grafana-ansible-automation-complete-guide/) - Detailed tutorial with examples

## 🤝 Contributing

### To This Framework
1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Test your changes thoroughly
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Submit a pull request

### To the Official Collection
For issues or contributions to the underlying Grafana modules, please contribute to the [official Grafana Ansible Collection](https://github.com/grafana/grafana-ansible-collection).

## 📜 Code of Conduct

This project follows the [Ansible Community Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html).

## 📖 About This Framework vs Official Collection

This automation framework **complements** the official [`grafana.grafana`](https://github.com/grafana/grafana-ansible-collection) collection by focusing on different use cases:

### 🎯 This Framework (Resource Management)
**Purpose**: Manage existing Grafana resources via API
**Uses**: Collection **modules** for CRUD operations
**Target**: Already deployed Grafana instances

- ✅ **Grafana Resources**: Folder, datasource, dashboard, user, alert
- ✅ **Multi-environment**: Production-ready playbooks for dev/staging/prod
- ✅ **CRUD Operations**: Complete Create, Read, Update, Delete workflows
- ✅ **Security**: Ansible Vault integration and best practices
- ✅ **Managed Services**: Works with Grafana Cloud, Azure, AWS managed instances

### 🏗️ Official Collection (Software Installation)
**Purpose**: Install and deploy Grafana stack software
**Uses**: Collection **roles** for installation/configuration
**Target**: Fresh servers needing Grafana stack deployment

- ✅ **Software Installation**: Grafana, Grafana Agent, Alloy, Loki, Mimir, Promtail
- ✅ **System Configuration**: Service setup, configuration files, system dependencies
- ✅ **OpenTelemetry**: Deploy and configure OpenTelemetry Collector
- ✅ **Infrastructure**: Complete observability stack deployment

### 🔄 Typical Workflow
1. **Deploy Software** → Use official collection **roles** to install Grafana stack
2. **Manage Resources** → Use this framework's **modules** to configure and manage resources

### 💡 When to Use What
- **Need to install Grafana?** → Use official collection roles
- **Need to manage Grafana resources?** → Use this framework's playbooks
- **Both?** → Use them together for complete automation!

## 📄 License

**This Framework**: MIT License - see LICENSE file for details.

**Grafana Collection**: The underlying `grafana.grafana` collection is licensed under [GPL-3.0-or-later](https://github.com/grafana/grafana-ansible-collection/blob/main/LICENSE).

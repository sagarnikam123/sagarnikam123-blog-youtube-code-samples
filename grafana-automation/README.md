# Grafana Automation Suite

Complete automation solutions for managing Grafana resources across multiple environments using different tools and approaches.

## 🚀 Available Automation Methods

### 🤖 [Ansible](ansible/)
Production-ready Ansible automation framework with full CRUD operations for all Grafana resources.

**Features:**
- ✅ Complete CRUD operations for 9 Grafana modules
- ✅ Multi-environment support (dev/staging/prod)
- ✅ Production-ready security with Ansible Vault
- ✅ Works with Grafana Cloud, Azure, AWS managed instances

**Quick Start:**
```bash
cd ansible/
ansible-playbook -i inventory.ini grafana_info.yml -e target_hosts=grafana_local
```

### 🏗️ [Terraform](terraform/) *Coming Soon*
Infrastructure as Code approach for Grafana resource management.

### 🔌 [REST API](api/) *Coming Soon*
Direct API integration examples and utilities.

## 📚 Documentation & Guides

### 📖 [Guides](guides/)
- **[Provisioning](guides/provisioning/)** - Configuration management with provisioning
- **[Foundation SDK](guides/foundation-sdk/)** - Using Grafana Foundation SDK
- **[Grafanactl](guides/grafanactl/)** - Command-line tool usage

### 📋 [Documentation](docs/)
- **Advanced Grafana Guide** - Advanced configuration and optimization
- **Tools Comparison** - Comparison of different automation approaches
- **Observability as Code** - Best practices and patterns

## 🎯 Choose Your Approach

| Method | Best For | Complexity | Production Ready |
|--------|----------|------------|------------------|
| **Ansible** | Configuration Management, Multi-env | Medium | ✅ Yes |
| **Terraform** | Infrastructure as Code | Medium | 🔄 Coming Soon |
| **REST API** | Custom Integration, Scripts | Low | 🔄 Coming Soon |
| **Provisioning** | GitOps, Declarative Config | Low | ✅ Yes |

## 🤝 Contributing

1. Fork this repository
2. Create your feature branch
3. Test your changes thoroughly
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
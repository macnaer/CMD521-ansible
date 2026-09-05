# CMD521 Ansible

Ansible playbooks and infrastructure automation for AWS hosts.

## Project Structure

```
.
├── .agents/skills/           # Agent skills for Ansible and Git
├── inventory/
│   └── production/
│       ├── hosts             # Inventory file (INI)
│       └── group_vars/
│           ├── aws_hosts.yml
│           └── windows_hosts.yml
├── playbooks/
│   ├── install-packages.yml           # Install Linux packages (uses role)
│   ├── install-windows-packages.yml   # Install Windows packages (uses role)
│   ├── show-message.yml               # Show Windows message box
│   ├── shutdown-host.yml              # Shut down Windows host
│   └── roles/
│       ├── common/                    # Linux role
│       │   ├── defaults/main.yml
│       │   └── tasks/main.yml
│       └── windows-common/            # Windows role
│           ├── defaults/main.yml
│           └── tasks/main.yml
├── scripts/
│   └── setup-winrm.ps1       # Windows WinRM setup
└── README.md
```

## Inventory

| Host | IP | OS | User |
|------|----|----|------|
| amazon-linux | 13.60.184.149 | Amazon Linux | ec2-user |
| ubuntu | 16.171.193.140 | Ubuntu | ubuntu |
| windows | 10.20.42.122 | Windows | master |

## Playbooks

| Playbook | Description |
|----------|-------------|
| `install-packages.yml` | Install common Linux packages (mc, net-tools, curl, wget, git, vim, htop, unzip, tree, nano) |
| `install-windows-packages.yml` | Install common Windows packages (Chrome, WinRAR, Wireshark, Notepad++, Git) |
| `show-message.yml` | Show a Windows message box with custom text |
| `shutdown-host.yml` | Shut down a Windows host |

### Run Linux playbook
```bash
# Default (all aws_hosts):
ansible-playbook playbooks/install-packages.yml -i inventory/production/hosts

# Target specific host:
ansible-playbook playbooks/install-packages.yml -i inventory/production/hosts -e "target_hosts=ubuntu"
ansible-playbook playbooks/install-packages.yml -i inventory/production/hosts -e "target_hosts=amazon-linux"
```

### Run Windows playbook
```bash
# Default (all windows_hosts):
ansible-playbook playbooks/install-windows-packages.yml -i inventory/production/hosts --ask-vault-pass

# Target specific host:
ansible-playbook playbooks/install-windows-packages.yml -i inventory/production/hosts -e "target_hosts=windows" --ask-vault-pass
```

### Show message on Windows
```bash
# Default message:
ansible-playbook playbooks/show-message.yml -i inventory/production/hosts --ask-vault-pass

# Custom message:
ansible-playbook playbooks/show-message.yml -i inventory/production/hosts --ask-vault-pass -e "user_message=Hello World!"
```

### Shut down Windows host
```bash
ansible-playbook playbooks/shutdown-host.yml -i inventory/production/hosts --ask-vault-pass
```

## Quick Start

### Test connection
```bash
ansible aws_hosts -i inventory/production/hosts -m ping
```

### Run ad-hoc command
```bash
ansible aws_hosts -i inventory/production/hosts -m shell -a "uptime"
```

## SSH Key

Private key location: `/home/master/ansible/keys/Stockholm_3.pem`

## Windows WinRM Setup

On Windows machine (PowerShell as Administrator):

```powershell
.\scripts\setup-winrm.ps1
```

Test connection:

```bash
ansible windows_hosts -i inventory/production/hosts -m win_ping --ask-vault-pass
```

## Agent Skills

- **ansible** - Playbook development, roles, collections
- **git** - Version control operations

## License

MIT

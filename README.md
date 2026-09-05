# CMD521 Ansible

Ansible playbooks and infrastructure automation for AWS hosts.

## Project Structure

```
.
├── .agents/skills/           # Agent skills for Ansible and Git
├── inventory/
│   ├── production/
│   │   ├── hosts             # Static inventory file (INI)
│   │   └── group_vars/
│   │       ├── aws_hosts.yml
│   │       └── windows_hosts.yml
│   └── fastapi_inventory.yml # Dynamic inventory (plugin config)
├── plugins/
│   └── inventory/
│       └── fastapi_inventory.py  # Custom inventory plugin
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
├── api/
│   ├── main.py               # FastAPI app + routes
│   ├── database.py           # SQLite connection + schema
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic validation models
│   ├── auth.py               # Cookie-based authentication
│   ├── templates/            # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── hosts.html
│   │   ├── host_form.html
│   │   ├── groups.html
│   │   └── group_form.html
│   └── static/css/style.css  # Styling
├── scripts/
│   └── setup-winrm.ps1       # Windows WinRM setup
├── ansible.cfg                # Ansible configuration
├── requirements.txt           # Python dependencies
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

## Dynamic Inventory API + Web UI

FastAPI application with SQLite database and web interface for managing inventory.

### Setup

```bash
pip install -r requirements.txt
```

### Start API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Web UI

Open [http://localhost:8000/login](http://localhost:8000/login)

| Default | |
|---------|---------|
| Username | `admin` |
| Password | `admin` |

Features:
- **Dashboard** — overview of hosts and groups
- **Hosts** — add, edit, delete hosts with IP, SSH user, and password
- **Groups** — add, edit, delete groups with HTML form inputs

### Use with Ansible (Inventory Plugin)

The project uses a custom Ansible inventory plugin that fetches hosts from the API.

```bash
# Run playbook with dynamic inventory (default in ansible.cfg)
ansible-playbook playbooks/install-packages.yml

# Or explicitly specify inventory
ansible-playbook playbooks/install-packages.yml -i inventory/fastapi_inventory.yml

# Test inventory
ansible-inventory -i inventory/fastapi_inventory.yml --list
ansible-inventory -i inventory/fastapi_inventory.yml --graph
```

### API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/login` | No | Login page |
| `POST` | `/login` | No | Process login |
| `GET` | `/logout` | Yes | Clear session |
| `GET` | `/` | Yes | Dashboard |
| `GET` | `/hosts` | Yes | List hosts |
| `GET` | `/hosts/add` | Yes | Add host form |
| `POST` | `/hosts/add` | Yes | Create host |
| `GET` | `/hosts/{id}/edit` | Yes | Edit host form |
| `POST` | `/hosts/{id}/edit` | Yes | Update host |
| `POST` | `/hosts/{id}/delete` | Yes | Delete host |
| `GET` | `/groups` | Yes | List groups |
| `GET` | `/groups/add` | Yes | Add group form |
| `POST` | `/groups/add` | Yes | Create group |
| `GET` | `/groups/{id}/edit` | Yes | Edit group form |
| `POST` | `/groups/{id}/edit` | Yes | Update group |
| `POST` | `/groups/{id}/delete` | Yes | Delete group |
| `GET` | `/api/hosts` | No | Hosts list for inventory plugin |
| `GET` | `/api/groups` | No | Groups list for inventory plugin |

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

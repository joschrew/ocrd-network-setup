Files for deployment of [OCR-D](https://ocr-d.de/) processing-server
====================================================================


What is this?
-------------
### briefly
Start [OCR-D](https://ocr-d.de/) [Processing-Server](https://github.com/OCR-D/core/blob/master/ocrd/ocrd/cli/processing_server.py) together with the [OCR-D Webapi](https://github.com/OCR-D/ocrd-webapi-implementation) in a VM

### Summary of what is done to run the Processing-Server
- Processing-Server and Webapi run in docker on the VM
- Workers are started on the VM
- Workers are installed in a venv
- Traefik to route to either the Processing-Server or Webapi (for workflows/workspaces management)

### Details of deployment
1. create venv on VM with script ocrd-venv.sh. The needed processors are installed to this venv.
   venv is added to PATH with ~/.profile:
```
if [ -d '$HOME/venv-ocrd/bin' ]; then
  PATH=$HOME/venv-ocrd/bin:$PATH
fi
```

2. create ssh-key for Procesing-Server to ssh into the VM (its own host)
  - the pub-key is added to ~/.ssh/authorized keys and the private key will be volume-mounted to the
    Processing-Server Docker Container
3. clone Webapi-Repo
  - https://github.com/OCR-D/ocrd-webapi-implementation
  - Reason: Webapi-container will be build from this cloned repo
4. Create Volume folder for workspaces:
  - /tmp/ocrd-webapi-data
  - owner is normal user (uid 1000)
  - folder must be created before webapi-container startup, otherwise it will be owned by root
  - must be identically for what is used in the webapi: `OCRD_WEBAPI_BASE_DIR` and the volume mount
    of `/tmp/ocrd-webapi-data:/tmp/ocrd-webapi-data`. Otherwise workspace_id resolving will not work
5. upload processing-server config:
  - must be volume mounted to the processing-server
6. start docker-compose.yml in vm
  - currently username and password are commented in the docker-compose file. They must be set to
    make uploading possible

Ansible
-------
- I use the ansible-playbook to set up the VM
- the repos structure currently is based on my needs to work together with my other ansible stuff
  I use for other projects.

### Installation and setup for/of ansible
- I forgot how I installed ansible, but that should be simple
- Ansible needs to know how to login to the servers. There is a default way to provide
  this info (`hosts`-file in /etc/ansible). But I wanted to keep the hosts here so I use ansible.cfg
  to set where to look for the hosts
- So it is neccessary to copy ansible.cfg.example to ansible.cfg and set `inventory` to the folder
  of this repo.
    - info regarding ansible.cfg detection: https://docs.ansible.com/ansible/latest/reference_appendices/config.html
        - first it checks env-var, then current dir, then home then /etc/ansible/ansible.cfg
- Hosts file must be copied as well: `cp hosts.example hosts` and the path to the ssh-key must be
  set

### Usage:
- `ansible-playbook p_install_processing_server.yml`

### further Infos:
- In ansible there are roles and tasks. For this script I only use tasks because of interference
  with my other ansible playbooks/setup
- I have a ansible-script to to a basic cloud-server setup (I use that for all my vms): install some
  stuff like fzf and ripgrep, disable password login, vimrc, docker-mtu etc. But this is not
  included here, this playbook is only about what is specific for ocrd-webapi/processing-server

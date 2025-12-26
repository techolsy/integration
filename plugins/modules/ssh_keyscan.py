#!/usr/bin/python3

DOCUMENTATION = r'''
---
module: ssh_keyscan
short_description: Scan a Linux server for its SSH host keys
description:
  - Retrieves the public SSH host keys from a target host and returns them.
options:
  target_host:
    description:
      - Hostname or IP address of the target machine.
    required: true
    type: str
  target_port:
    description:
      - TCP port on which the SSH service is listening.
    required: true
    type: int
author:
  - Alexander Olsson (@techolsy)
'''

EXAMPLES = r'''
- name: Scan for server keys
  techolsy.integration.ssh_keyscan:
    target_host: pihole.local
    target_port: 22
'''

RETURN = r'''
keys:
  description: List of SSH public keys retrieved from the target.
  type: list
  elements: str
  sample: ["ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA..."]
'''

from ansible.module_utils.basic import AnsibleModule
import paramiko
import socket

def main():
    parameters = {
        'target_host': {"required": True, "type": 'str'},
        'target_port': {"required": True, "type": 'int'}
    }

    module = AnsibleModule(argument_spec=parameters)

    target_host = module.params['target_host']
    target_port = module.params['target_port']

    key_types = [
        'ssh-ed25519',
        'ecdsa-sha2-nistp256',
        'rsa-sha2-256',
        'rsa-sha2-512',
        'ssh-rsa' # Legacy, should throw a warning
    ]
    keys = {}

    for key_type in key_types:
        try:
            sock = socket.create_connection((target_host, target_port), timeout=5)
            transport = paramiko.Transport(sock)
            transport.get_security_options().key_types = [key_type]
            transport.start_client()
            key = transport.get_remote_server_key()
            transport.close()
            base64_key = key.get_base64()
            keys[key_type] = base64_key 
        except Exception as e:
            module.warn(f'{key_type} failed: {e}')
            continue

    output = {
        'target_host': target_host,
        'target_port': target_port,
        'keys': keys
    }

    module.exit_json(changed=False, **output)

if __name__ == '__main__':
    main()

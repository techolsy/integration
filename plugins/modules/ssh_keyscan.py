#!/usr/bin/python3

DOCUMENTATION = r'''
---
module: ssh_keyscan
short_description: Scan a Linux server for its SSH host keys
description:
  - Retrieves the public SSH host keys from a target host and returns them.
options:
  host:
    description:
      - Hostname or IP address of the target machine.
    required: true
    type: str
  port:
    description:
      - TCP port on which the SSH service is listening.
    required: false
    type: int
author:
  - Alexander Olsson (@techolsy)
'''

EXAMPLES = r'''
- name: Scan for server keys
  techolsy.integration.ssh_keyscan:
    host: pihole.local
    port: 22
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

def run_module():
    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=False, default=22)
    )

    result = dict(
        changed=False,
        host='',
        port='',
        keys=[]
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    target_host = module.params['host']
    target_port = module.params['port']

    key_types = [
        'ssh-ed25519',
        'ecdsa-sha2-nistp256',
        'rsa-sha2-256',
        'rsa-sha2-512',
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

    result['host'] = module.params['host']
    result['port'] = module.params['port']
    result['keys'] = keys

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

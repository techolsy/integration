from ansible.module_utils.basic import AnsibleModule
import paramiko
import socket

def main():
    parameters = {
        'target_host': {"requried": True, "type": 'str'},
        'target_port': {"required": True, "type": 'int'}
    }

    module = AnsibleModule(argument_spec=parameters)

    target_host = module.params['target_host']
    target_port = module.params['target_port']

    key_types = ['ssh-ed25519', 'ecdsa-sha2-nistp256', 'ssh-rsa']
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
        except:
            continue

    output = {
        'target_host': target_host,
        'target_port': target_port,
        'keys': keys
    }

    module.exit_json(changed=False, **output)

if __name__ == '__main__':
    main()

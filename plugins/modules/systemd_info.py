#!/usr/bin/python3

DOCUMENTATION = r'''
---
module: systemd_info
short_description: Gather systemd units
description:
  - Collectins units and some simple information about them
  - Return the units as ansible facts

version_added: "0.3.0"

author:
  - Alexander Olsson (@techolsy)

options: {}

notes:
  - I wrote this to gather systemd unit facts faster then builtin and community alternatives
'''

EXAMPLES = r'''
- name: Gather systemd units
  techolsy.exmod.systemd_units_facts:

- name: Check if ssh service exists
  debug:
    msg: "SSH service exists"
  when: "'ssh.service' in ansible_facts.units"

- name: Check if ssh service is active
  debug:
    msg: "SSH is running"
  when: ansible_facts.units["ssh.service"].active == "active"
'''

RETURN = r'''
ansible_facts:
  description: systemd units description
  returned: always
  type: dict
  contains:
    units:
      description: Dict of systemd units keyed by unit name
      type: dict
      returned: always
      sample:
        ssh.service:
          load: loaded
          active: active
          sub: running
          description: OpenBSD Secure Shell server
'''

from ansible.module_utils.basic import AnsibleModule

def get_units(module):
    systemctl = module.get_bin_path("systemctl", required=True)

    rc, out, err = module.run_command([
        systemctl,
        "list-units",
        "--all",
        "--no-legend",
        "--no-pager",
        "--plain"
    ])

    if rc != 0:
        module.fail_json(msg="Failed to list systemd units", stderr=err)

    units = {}

    for line in out.splitlines():
        parts = line.split(None, 4)

        if len(parts) < 5:
            continue

        name = parts[0]

        units[name] = {
            "load": parts[1],
            "active": parts[2],
            "sub": parts[3],
            "description": parts[4],
        }

    return units

def main():
    module = AnsibleModule(
        argument_spec={},
        supports_check_mode=True
    )

    units = get_units(module)

    module.exit_json(
        changed=False,
        ansible_facts={
            "units": units
        }
    )

if __name__ == "__main__":
    main()

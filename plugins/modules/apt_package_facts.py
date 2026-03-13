#!/usr/bin/python3

DOCUMENTATION = r'''
---
module: apt_package_facts
short_description: Collect facts about installed APT packages.
description:
  - Faster way to collect facts on installed apt packages.
  - Only works on debian based systems.

version_added: "0.4.0"

author:
  - Alexander Olsson (@techolsy)
'''

EXAMPLES = r'''
- name: Gather APT package facts
  techolsy.exmod.apt_package_facts:

- name: Show nginx package version
  debug:
    var: ansible_facts.apt_packages['nginx']

- name: Print all packages
  debug:
    var: ansible_facts.apt_packages
'''

RETURN = r'''
ansible_facts:
  description: Collected package facts
  returned: always
  type: dict
  sample:
    apt_packages:
      nginx:
        version: "1.24.0-2ubuntu7"
        arch: "amd64"
'''

from ansible.module_utils.basic import AnsibleModule

DPKG_STATUS_FILE = "/var/lib/dpkg/status"

def parse_dpkg_status():
    packages = {}
    current = {}

    with open(DPKG_STATUS_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip()

            if not line:
                if current.get("Status", "").startswith("install ok installed"):
                    name = current.get("Package")
                    if name:
                        packages[name] = {
                            "version": current.get("Version"),
                            "arch": current.get("Architecture")
                        }
                current = {}
                continue

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            current[key.rstrip()] = value.strip()

    return packages

def run_module():
    module = AnsibleModule(
        argument_spec={},
        supports_check_mode=True
    )

    try:
        packages = parse_dpkg_status()

        module.exit_json(
            changed=False,
            ansible_facts={
                "apt_packages": packages
            }
        )

    except Exception as e:
        module.fail_json(msg=str(e))

def main():
    run_module()

if __name__ == "__main__":
    main()

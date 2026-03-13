#!/usr/bin/python3

DOCUMENTATION = r'''
---
module: nftable_raw
short_description: Manage nftables in same manner as iptables_raw
description:
  - Manage nftable rules in a similar fashion as iptables_raw
  - The module has validation before applying the rules
  - This was basically built to manage nftables in a simple manner

version_added: "0.2.0"

author:
  - Alexander Olsson (@techolsy)

options:
  name:
    description:
      - Unique name of the ruleset
      - Is used as filename
    required: true
    type: str

  rule:
    description:
      - Raw nftables rules to apply
      - Content will be written to a file
    required: false
    type: str
    default: ""

  weight:
    description:
      - Ordering weight of the rule files
      - Lower number is applied earlier
      - Weight number are part of filename
    required: false
    type: int
    default: 50

  state:
    description:
      - If rule should be present of absent
      - If absent it will delete all rule files with name regardless of weight
    type: str
    choices:
      - present
      - absent
    default: present

  validate:
    description:
      - Validate the rules before applying
    type: bool
    default: true

notes:
  - flush ruleset is always applied when rules gets applied

requirements:
  - nftables
'''

EXAMPLES = r'''
- name: Create base firewall rules
  techolsy.exmod.nftables_raw:
    name: base
    weight: 10
    rules: |
      table inet filter {
        chain input {
          type filter hook input priority 0;
          policy drop;

          ct state established,related accept
          iif lo accept
        }
      }

- name: Allow SSH
  techolsy.exmod.nftables_raw:
    name: ssh
    weight: 20
    rules: |
      add rule inet filter input tcp dport 22 accept

- name: Remove old rules
  techolsy.exmod.nftables_raw:
    name: legacy_rules
    state: absent
'''

RETURN = r'''
path:
  description: Path of the rule snippet file.
  type: str
  returned: when state=present
  example: /etc/ansible/nftables.d/020-ssh.nft

changed:
  description: Whether the ruleset was modified.
  type: bool
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import os
import glob
import tempfile

BASE_DIR="/etc/ansible/nftables.d"
MAIN_CONF="/etc/nftables.conf"

def ensure_dir():
    os.makedirs(BASE_DIR, exist_ok=True)

def snippet_path(weight, name):
    weight = int(weight)
    return os.path.join(BASE_DIR, f"{weight:03d}-{name}.nft")

def find_existing(name):
    pattern = os.path.join(BASE_DIR, f"*-{name}.nft")
    matches = glob.glob(pattern)
    return matches[0] if matches else None

def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read()

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def remove_file(path):
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def list_snippets():
    files = glob.glob(os.path.join(BASE_DIR, "*.nft"))
    return sorted(files)

def assemble_rules():
    tmp = tempfile.NamedTemporaryFile(delete=False)

    tmp.write(b"flush ruleset\n\n")

    for file in list_snippets():
        with open(file) as f:
            tmp.write(f.read().encode())
            tmp.write(b"\n")

    tmp.close()
    return tmp.name

def validate_rules(module, nft, tmpfile):
    rc, out, err = module.run_command([nft, "-c", "-f", tmpfile])

    if rc != 0:
        return False, err or out

    return True, None

def apply_rules(module, nft, tmpfile):
    rc, out, err = module.run_command([nft, "-f", tmpfile])

    if rc != 0:
        module.fail_json(
            msg="Failed applying nftables rules",
            stdout=out,
            stderr=err,
            rc=rc
        )

def detect_change(path, new_content):
    current = read_file(path)
    return current != new_content

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        rules=dict(type='str', required=False, default=""),
        weight=dict(type='int', default=50),
        state=dict(type='str', default='present', choices=['present','absent']),
        validate=dict(type='bool', default=True)
    )

    result = dict(
        changed=False,
        path=None,
        diff={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    nft = module.get_bin_path("nft", required=True)

    name = module.params['name']
    rules = module.params['rules']
    weight = module.params['weight']
    state = module.params['state']
    validate = module.params['validate']

    ensure_dir()

    desired_path = snippet_path(weight, name)
    existing = find_existing(name)

    try:

        if state == "present":

            if existing and existing != desired_path:
                if not module.check_mode:
                    os.remove(existing)
                result['changed'] = True

            current = read_file(desired_path)

            if detect_change(desired_path, rules):

                if module._diff:
                    result['diff'] = {
                        "before": current or "",
                        "after": rules
                    }

                if not module.check_mode:
                    write_file(desired_path, rules)
                result['changed'] = True

            result['path'] = desired_path

        elif state == "absent":

            if existing:
                current = read_file(desired_path)

                if module._diff:
                    result['diff'] = {
                        "before": current or "",
                        "after": ""
                    }

                if not module.check_mode:
                    remove_file(existing)
                result['changed'] = True

        if result['changed'] and not module.check_mode:

            tmpfile = assemble_rules()

            if validate:
                ok, err = validate_rules(module, nft, tmpfile)

                if not ok:
                    os.unlink(tmpfile)
                    module.fail_json(
                        msg="nftables validation failed",
                        error=err
                    )

            apply_rules(module, nft, tmpfile)
            os.unlink(tmpfile)

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    run_module()

if __name__ == '__main__':
    main()

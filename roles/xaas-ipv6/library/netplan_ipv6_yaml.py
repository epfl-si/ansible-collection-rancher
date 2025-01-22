import os
import re

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
---
module: netplan_ipv6_yaml

short_description: Set up IPv6 in a Netplan YAML file.

options:
    path:
        description: The path of the YAML file to add IPv6 configuration to.
        required: true
        type: str
    ipv6_address:
        description:
            - The IPv6 address to set up.
        required: true
        type: str
    ipv6_netmask:
        description:
            - The IPv6 netmask to set up.
        required: true
        type: str
    ipv6_gateway:
        description:
            - The IPv6 gateway to set up for the default route.
        required: false
        type: str
'''

def run ():
    module_args = dict(
        path=dict(type='str', required=True),
        ipv6_address=dict(type='str', required=True),
        ipv6_netmask=dict(type='str', required=True),
        ipv6_gateway=dict(type='str', required=False))

    module = AnsibleModule(argument_spec=module_args,
                           supports_check_mode=True)

    result = dict(changed=False)

    config_path = module.params['path']
    with open(config_path) as f:
        netplan_conf = f.read()

    netplan_conf_rewritten = add_ipv6_address(
        netplan_conf, module.params['ipv6_address'], module.params['ipv6_netmask'])
    netplan_conf_rewritten = add_ipv6_gateway(
        netplan_conf_rewritten, module.params.get('ipv6_gateway'))

    if netplan_conf_rewritten != netplan_conf:
        result['changed'] = True
        if module._diff:
            result['diff'] = dict(
                before=netplan_conf,
                after=netplan_conf_rewritten)

        if not module.check_mode:
            config_path_rewritten = f'{config_path}.ANSIBLENEW-{os.getpid()}'
            with open(config_path_rewritten, 'w') as f:
                f.write(netplan_conf_rewritten)
            os.replace(config_path_rewritten, config_path)

    module.exit_json(**result)

def unable (why=None):
    fail = "Unable to parse Netplan YAML configuration"
    if why is not None:
        fail = f'{fail}: {why}'
    raise ValueError(fail)

def add_ipv6_address (netplan_conf_yaml, ipv6_address, ipv6_netmask):
    if ipv6_address in netplan_conf_yaml:
        return netplan_conf_yaml

    lines = netplan_conf_yaml.splitlines()

    for i in range(0, len(lines) - 1):
        this_line = lines[i]
        next_line = lines[i + 1]

        if "nameservers:" in next_line:
            dash = re.match('(.*- )', this_line)
            if not dash:
                unable(f"add_ipv6_address: cannot parse line {i} as a list item")

            lines[i+1:i+1] = [dash[1] + f'{ipv6_address}/{ipv6_netmask}']

            return ''.join(f"{line}\n" for line in lines)

    unable("add_ipv6_address: `nameservers:` not found")

def add_ipv6_gateway (netplan_conf_yaml, ipv6_gateway):
    if ipv6_gateway in netplan_conf_yaml:
        return netplan_conf_yaml

    lines = netplan_conf_yaml.splitlines()

    for i in range(0, len(lines) - 1):
        this_line = lines[i]
        next_line = lines[i + 1]

        if "routes:" in this_line:
            indent = re.match('(.* )-', next_line)
            if not indent:
                unable(f"add_ipv6_gateway: cannot parse line {i + 1} as a list item")

            spaces = indent[1]
            lines[i+1:i+1] = [spaces + l
                              for l in (
                                      f'- to: "::/0"',
                                      f'  via: "{ipv6_gateway}"',
                                      f'  on-link: true')]

            return ''.join(f"{line}\n" for line in lines)

    unable("add_ipv6_gateway: `routes:` not found")


if __name__ == '__main__':
    run()

# `epfl_si.rancher.rke2_node` Ansible role

Manage the lifecycle of a Rancher RKE2 cluster member node, from insertion to uninstall.

Even though the module is currently tested on Ubuntu Noble only, it
strives for portability between Linux distributions. (RKE2 on Windows® is not supported.)

The following snippet in your playbook will insert all nodes into an existing Rancher cluster:

```yaml
- hosts: all_nodes
  gather_facts: yes   # epfl_si.rancher.rke2_node wants facts
  roles:
    - role: gitlab-node
    - role: xaas-ipv6
    - role: epfl_si.rancher.rke2_node
      vars:
        rancher_rke2_insecure: false
        rancher_rke2_is_worker: >-
           {{ inventory_hostname in ["worker1", "worker2"] }}
        rancher_rke2_is_controlplane: >-
           {{ inventory_hostname in ["master1", "master2", "master3"] }}
```

The following task will remove nodes if you specify so explicitly (e.g. with `ansible-playbook -t rke2-node.uninstall -l master2`):

```yaml
- name: Uninstall Rancher
  tags:
    - never
    - rke2-node.uninstall
  include_role:
    name: epfl_si.rancher.rke2_node
    tasks_from: uninstall
    apply:
      tags:
        - rke2-node.uninstall
```

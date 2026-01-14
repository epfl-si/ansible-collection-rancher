# This file is here for ansible-doc purposes **only**. The actual
# implementation is in ../action/namespace.py as an action plugin
# (i.e. it runs on the Ansible controller.)

# This file is here for ansible-doc purposes **only**. The actual
# implementation is in ../action/rancher_helm_chart.py as an action plugin
# (i.e. it runs on the Ansible controller.)

DOCUMENTATION = r'''
---
module: namespace
short_description: Manage a namespace in a Rancher downstream cluster
description:
- This module is implemented as an B(action plugin), meaning that it
  runs on the Ansible controller (*not* over any remote shell,
  regardless of `ansible_connection` etc. settings)

- This action plugin creates or deletes namespaces, and manages its
  Rancher-specific annotations and relationships, namely: whether the
  namespace appears as a B(system namespace) in the Rancher manager UI;
  and whether it is part of a B(project), which interacts with access
  control and resource quotas.

options:
  state:
    type: str
    default: V(present)
    description: The desired postcondition, either V(present) or V(absent).
      Note that deleting a project (with V(absent)) wont't delete
      the namespaces and resources that formerly belonged to the project.
  name:
    required: true
    type: str
    description: >
      The name of the Kubernetes C(Namespace) object.
  is_system:
    required: false
    type: bool
    default: false
    description: Whether the namespace should be identified as a system namespace
      in the Rancher UI

version_added: 0.10.0
'''

EXAMPLES = r'''

- name: "`namespace/my-namespace`"
  epfl_si.rancher.namespace:
    name: "my-namespace"
    is_system: false
'''

# This file is here for ansible-doc purposes **only**. The actual
# implementation is in ../action/rancher_helm_chart.py as an action plugin
# (i.e. it runs on the Ansible controller.)

DOCUMENTATION = r'''
---
module: rancher_helm_chart
short_description: Install a Helm package through the Rancher manager
description:
- This module is implemented entirely as an B(action plugin), that
  runs on the Ansible controller.

- This action plugin exercises Rancher's Helm-as-a-service feature
  like a human operator would, when clicking their way through Charts
  > Installed Apps in the rancher UI.

options:
  state:
    type: str
    default: V(present)
    description: The desired postcondition, either V(present) or V(absent)
  repository:
    required: true
    type: str
    description: >
      The name of the repository, which must match the Kubernetes name of a
      C(kind: ClusterRepo) object defined in the Rancher manager cluster
  chart:
    required: true
    type: str
    description: The name of the chart to install.
  release:
    required: false
    type: str
    default: same as C(chart)
    description: The release of the chart to install.
  namespace:
    required: true
    type: complex
    description: The namespace to install the chart into (same as the C(--namespace) flag
                 on the C(helm install) command line). Can either be specified as a string
                 (same as setting O(namespace.name), or as a dict with the fields below.
    suboptions:
      name:
        type: string
        required: true
        description: The name of the namespace
      owned:
        type: bool
        default: false
        description: Set to true to have Ansible create the namespace on install,
                     and delete it on uninstall.
      system:
        type: bool
        default: false
        description: Set to true to create the namespace
                     in the "System" C(Project.management.cattle.io),
                     which makes it appear as a system namespace in the
                     Rancher UI. Has no effect if O(namespace.owned) is false.

  version:
    required: true
    type: str
    description: The version of the Helm chart to install.
  values:
    required: true
    type: dict
    description: The dict of values passed as Helm's C(values.yaml) file
  timeout:
    type: str
    default: 600s
    description: How long to wait for the Rancher manager RPC to complete

version_added: 0.7.0

'''

EXAMPLES = r'''

- name: "nfs-subdir-external-provisioner Helm chart"
  epfl_si.rancher.rancher_helm_chart:
    repository: nfs-subdir-external-provisioner
    chart: nfs-subdir-external-provisioner
    namespace: "my-namespace"
    version: 4.0.18
    values:
      nfs:
        server: mynas.example.com
        path: /myshare/some/sub/path
      storageClass:
        defaultClass: true
'''

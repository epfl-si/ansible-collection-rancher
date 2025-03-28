from functools import cached_property
import json

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import AnsibleK8SModule
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherAPIClient

DOCUMENTATION = r'''
---
module: rancher_k8s_api_call
short_description: Make extended (Rancher-specific) API calls using Kubernetes bearer tokens
description:

- This is an I(Ansible module), i.e. some mobile Python code that
  Ansible executes on the remote host.

- This module lets your configuration-as-code exert the same API calls
  that your browser does; thereby allowing you to automate some
  operations typically done through the Rancher UI.

- 💡 Some of these UI actions are implemented as higher-level Ansible
  modules or action plugins, for instance C(rancher_helm_chart).
  Consider using them instead, if applicable.

- This module expects the C(K8S_AUTH_KUBECONFIG) environment variable
  to be set, and to point to a suitable Kubeconfig file (e.g. one
  downloaded from the Rancher UI). This module will authenticate to
  Rancher using the credentials found within.

- B(⚠ This module always returns a “changed“) (i.e. yellow) B(Ansible
  result.) It is up to you to short-circuit it (using a C(when:)
  clause) if its post-condition is already met.

options:
  method:
    description:
      - The HTTP method to use.
    type: str
    required: true

  uri:
    description:
      - The relative URI below the target cluster's entry point;
        typically starts with C(/v1/)
    type: str
    required: true

  body:
    description:
      - The HTTP request body, as a data structure I(before)
        serialization to JSON (done by the module)
    type: complex

version_added: 0.2.1
'''

EXAMPLES = r'''

- name: Install `some-helm-chart`
  epfl_si.rancher.rancher_k8s_api_call:
    method: POST
    uri: /v1/catalog.cattle.io.clusterrepos/some-helm-repo?action=install
    body:
      namespace: some-namespace
      charts:
        - annotations:
            catalog.cattle.io/ui-source-repo-type: cluster
            catalog.cattle.io/ui-source-repo: some-helm-repo
          chartName: nfs-subdir-external-provisioner
          releaseName: nfs-subdir-external-provisioner
          version: 1.2.3
          resetValues: false
          values:
            foo: bar
            baz: quux
      wait: true
      timeout: 600s

'''

class RancherAPICall:
    """Implementation for `rancher_k8s_api_call` Ansible tasks."""
    module_args = dict(
        method=dict(type='str'),
        uri=dict(type='str'),
        body=dict(type='dict'))

    @cached_property
    def client (self):
        return RancherAPIClient(module=self.module)

    @cached_property
    def module (self):
        return AnsibleK8SModule(
            argument_spec=self.module_args)

    def run (self):
        # https://stackoverflow.com/a/63747147
        data = self.client.call_k8s_api(
            self.module.params['method'],
            self.module.params['uri'],
            body=self.module.params['body'])

        self.module.exit_json(
            changed=True,
            api_response=data)


if __name__ == '__main__':
    RancherAPICall().run()

from functools import cached_property
import json

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import AnsibleK8SModule
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherAPIClient

DOCUMENTATION = r"""
---
module: rancher_api_call
short_description: Exert a (non-REST) Kubernetes API call against Rancher.
"""

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

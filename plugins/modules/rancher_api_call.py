from functools import cached_property
import json

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import AnsibleK8SModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client

DOCUMENTATION = r"""
---
module: rancher_api_call
short_description: Exert a (non-Kubernetes) API call against Rancher.
"""

class RancherAPICall:
    """Implementation for `rancher_api_call` Ansible tasks."""
    module_args = dict(
        method=dict(type='str'),
        uri=dict(type='str'),
        body=dict(type='dict'))

    @cached_property
    def k8s_client (self):
        client = get_api_client(self.module)
        return client.client

    @cached_property
    def module (self):
        return AnsibleK8SModule(
            argument_spec=self.module_args)

    def run (self):
        # https://stackoverflow.com/a/63747147
        (data, status, headers) = self.k8s_client.client.call_api(
            self.module.params['uri'],
            self.module.params['method'],
            auth_settings = ['BearerToken'],
            response_type="object",
            body=self.module.params['body'])

        self.module.exit_json(
            changed=True,
            api_response=data)


if __name__ == '__main__':
    RancherAPICall().run()

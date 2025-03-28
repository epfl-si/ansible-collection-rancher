from functools import cached_property
import json

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import AnsibleK8SModule


import kubernetes   # Because Ansible code has this bizarre `except ImportError` clause on it, which we really don't want to investigate (again)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client

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

  kubeconfig:
    type: complex
    required: false
    description:
      - The deserialized `kubeconfig` YAML file to authenticate with.
      - If not set, use the (remote) file pointed to by the
        C(K8S_AUTH_KUBECONFIG) environment variable.

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
        body=dict(type='dict'),
        kubeconfig=dict(type='dict'))

    @cached_property
    def client (self):
        if self.module.params.get("kubeconfig") is not None:
            return Steve(kubeconfig=self.module.params["kubeconfig"])
        else:
            return Steve(module=self.module)

    @cached_property
    def module (self):
        return AnsibleK8SModule(
            argument_spec=self.module_args)

    def run (self):
        # https://stackoverflow.com/a/63747147
        data = self.client.call(
            self.module.params['method'],
            self.module.params['uri'],
            body=self.module.params['body'])

        self.module.exit_json(
            changed=True,
            api_response=data)


class Steve:
    """Access the “Steve” (Kubernetes-style) API of a managed cluster."""
    def __init__ (self,
                  module=None,
                  kubeconfig=None,
                  api_key=None, base_url=None, rancher_api_cluster_id=None, ca_cert=None, validate_certs=True):
        if module is not None:
            # Ansible-style API: pass in an AnsibleModule instance
            client = get_api_client(module=module)
        elif kubeconfig is not None:
            client = get_api_client(kubeconfig=kubeconfig)
        elif (api_key is not None) and (base_url is not None) and (rancher_api_cluster_id is not None):
            # The `kubernetes` Python client insists to test its
            # connection against (you guessed it) a
            # Kubernetes-compatible API endpoint:
            server_uri = '%s/k8s/clusters/%s' % (base_url, rancher_api_cluster_id)
            client = get_api_client(api_key=api_key, host=server_uri,
                                    ca_cert=ca_cert, validate_certs=validate_certs)
        else:
            raise ValueError("Unable to create API client from constructor arguments")

        self.client = client

    @property
    def k8s_client (self):
        return self.client.client.client  # Ansible was there 🤷

    def call (self, method, uri, body=None):
        (data, status, headers) = self.k8s_client.call_api(
            uri, method,   # Google was there 🤷
            auth_settings=['BearerToken'],
            response_type="object",
            body=body)

        if status not in (200, 201):
            raise RancherAPIError(data)

        return data


class RancherAPIError (Exception):
    pass


if __name__ == '__main__':
    RancherAPICall().run()

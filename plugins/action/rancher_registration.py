from functools import cached_property

from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherAPIClient

_not_set = object()


DOCUMENTATION = r"""
---
module: rancher_registration
short_description: Create and download Rancher registration tokens and structures.
description:
  - This task lets your Ansible playbook register nodes into an existing Rancher cluster. It ensures that at least one `clusterregistrationtokens.management.cattle.io` object exists for your cluster, and returns the list of them as the `registrations` property of the task's return value.
"""

RETURN = r"""
registrations:
    description: The list of `clusterregistrationtokens.management.cattle.io` objects stored in the management Rancher. The Rancher UI apparently uses the first entry in this list for its “Cluster Management” → “Registration” tab.
    type: list
    returned: always
changed:
    description: Whether the task had to ask the Rancher back-end to create more `clusterregistrationtokens.management.cattle.io` objects (as the UI does if the GET API call returns an empty list).
"""

class RancherRegistrationAction (ActionBase):
    """Obtain the data structure that feeds the “Cluster Management” → “Registration” tab in the Rancher UI.
    """
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        self.ansible_api = ansible_api

        rancher = RancherAPIClient(kubeconfig=self.kubeconfig_path)
        existing = rancher.get_cluster_registrations()
        if existing:
            return {
                "changed": False,
                # Apparently the UI always picks the first entry in the
                # list (even if you deleted a few):
                "registrations": existing[0]
            }
        else:
            # This is also what the UI does if you delete everything.
            rancher.renew_cluster_registrations()
            return {
                "changed": True,
                "registrations": rancher.get_cluster_registrations()[0]
            }

    # TODO: these methods are shared with RancherLoginAction;
    # refactor into a trait or superclass.
    @cached_property
    def kubeconfig_path (self):
        return self._expand_var('ansible_rancher_credentials_file')

    def _expand_var (self, var_name, default=_not_set):
        if default is not _not_set and not self.ansible_api.has_var(var_name):
            return default
        else:
            return self.ansible_api.expand_var('{{ %s }}' % var_name)


ActionModule = RancherRegistrationAction

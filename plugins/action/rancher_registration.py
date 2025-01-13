from functools import cached_property

from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherManagerAPIClient
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin

_not_set = object()


DOCUMENTATION = r"""
---
module: rancher_registration
short_description: Create and download Rancher registration tokens and structures.
description:
  - This task lets your Ansible playbook register nodes into an existing Rancher cluster. It ensures that at least one `clusterregistrationtokens.management.cattle.io` object exists for your cluster, and returns the list of them as the `registrations` property of the task's return value.
  - This task authenticates against the master Rancher back-end (for the case where the cluster doesn't already exist). It transparently fetches (or creates) a token by connecting into the Rancher master over ssh.
"""

RETURN = r"""
registration:
    description: The first entry in the list of `clusterregistrationtokens.management.cattle.io` objects stored in the management Rancher. The Rancher UI apparently uses this one for its “Cluster Management” → “Registration” tab.
    type: list
    returned: always
changed:
    description: Whether the task had to ask the Rancher back-end to create more `clusterregistrationtokens.management.cattle.io` objects (as the UI does if the GET API call returns an empty list).
"""


class RancherRegistrationAction (ActionBase, RancherActionMixin):
    """Obtain the data structure that feeds the “Cluster Management” → “Registration” tab in the Rancher UI.
    """
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        super(RancherRegistrationAction, self).run(args, ansible_api)
        self._init_rancher(ansible_api=ansible_api)

        if "cluster_name" in args:
            self.rancher_cluster_name = args["cluster_name"]

        base_url = args.get("rancher_manager_url", self.rancher_base_url)

        self.rancher = RancherManagerAPIClient(
            base_url=base_url,
            api_key=self._obtain_token())

        try:
            return {
                "changed": False,
                "registration": self.get_first_registration()
            }
        except IndexError:
            # No more cluster tokens? Make new ones. (This is also
            # what the UI does if you delete everything.)
            self.rancher.renew_cluster_registrations(self.cluster_id)
            return {
                "changed": True,
                "registration": self.get_first_registration()
            }

    def get_first_registration (self):
        registrations = self.rancher.get_cluster_registrations(self.cluster_id)
        # Apparently the UI always picks the first entry in the
        # list (even if you deleted a few).
        return registrations[0]

    @cached_property
    def cluster_id (self):
        return self.rancher.get_cluster_id(self.rancher_cluster_name)


ActionModule = RancherRegistrationAction

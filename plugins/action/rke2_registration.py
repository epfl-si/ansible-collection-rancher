from functools import cached_property

from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin

_not_set = object()

class RancherRegistrationAction (ActionBase, RancherActionMixin):
    """Obtain the data structure that feeds the “Cluster Management” → “Registration” tab in the Rancher UI.

    See operation details and Ansible-level documentation in
    ../modules/rke2_registration.py which only exists for documentation
    purposes.
    """
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        super(RancherRegistrationAction, self).run(args, ansible_api)
        self._init_rancher(ansible_api=ansible_api)

        if "cluster_name" in args:
            self.rancher_cluster_name = args["cluster_name"]

        if "rancher_manager_url" in args:
            self.rancher_base_url = args["rancher_manager_url"]

        try:
            # Apparently the UI always picks the first entry in the
            # list (even if you deleted a few).
            return {
                "changed": False,
                "registration": self.registration_tokens.first()
            }
        except IndexError:
            # No more cluster tokens? Make new ones. (This is also
            # what the UI does if you delete everything.)
            self.registration_tokens.make_more()
            return {
                "changed": True,
                "registration": self.registration_tokens.first()
            }

    @property
    def registration_tokens (self):
        return self.rancher_manager.get_cluster_by_name(self.rancher_cluster_name).registration_tokens


ActionModule = RancherRegistrationAction

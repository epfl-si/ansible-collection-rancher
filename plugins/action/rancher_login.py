from functools import cached_property

from ansible.errors import AnsibleUndefinedVariable
from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import exceptions as k8s_exceptions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_model import RancherManager
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin

class RancherLoginAction (ActionBase, RancherActionMixin):
    """Download a Kubeconfig file from the rancher back-end.

    See operation details and Ansible-level documentation in
    ../modules/rancher_login.py which only exists for documentation
    purposes.
    """
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        self._init_rancher(ansible_api=ansible_api)

        explicit_cluster_name = args.get('cluster_name')
        if explicit_cluster_name:
            self.rancher_cluster_name = explicit_cluster_name

        self.result["kubeconfig"] = self.rancher_manager.get_cluster_by_name(self.rancher_cluster_name).download_kubeconfig()
        return self.result

ActionModule = RancherLoginAction

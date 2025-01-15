from functools import cached_property

from ansible.errors import AnsibleUndefinedVariable
from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import exceptions as k8s_exceptions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherAPIClient, RancherManagerAPIClient
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

        token = self._obtain_token()
        rancher_api_cluster_id = RancherManagerAPIClient(
            self.rancher_base_url,
            token).get_cluster_id(self.rancher_cluster_name)

        client = RancherAPIClient(
            api_key=token,
            base_url=self.rancher_base_url,
            rancher_api_cluster_id=rancher_api_cluster_id,
            ca_cert=self._expand_var("ansible_rancher_ca_cert", None),
            validate_certs=self._expand_var("ansible_rancher_validate_certs", True))
        self.result["kubeconfig"] = client.download_kubeconfig()
        return self.result

ActionModule = RancherLoginAction

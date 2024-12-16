from functools import cached_property

from kubernetes.client.exceptions import ApiException

from ansible.errors import AnsibleUndefinedVariable
from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import exceptions as k8s_exceptions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherAPIClient, RancherManagerAPIClient
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin

class RancherLoginAction (ActionBase, RancherActionMixin):
    """Download a Kubeconfig file from the rancher back-end.

    In the “worst best case” (i.e. success with all caches cold), this action

    1. connects over ssh to the node where the Rancher front-end is running,
    2. creates an authentication token as a `kind: Token` object with a very short expiration time,
    3. requests the “child” cluster's kubeconfig from the Rancher backend (like the Web UI would), using the token for authentication.

    `epfl_si.rancher.login` saves the downloaded kubeconfig to the directory
    named by the `ansible_rancher_credentials_dir` variable.

    All three steps are bypassed if a previously dowloaded kubeconfig still contains valid
    credentials.
    """
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        super(RancherLoginAction, self).run(args, ansible_api)
        self._init_rancher(ansible_api=ansible_api)

        self.cluster_name = args.get('cluster_name')

        if not self.is_kubeconfig_still_valid():
            self.save_kubeconfig(self.do_download_kubeconfig())
        return self.result

    def save_kubeconfig (self, kubeconfig_content):
        self.change(
            "ansible.builtin.copy",
            dict(dest=self.kubeconfig_path,
                 content=kubeconfig_content))

    def is_kubeconfig_still_valid (self):
        try:
            RancherAPIClient(kubeconfig=self.kubeconfig_path)
            return True
        except k8s_exceptions.CoreException:
            # Happens when there is no kubeconfig file
            return False
        except ApiException:
            # Happens when the `server:` value in the kubeconfig is bogus
            return False

    @property
    def kubeconfig_path (self):
        if self._expand_var('ansible_rancher_credentials_dir', None) is not None:
            return super().kubeconfig_path
        else:
            # For backwards compatibility...
            retval = self._expand_var('ansible_rancher_credentials_file')
            if self._cluster_name_explicitly_set:
                # ... or lack thereof
                raise ValueError('Please use `ansible_rancher_credentials_dir`, rather than '
                                 '`ansible_rancher_credentials_file`, if you want to log in to '
                                 'a specific cluster in the Rancher inventory.')
            return retval

    def do_download_kubeconfig (self):
        """The “cold cache” path."""
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
        return client.download_kubeconfig()


ActionModule = RancherLoginAction

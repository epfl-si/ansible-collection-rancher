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

    1. connect over ssh to the node where the Rancher front-end is running,
    2. create an authentication token as a `kind: Token` object with a very short expiration time,
    3. request the “child” cluster's kubeconfig from the Rancher backend (like the Web UI would),
       using the token for authentication,
    4. present the result of same as the `.kubeconfig` property of the task result.

    ⚠ This action *does not* check any pre-existing credentials; as a
    consequence, it always satisfies the `is changed` Jinja predicate
    (a.k.a. is “always yellow” in the Ansible UI). Likewise, this
    action doesn't store the retrieved credentials in a kubeconfig
    file. It behooves the calling role or playbook to take care of
    both.

    Recognized task args:
        cluster_name      The name of the cluster (the one you see in the
                          “name” column on the Rancher dashboard). Defaults
                          to the `ansible_rancher_cluster_name` variable,
                          if set.

    Ansible variables used:
        ansible_rancher_cluster_name   The default for the `cluster_name`
                                       task argument

        ansible_rancher_url            The hostname portion of that URL
                                       indicates the host to ssh into to
                                       obtain credentials

        ansible_rancher_ca_cert
        ansible_rancher_validate_certs The usual parameters for
                                       server-to-client TLS authentication,
                                       shared with other tasks in this Ansible
                                       collection. At least one of these
                                       must be set. `ansible_rancher_ca_cert`,
                                       if set, must be a string in multiline
                                       PEM format.
                                       `ansible_rancher_validate_certs` is
                                       a Boolean.

        ansible_rancher_username       The Rancher username that the
                                       retrieved credentials will belong to;
                                       defaults to “admin”

        ansible_rancher_token_stem     The prefix of the short-lived bearer
                                       token that `epfl_si.rancher.rancher_login`
                                       creates for itself in order to
                                       download the (longer-lived)
                                       credentials in kubeconfig
                                       format. Visible forever (we
                                       think ?) with `kubectl get
                                       token` in the `local` cluster,
                                       even though they expire after
                                       two minutes.
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

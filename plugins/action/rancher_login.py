from functools import cached_property
import getpass
import socket
from urllib.parse import urlparse

from kubernetes.client.exceptions import ApiException

from ansible.errors import AnsibleUndefinedVariable
from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions, Subaction
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import exceptions as k8s_exceptions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherAPIClient

_not_set = object()

class RancherLoginAction (ActionBase):
    """Download a Kubeconfig file from the rancher back-end.

    In the “worst best case” (i.e. success with all caches cold), this action

    1. connects over ssh to the node where the Rancher front-end is running,
    2. creates an authentication token as a `kind: Token` object with a very short expiration time,
    3. requests the “child” cluster's kubeconfig from the Rancher backend (like the Web UI would), using the token for authentication.

    `epfl_si.rancher.login` saves the downloaded kubeconfig to the file
    named by the `ansible_rancher_credentials_file` variable.

    All three steps are bypassed if the
    `ansible_rancher_credentials_file` still contains valid
    credentials.
    """
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        self.ansible_api = ansible_api

        self.result = dict(changed=False)
        if not self.is_kubeconfig_still_valid():
            self.save_kubeconfig(self.do_download_kubeconfig())
        return self.result

    def save_kubeconfig (self, kubeconfig_content):
        self.change(
            "ansible.builtin.copy",
            dict(dest=self.kubeconfig_path,
                 content=kubeconfig_content),
            overrides=dict(ansible_python_interpreter=self._expand_var('ansible_playbook_python')),
            connection=self._local_connection)

    @cached_property
    def kubeconfig_path (self):
        return self._expand_var('ansible_rancher_credentials_file')

    def _expand_var (self, var_name, default=_not_set):
        if default is not _not_set and not self.ansible_api.has_var(var_name):
            return default
        else:
            return self.ansible_api.expand_var('{{ %s }}' % var_name)

    @cached_property
    def _local_connection (self):
        return self.ansible_api.make_connection(
            ansible_connection="local",
            # TODO: does this work sometimes? Or at all?
            env=dict(
                KUBECONFIG=self.kubeconfig_path,
                K8S_AUTH_KUBECONFIG=self.kubeconfig_path))

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

    def do_download_kubeconfig (self):
        """The  “cold cache” path."""
        return RancherAPIClient(
            api_key=self._obtain_token(),
            base_url=self.rancher_base_url,
            rancher_api_cluster_id=self.rancher_api_cluster_id,
            ca_cert=self._expand_var("ansible_rancher_ca_cert", None),
            validate_certs=self._expand_var("ansible_rancher_validate_certs", True)).download_kubeconfig()

    _obtain_token_action_name = 'epfl_si.rancher._rancher_obtain_token'

    def _obtain_token (self):
        if self.ansible_api.check_mode.is_active:
            result = dict(
                changed=True,
                token="MOCK:TOKEN_FOR_CHECK_MODE")
            self.result.update(result)
        else:
            result = self.change(
                self._obtain_token_action_name,
                dict(cluster_name=self._expand_var('ansible_rancher_cluster_name'),
                     impersonate=self._expand_var('ansible_rancher_username', 'admin'),
                     stem=self.token_stem),
                connection=self._rancher_ssh_connection)
        return result['bearer_token']

    @property
    def token_stem (self):
        stem = self._expand_var(
            'ansible_rancher_token_stem',
            "ansible-%s-%s" % (getpass.getuser().lower(),
                       socket.gethostname().lower()))
        if not stem.endswith('-'):
            stem = stem + '-'
        return stem

    @cached_property
    def _rancher_ssh_connection (self):
        return self.ansible_api.make_connection(
            ansible_connection="ssh",
            ansible_ssh_host=self.rancher_hostname)

    @cached_property
    def rancher_base_url (self):
        return self._expand_var('ansible_rancher_url')

    @property
    def rancher_hostname (self):
        return urlparse(self.rancher_base_url).hostname

    def change (self, task_name, task_args, **subaction_kwargs):
        result = self._subaction.change(
            task_name, task_args, **subaction_kwargs)
        self.result.update(result)
        return result

    @property
    def rancher_api_cluster_id (self):
        return 'c-m-gdkcxchl' # XXX

    @cached_property
    def _subaction (self):
        return Subaction(self.ansible_api)

ActionModule = RancherLoginAction

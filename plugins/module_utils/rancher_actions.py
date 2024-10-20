"""Common material for Rancher-related action plugins."""

from abc import ABC, abstractmethod
from functools import cached_property
import getpass
import socket
from urllib.parse import urlparse

from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import Subaction


_not_set = object()


class RancherActionMixin(ABC):
    """Things that are useful to more than one action plugin.

    How to use:
    - Caller class should multiply inherit from both `ansible.plugins.action.ActionBase` and this here `RancherActionMixin`
    - Caller class should overload the `run()` method and call both super-methods, like so:

      @AnsibleActions.run_method
      def run (self, args, ansible_api):
          super(RancherLoginAction, self).run(args, ansible_api)
          RancherActionMixin.run(self, args, ansible_api)
    """
    @abstractmethod
    def run (self, args, ansible_api):
        self.ansible_api = ansible_api
        self.result = dict(changed=False)

    def _expand_var (self, var_name, default=_not_set):
        if default is not _not_set and not self.ansible_api.has_var(var_name):
            return default
        else:
            return self.ansible_api.expand_var('{{ %s }}' % var_name)

    _obtain_token_action_name = 'epfl_si.rancher._rancher_obtain_token'

    def _obtain_token (self):
        if self.ansible_api.check_mode.is_active:
            result = dict(
                changed=True,
                token="MOCK:TOKEN_FOR_CHECK_MODE")
            self.result.update(result)
        else:
            result = self.change_over_ssh(
                self._obtain_token_action_name,
                dict(cluster_name=self._expand_var('ansible_rancher_cluster_name'),
                     impersonate=self._expand_var('ansible_rancher_username', 'admin'),
                     stem=self.token_stem))
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

    @property
    def rancher_hostname (self):
        return urlparse(self.rancher_base_url).hostname

    @cached_property
    def rancher_base_url (self):
        return self._expand_var('ansible_rancher_url')

    def change (self, task_name, task_args):
        result = self._subaction.change(
            task_name, task_args)
        self.result.update(result)
        return result

    def change_over_ssh (self, task_name, task_args):
        result = self._subaction.change(
            task_name, task_args,
            overrides=dict(ansible_python_interpreter='/usr/bin/python3'),
            connection=self._rancher_ssh_connection)
        self.result.update(result)
        return result

    @cached_property
    def _rancher_ssh_connection (self):
        return self.ansible_api.make_connection(
            ansible_connection="ssh",
            ansible_ssh_host=self.rancher_hostname)

    @cached_property
    def _subaction (self):
        return Subaction(self.ansible_api)

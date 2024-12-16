"""Common material for Rancher-related action plugins."""

from abc import ABC, abstractmethod
from functools import cached_property
import getpass
import os
import socket
from urllib.parse import urlparse

from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import Subaction
from ansible_collections.epfl_si.actions.plugins.module_utils.ansible_api import AnsibleActions


_not_set = object()


class RancherActionMixin(ABC):
    """Things that are useful to more than one action plugin.

    How to use:
    - Caller class should multiply inherit from both `ansible.plugins.action.ActionBase` and this here `RancherActionMixin`
    - Caller class must call `_init_rancher` at construction time, e.g.

        @AnsibleActions.run_method
        def run (self, args, ansible_api):
            self._init_rancher(ansible_api=ansible_api)
            # ...

      or just (for the “old-school” API sans `AnsibleActions`)

        def run (self, task_vars=None):
            self._init_rancher(task_vars=task_vars)
            # ...
    """
    def _init_rancher (self, ansible_api=None, task_vars=None):
        if ansible_api is not None:
            self.ansible_api = ansible_api
        elif task_vars is not None:
            self.ansible_api = AnsibleActions(self, task_vars)
        else:
            raise TypeError("Either `ansible_api` or `task_vars` must be set.")
        self.result = dict(changed=False)

    def _expand_var (self, var_name, default=_not_set):
        jinja = self.ansible_api.jinja
        if default is not _not_set and var_name not in jinja.vars:
            return default
        else:
            return jinja.expand('{{ %s }}' % var_name)

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

    @property
    def rancher_cluster_name (self):
        try:
            return self._explicitly_set_rancher_cluster_name
        except AttributeError:
            return self._expand_var("ansible_rancher_cluster_name")

    @rancher_cluster_name.setter
    def rancher_cluster_name (self, cluster_name):
        self._explicitly_set_rancher_cluster_name = cluster_name

    def change (self, task_name, task_args):
        result = self._subaction.change(
            task_name, task_args)
        self.result.update(result)
        return result

    def change_over_ssh (self, task_name, task_args):
        result = self._subaction.change(
            task_name, task_args,
            overrides=dict(
                ansible_connection="ssh",
                ansible_ssh_host=self.rancher_hostname,
                ansible_python_interpreter='/usr/bin/python3'))
        self.result.update(result)
        return result

    @cached_property
    def _subaction (self):
        return Subaction(self.ansible_api)

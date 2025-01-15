import datetime
import json
import os
import random
import re
import shutil
import socket
import string
import subprocess

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: _rancher_obtain_token
short_description: Obtain a “master” token (valid for Rancher's “Norman” API)
description:
  - This task first creates a C(kind: Token) object if a suitable one
      doesn't exist already; then returns the C(.token) value within.
  - This task is supposed to run over ssh on (one of) the Rancher master
      node(s).
requirements:
  - The C(kubectl) go binary must be installed on the remote Rancher server.
options:
  cluster_name:
    type: str
    required: true
    description:
      - The name of the cluster to create a token for.
  impersonate:
    type: str
    default: "admin"
    description:
      - >
        The name of the user to impersonate. (Equal to the C(.username)
        of the C(kind: User) object to impersonate). User must already exist.
  stem:
    type: str
    required: true
    description:
      - The prefix to use for the Kubernetes C(name) in case a new token
        needs to be created. Must end with a dash.
  validity:
    type: str
    default: "2min"
    description:
      - The validity time of new tokens, as a string formed of digits
        optionally followed by a time unit picked among 's', 'm'
        (or equivalently) 'min', 'h' or 'd'. 's' is the default time
        limit.
"""

RETURN = r"""
bearer_token:
    description: The bearer token value, complete with the name prefix
    type: str
    returned: always
    sample: 'koom7die5ohNgokoo6nung7ciesh7chae1Eici9fie5iDeinaere6r'
changed:
    description: Whether a new token was created (as per Ansible standard)
    type: bool
    returned: always
    sample: True
"""

def parse_duration (duration):
    """Parse a string duration e.g. "10s" or "10m" into a `datetime.timedelta`."""
    if type(duration) == int:
        return datetime.timedelta(seconds=duration)

    matched = re.match(r"^([1-9]\d*)([a-z]*)$", str(duration))

    if not matched:
        raise ValueError("Invalid duration format: %s" % duration)

    qty, unit = matched.groups()

    multipliers = {
        '': 1,
        's': 1,
        'm': 60,
        'min': 60,
        'h': 3600,
        'd': 86400
    }
    if unit not in multipliers:
        return ValueError('Unknown time unit: %s' % unit)

    return datetime.timedelta(seconds=multipliers[unit]*int(qty))


class RancherObtainTokenModule:
    argspec = dict(
        cluster_name=dict(type='str', required=True),
        impersonate=dict(type='str', default='admin'),
        stem=dict(type='str', required=True),
        validity=dict(type='str', default='2min'))

    def __init__ (self):
        self.module = AnsibleModule(self.argspec)

        def bearer_token(name, secret):
            return "%s:%s" % (name, secret)

        for token in self._get_tokens_with_stem(self.stem):
            self.module.exit_json(
                changed=False,
                bearer_token=bearer_token(token['metadata']['name'],
                                          token['token']))

        # No token? No problem, let's make one up!
        user_login_name = self.module.params['impersonate']
        user = self.get_user_by_name(user_login_name)
        token = self._make_fresh_token()
        name = self.stem + self._make_random_string(length=6)

        self._kubectl_apply('''
apiVersion: management.cattle.io/v3
kind: Token
metadata:
  name: %(name)s
  labels:
    authn.management.cattle.io/kind: kubeconfig
    authn.management.cattle.io/token-userId: %(user_id)s
    cattle.io/creator: Ansible
authProvider: local
description: Kubeconfig token generated by the epfl_si.rancher Ansible collection
expired: false
expiresAt: "%(expires_at_zulu)s"
token: %(token)s
userId: %(user_id)s
userPrincipal:
  displayName: %(user_display_name)s
  loginName: %(user_login_name)s
  metadata:
    creationTimestamp: null
    name: local://%(user_id)s
  principalType: user
  provider: local
''' %   dict(
            name=name,
            user_id=user['metadata']['name'],
            expires_at_zulu=self.new_token_expires_at_zulu,
            token=token,
            user_display_name=user['displayName'],
            user_login_name=user_login_name))
        self.module.exit_json(
            changed=True,
            bearer_token=bearer_token(name, token))

    def get_user_by_name (self, username):
        print("username: %s" % username)
        [the_user] = (user for user in self._kubectl_get(
                                 'User.management.cattle.io')
                      if user.get('username', None) == username)
        return the_user

    def _get_tokens_with_stem (self, stem):
        return (tok for tok in self._kubectl_get(
                                 'Token.management.cattle.io')
                if tok['metadata']['name'].startswith(stem))

    def _kubectl_get (self, *cmdline):
        kubectl_stdout = self._kubectl_subprocess(
            ['get', '-o', 'json'] + list(cmdline),
            stdout=subprocess.PIPE).stdout
        return json.loads(kubectl_stdout)['items']

    def _kubectl_apply (self, yaml_string):
        self._kubectl_subprocess(
            ['apply', '-f', '-'],
            input=yaml_string.encode('utf-8'))

    def _kubectl_subprocess (self, args, **subprocess_run_kwargs):
        kubectl_path = shutil.which('kubectl',
                                    path="/usr/local/bin:%s" % os.environ.get('PATH', ''))
        return subprocess.run(
            args=[kubectl_path] + args,
            shell=False,
            check=True,
            env=dict(KUBECONFIG=self._get_kubeconfig_path()),
            **subprocess_run_kwargs)

    def _get_kubeconfig_path (self):
        for guess in (
                '/etc/rancher/k3s/k3s.yaml',
                '/var/lib/rancher/rke2/server/cred/admin.kubeconfig'):
            if os.path.exists(guess):
                return guess

        raise FileNotFoundError("Cannot find suitable Kubeconfig file on %s"
                                % socket.gethostname())

    @property
    def cluster_name (self):
        return self.module.params['cluster_name']

    @property
    def stem (self):
        return self.module.params['stem']

    @property
    def new_token_expires_at_zulu (self):
        expires_at = datetime.datetime.now() + parse_duration(
            self.module.params['validity'])
        return expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def impersonate (self):
        return self.module.params.get('impersonate', 'admin')

    def _make_fresh_token (self):
        return self._make_random_string(length=54)

    def _make_random_string (self, length):
        return ''.join(random.choices(string.ascii_lowercase + string.digits,
                                      k=length))

if __name__ == "__main__":
    RancherObtainTokenModule().run()

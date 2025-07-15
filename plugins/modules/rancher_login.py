# This file is here for ansible-doc purposes **only**. The actual
# implementation is in ../action/rancher_login.py as an action plugin
# (i.e. it runs on the Ansible controller.)

DOCUMENTATION = r'''
---
module: rancher_login
short_description: Log in to Rancher
description:
- This module is implemented as an B(action plugin), meaning that it
  runs on the Ansible controller (*not* over any remote shell,
  regardless of `ansible_connection` etc. settings)

- This action plugin retrieves Kubernetes-style credentials (i.e.
  C(kubeconfig) files) from the Rancher back-end. It B(does not)
  revalidate pre-existing credentials, or store them to disk. It
  behooves the calling role or playbook to take care of both; see
  EXAMPLES.

- >
  This action plugin first connects over ssh to the node where the
  Rancher front-end is running (as deduced from the
  C(ansible_rancher_url) variable). It then generates an
  authentication token as a C(kind: Token) object with a very short
  expiration time if required; and finally it uses that to request the
  “child” cluster's kubeconfig from the Rancher backend, like the Web
  UI would.

- 💡 This action plugin obtains credentials over ssh,
  regardless of your C(ansible_connection) setting; and you should
  therefore set either the C(ansible_user) or the C(ansible_ssh_user)
  variable to specify the remote username to connect as (even though
  the rest of your playbook may not make use of that variable).

- "This action plugin reads from the following Ansible variables:"

- C(ansible_rancher_cluster_name)
- The default for the C(cluster_name) task argument

- C(ansible_rancher_url)
- The hostname portion of that URL
  indicates the host to ssh into to
  obtain credentials

- C(ansible_rancher_validate_certs)
- (Boolean) Whether to authenticate the TLS server. Setting this to false B(is insecure).
  At least one of C(ansible_rancher_validate_certs) or C(ansible_rancher_ca_cert) must be set.

- C(ansible_rancher_ca_cert)
- The CA certificate to validate the Rancher TLS server, as a string in multiline
  PEM format.

- C(ansible_rancher_username)
- The Rancher username that the
  retrieved credentials will belong to;
  defaults to “admin”

- C(ansible_rancher_token_stem)
- The prefix of the short-lived bearer token that this action plugin
  creates for itself in order to download the (longer-lived)
  credentials in kubeconfig format. The tokens remain visible forever
  (we think ?) with C(kubectl get token) in the C(local) cluster, even
  though they expire after two minutes.

options:
  cluster_name:
    description: >
      The name of the cluster (the one you see in the
      “name” column on the Rancher dashboard). Defaults
      to the value of the C(ansible_rancher_cluster_name)
      variable.

version_added: 0.2.1

'''

RETURN = r'''
changed:
  type: bool
  description: True (“yellow”) iff creating a new C(Token) Kubernetes object
               was necessary to retrieve the credentials. That is,
               re-using an existing C(Token) results in unchanged (”green”)
               Ansible outcome; or to put it otherwise, the part where we fetch
               the Kubeconfig “doesn't count” for green / yellow.

kubeconfig:
  description: The contents of the C(kubeconfig) file downloaded from the Rancher backend,
               as an unparsed, multiline YAML string.
  type: str
'''

EXAMPLES = r'''
- changed_when: false
  shell:
    cmd: |
      if KUBECONFIG="$K8S_AUTH_KUBECONFIG" kubectl get pods ; then
        echo "CREDENTIALS_ARE_STILL_VALID"
        exit 0
      fi
  register: _credentials_check

- when: >-
     "CREDENTIALS_ARE_STILL_VALID" not in _credentials_check.stdout
  epfl_si.rancher.rancher_login: {}
  register: _rancher_login

- when: >-
     "CREDENTIALS_ARE_STILL_VALID" not in _credentials_check.stdout
  copy:
    dest: >-
      {{ lookup("env", "K8S_AUTH_KUBECONFIG") }}
    content: >-
      {{ _rancher_login.kubeconfig }}
'''

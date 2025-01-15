# This file is here for ansible-doc purposes **only**. The actual
# implementation is in ../action/rancher_helm_chart.py as an action plugin
# (i.e. it runs on the Ansible controller.)

DOCUMENTATION = r'''
---
module: rancher_registration
short_description: Prepare the command line for registering a node into Rancher
description:

- This action plugin is intended for internal consumption by the M(epfl_si.rancher.rke2-node) role.
  It is not really meant to be used directly.

- This action plugin acts as a helper to register nodes into an
  existing Rancher cluster. It ensures that at least one
  C(clusterregistrationtokens.management.cattle.io) object exists for
  your cluster, and returns the list of them as the C(registrations)
  property of the task's return value.

- This action plugin authenticates against the master Rancher back-end
  (for the case where the cluster doesn't already exist). To this end,
  it fetches (or creates) a token behind the scenes by running a
  M(epfl_si.rancher.rancher_login) task.

- "This action plugin reads from the following Ansible variables:"

- C(ansible_rancher_cluster_name)
- The default for the C(cluster_name) task argument, and also the
  name of the cluster to obtain a token for.
# Yes, that means there's a bug there, and that the cluster_name
# task arg doesn't actually work. TODO: fix this.

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
  rancher_manager_url:
    type: str
    default: value of the C(ansible_rancher_manager_url) variable
    description: The URL of the Rancher manager to register into

  cluster_name:
    type: str
    default: value of the C(ansible_rancher_cluster_name) variable
    description: The display name of the cluster to register into

version_added: 0.2.1

'''

RETURN = r'''
registration:
    description: The first entry in the list of C(clusterregistrationtokens.management.cattle.io) objects stored in the management Rancher. The Rancher UI apparently uses this one for its “Cluster Management” → “Registration” tab.
    type: dict
    returned: always
changed:
    description: Whether the task had to ask the Rancher back-end to create more C(clusterregistrationtokens.management.cattle.io) objects (as the UI does if the GET API call returns an empty list).

'''

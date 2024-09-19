# `epfl_si.rancher.rke2_access` role

This role ensures that a suitable Kubeconfig file exists, and contains up-to-date credentials, so as to connect to a RKE2 cluster.

The `epfl_si.rancher.rke2_access` role expects the following variables to be set:

- `rke2_cluster_token_store` <br/> The filename for the Kubeconfig file to create or refresh. The role takes care of (recursively) creating any required directories above this filename.
- `rancher_hostname` <br/> The hostname to `ssh` into (as root), in order to retrieve the credentials. Suitable credentials to the “parent” Kubernetes cluster (the one where the Rancher UI runs) should exist on that host at `/etc/rancher/k3s/k3s.yaml`, as per [the Rancher documentation](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/kubernetes-cluster-setup/k3s-for-rancher#3-save-and-start-using-the-kubeconfig-file). <br/> 💡 The remote host is assumed to have the `kubectl` command installed.
- `rke2_cluster_name` <br/> The name of the cluster created or imported by Rancher. The name of the Kubernetes `Secret` containing the access token (in namespace `fleet-default`) is computed as `{{ rke2_cluster_name }}-kubeconfig`.

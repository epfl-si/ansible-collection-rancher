# `epfl_si.rancher.cached_login` Ansible role

A convenience wrapper for the `epfl_si.rancher.rancher_login` task,
that persists and caches the credentials to a file.

Here is an example of how to invoke this role from a tasks file:

```yaml
- name: Log in to Rancher if needed
  include_role: epfl_si.rancher.cached_login
```

The following variables must be set:

- `ansible_rancher_url` <br/>
  The base URL of the Rancher manager to exert API calls on
- `ansible_k8s_kubeconfig` <br/>
  The cache file. Will be fetched anew using `epfl_si.rancher.rancher_login`,
  unless the credentials it contains are still valid
- `ansible_rancher_cluster_name` <br/>
  The name of the cluster to log into in Rancher
- `ansible_ssh_user` <br/>
  The user on `inventory_hostname` to connect to, if required (given that
  `epfl_si.rancher.rancher_login` works over ssh)

## Delegation Support for Multi-Cluster Playbooks

Since `epfl_si.rancher` supports Ansible delegation, so
does this role. For instance, suppose you have work to do in the
Rancher manager cluster, like setting up a downstream cluster:

```yaml
# roles/downstreamcluster/tasks/upstream.yml

- tags: always
  include_role:
    name: epfl_si.rancher.cached_login

- name: Cluster object in upstream Rancher
  epfl_si.k8s.k8s:
    definition:
      apiVersion: provisioning.cattle.io/v1
      kind: Cluster
      metadata:
        name: my-cluster
        namespace: fleet-default
      # ...
```

Then you would want to make it so that these two tasks (and only them)
apply to the Rancher upstream cluster. Here is an example of how to
achieve that from your playbook using `delegate_to` in combination
with `include_role` and `tasks_from` (… and a touch of `apply.vars`, owing to the
[quirky semantics of delegated vars](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_delegation.html#templating-in-delegation-context)):

```
# playbook.yml

- hosts: downstream_clusters
  name: "Create cluster in upstream"
  tasks:
      - include_role:
          name: downstreamcluster
          tasks_from: upstream.yml
    apply:
      delegate_to: rancher-manager-vm.example.com
      vars:
        ansible_k8s_kubeconfig: >-
          {{ hostvars[inventory_hostname].ansible_k8s_kubeconfig }}

# ... then you can have a play that adds nodes to the cluster...

# ... then after the cluster is up and running, maybe you want to invoke
# the `downstreamcluster` role again through its ordinary
# entry point `tasks/main.yml`, without delegation:

- hosts: downstream_clusters
  name: "Configure cluster"
  roles:
    - role: downstreamcluster
```

and then `roles/downstreamcluster/tasks/main.yml` would also start by invoking
`epfl_si.rancher.cached_login` on the downstream cluster, i.e.

```yaml
# roles/downstreamcluster/tasks/main.yml

- tags: always
  include_role:
    name: epfl_si.rancher.cached_login

# ... Do other things in the downstream cluster
```

Here is a sample inventory fragment suitable for this scenario:

```yaml
# inventory.yml
all:
  vars:
    ansible_rancher_url: https://rancher-manager.example.com/
  hosts:
    rancher-manager-vm.example.com:
      ansible_k8s_kubeconfig: "rke2-credentials-cache/local.yaml"
      ansible_rancher_cluster_name: local
      ansible_ssh_user: root
  children:
    downstream_clusters:
      "hosts":  # Scarequotes intended — This group contains Kubernetes
                # clusters, but Ansible doesn't know or care
        cluster/mycluster:
          ansible_k8s_kubeconfig: "rke2-credentials-cache/mycluster.yaml"
          ansible_rancher_cluster_name: my-cluster
```

# Ansible Collection — `epfl_si.rancher`

## `epfl_si.rancher.rancher_login` Module

The `epfl_si.rancher.rancher_login` module retrieves Kubernetes-style credentials (i.e. `kubeconfig` files) from the Rancher back-end. It *does not* revalidate pre-existing credentials, or store them to disk. You need to do that yourself, for instance like this:

```yaml
- changed_when: false
  ignore_errors: true
  shell:
    cmd: |
      KUBECONFIG="$K8S_AUTH_KUBECONFIG" kubectl get pods
  register: _credentials_check

- when: _credentials_check is failed
  epfl_si.rancher.rancher_login:
    cluster_name: mycluster
  register: _rancher_login

- when: _credentials_check is failed
  copy:
    dest: >-
      {{ lookup("env", "K8S_AUTH_KUBECONFIG") }}
    content: >-
      {{ _rancher_login.kubeconfig }}
```

Or equivalently, in case you don't mind the extra complexity, but you *do* mind the red:

```yaml
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
```

`epfl_si.rancher.rancher_login` connects to the cluster designated by the `ansible_rancher_cluster_name` variable by default. This can be overridden using the `cluster_name` task argument:

```yaml
- epfl_si.rancher.rancher_login:
    cluster_name: local
  register: _rancher_login_to_rancher

- environment: '{{ lookup("epfl_si.rancher.rke2_access_environment", cluster_name="local") }}'
  kubernetes.core.k8s:
    kubeconfig: "{{ _rancher_login_to_rancher | from_yaml }}"
    apiVersion: provisioning.cattle.io/v1
    kind: Cluster
    metadata:
      name: "{{ ansible_rancher_cluster_name }}"
      namespace: fleet-default
      annotations:
        ui.rancher/badge-color: transparent
        ui.rancher/badge-icon-text: MYC
    spec:
      kubernetesVersion: v1.30.4+rke2r1
      rkeConfig: # ...
      # ...
```

The above creates a cluster for you inside the Rancher manager.

💡 `epfl_si.rancher.rancher_login` obtains credentials over ssh, regardless of your `ansible_connection` setting; and you should therefore set either the `ansible_user` or the `ansible_ssh_user` variable to specify the remote username to connect as (even though the rest of your playbook may not make use of that variable).

The status of the `epfl_si.rancher.rancher_login` task `is changed` (“yellow”) if obtaining the credentials required creating a new `Token` Kubernetes, with very short validity (2 minutes). It `is not changed` if said `Token` (“green”) could be re-used.

## `epfl_si.rancher.rancher_k8s_api_call` Module

This module lets your configuration-as-code exert the same API calls that your browser does; thereby allowing you to automate some operations typically done through the Rancher UI.

This module expects the `K8S_AUTH_KUBECONFIG` environment variable to be set, and to point to a suitable Kubeconfig file (e.g. one downloaded from the Rancher UI).

**⚠ This module always returns a “changed” (yellow) Ansible result.** It is up to you to short-circuit it (using a `when:` clause) if its post-condition is already met.

Here is an example task to install the [NFS subdir external provisioner](https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/) from its Helm chart, so as to provide NFS-based persistence:

```yaml
- epfl_si.rancher.rancher_k8s_api_call:
    method: POST   # ①
    uri: /v1/catalog.cattle.io.clusterrepos/nfs-subdir-external-provisioner?action=install   # ②
    body:
      charts:
        - annotations:
            catalog.cattle.io/ui-source-repo-type: cluster
            catalog.cattle.io/ui-source-repo: nfs-subdir-external-provisioner # ③
          chartName: nfs-subdir-external-provisioner
          releaseName: nfs-subdir-external-provisioner
          resetValues: false
          version: 4.0.18
          values: # ④
            nfs:
              server: nas-app-ma-nfs2.epfl.ch
              path: /svc1160_gitlab_test_app/nfs-storageclass
            storageClass:
              defaultClass: true
      cleanupOnFail: false
      force: false
      historyMax: 5
      namespace: nfs-subdir-external-provisioner-system  # ⑤
      noHooks: false
      timeout: 600s
      wait: true
```

①, ② These are the HTTP method and URL that your browser employs while performing the install “by hand” (from your cluster dashboard → Apps → Charts)

③ This points to a `ClusterRepo` object of the same name (as part of the `catalog.cattle.io` Kubernetes API). One could enforce that that object exists, using a `kubernetes.core.k8s` task that comes before this one.

④ Unlike what appears to happen in the UI, there is no need to transmit a complete `values.yaml` file; only those values that were edited from the defaults need to be set.

⑤ Likewise, the target namespace should exist already; which one can enforce using a `kubernetes.core.k8s` task that creates the `Namespace` object.

## `epfl_si.rancher.rancher_project` Lookup Plugin

This lookup plugin searches for `Project.management.cattle.io` objects belonging to the current cluster (the one that the `ansible_rancher_cluster_name` variable points to).

Here is how to use it to make a “system” namespace, as seen by the rancher dashboard:

```yaml
- name: "`namespace/something-something-system`"
  kubernetes.core.k8s:
    definition:
      kind: Namespace
      metadata:
        name: "something-something-system"
        annotations:
          field.cattle.io/projectId: "{{ _project.spec.clusterName }}:{{ _project.metadata.name }}"
  vars:
    _project: >-
      {{ lookup("epfl_si.rancher.rancher_project",
                kubeconfig="/where/the/rancher/master/credentials/are",
                display_name="System") }}
```

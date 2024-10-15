# Ansible Collection — `epfl_si.rancher`

## `epfl_si.rancher.rancher_login` Module

This module lets you retrieve Kubernetes-style credentials (i.e. `kubeconfig` files) from the Rancher back-end, and store them locally in the directory pointed to by the `ansible_rancher_credentials_dir` variable.

For instance, the following task

```yaml
- epfl_si.rancher_rancher_login: {}
```

retrieves credentials for the default cluster (the one whose name is in the `ansible_rancher_cluster_name` variable); while

```yaml
- epfl_si.rancher_rancher_login:
    cluster_name: local

- environment: '{{ lookup("epfl_si.rancher.rke2_access_environment", cluster_name="local") }}'
  kubernetes.core.k8s:
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

creates the default cluster for you inside the Rancher manager.

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

## `epfl_si.rancher.rke2_access` Role

This role ensures that a suitable Kubeconfig file exists, and contains up-to-date credentials, so as to connect to a RKE2 cluster.

## `epfl_si.rancher.rke2_access_environment` Lookup Plugin

This lookup plugin configures your play's or role's `environment:`, so that Ansible will make use of the `rke2_cluster_token_store` that the `epfl_si.rancher.rke2_access` role creates.

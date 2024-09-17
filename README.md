# Ansible Collection — `epfl_si.rancher`

## `epfl_si.rancher.rancher_api_call` Module

This module lets your configuration-as-code exert the same API calls that your browser does; thereby allowing you to automate some operations typically done through the Rancher UI.

This module expects the `K8S_AUTH_KUBECONFIG` environment variable to be set, and to point to a suitable Kubeconfig file (e.g. one downloaded from the Rancher UI).

**⚠ This module always returns a “changed” (yellow) Ansible result.** It is up to you to short-circuit it (using a `when:` clause) if its post-condition is already met.

Here is an example task to install the [NFS subdir external provisioner](https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/) from its Helm chart, so as to provide NFS-based persistence:

```yaml
- epfl_si.rancher.rancher_api_call:
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

# `epfl_si.rancher.rke2_cluster` Ansible role

A curated list of features that come in handy for many clusters.

The following play will install all the bells and whistles in your cluster:
```yaml
- hosts: rke2_clusters
  gather_facts: no
  roles:
    - role: epfl_si.rancher.rke2_cluster
      vars:
        rancher_rke2_cluster_cnpg:
          enabled: true
        rancher_rke2_cluster_metallb:
          enabled: true
        rancher_rke2_cluster_longhorn:
          enabled: true
        rancher_rke2_cluster_nfs_subdir:
          server: mynas.example.com
          path: /export/formycluster
        rancher_rke2_cluster_prometheus:
          expose:
            hostname: "my-prometheus.example.com"
            tls_secret: my-secret   # Must be in "cattle-monitoring-system"
                                    # namespace, with keys `tls.key` and
                                    # `tls.crt`
            basic_auth: |
              test:$2y$10$Yq4KJO2JP.MdIhu76TFcAuYCD/TNXtein50dIhrjMjV2Wu8.vuIR2
          additional_alertmanager_configs_secret:
            name: external-alertmanager-configs
```

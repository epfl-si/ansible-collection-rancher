# Ansible Collection — `epfl_si.rancher`

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

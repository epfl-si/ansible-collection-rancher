DOCUMENTATION = '''
module: rancher_cluster
short_description: Look up the name(space) of a downstream cluster in the Rancher manager cluster
description:
- Retrieve details of a Rancher C(Cluster) object.

- In the Rancher upstream (“local”) Kubernetes cluster, each
  downstream (“managed”) cluster is represented as a non-namespaced
  `Cluster.management.cattle.io` Kubernetes object, as well as a
  companion namespace with the same name. The name for both is
  nondescript, like `c-m-t2gz7sxt`. The purpose of the
  `epfl_si.rancher.cluster_name` lookup is to find them by their
  “human” handle instead, like for instance the `spec.displayName` of
  the `Cluster` object (as is visible from the Rancher UI).

version_added: 0.10.0
'''


EXAMPLES = '''

# Create a project for the cluster named “MyCluster” in the Rancher UI
- name: "`project/my-app`"
  kubernetes.core.k8s:
    definition:
      apiVersion: management.cattle.io/v3
      kind: Project
      metadata:
        name: "my-app"
        namespace: >-
          {{ lookup("epfl_si.rancher.rancher_cluster",
                    display_name="MyCluster").metadata.name }}
        spec:
          displayName: "My App"
'''

from ansible_collections.epfl_si.rancher.plugins.lookup._rancher_lookup_base import RancherLookupBase

class LookupModule (RancherLookupBase):
    def run (self, terms, variables=None, display_name=None, **kwargs):
        self._init_rancher(variables, kwargs)

        [result] = [c for c in self._all_clusters
                    if c["metadata"].get("annotations").get("provisioning.cattle.io/management-cluster-display-name") == display_name]
        return [result]

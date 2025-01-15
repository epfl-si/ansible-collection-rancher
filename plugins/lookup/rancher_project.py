DOCUMENTATION = '''
module: rancher_project
short_description: Look up Rancher projects (groups of namespaces) by display name
description:
- This lookup plugin searches for C(Project.management.cattle.io) objects belonging to
  the current cluster (the one that the C(ansible_rancher_cluster_name) variable points to).


version_added: 0.7.0
'''

EXAMPLES = '''

# Make a namespace belong to the “System” project
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
'''

from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client

display = Display()

class LookupModule(LookupBase):
    def _get_custom_resource (self, client, kind, api_version):
        return client.resource(kind, api_version).get().items

    def _get_clusters (self, client):
        return self._get_custom_resource(client, 'cluster', 'provisioning.cattle.io/v1')

    def _get_projects (self, client):
        return self._get_custom_resource(client, 'project', 'management.cattle.io/v3')

    def run (self, terms, variables=None, display_name=None, **client_kwargs):
        client = get_api_client(**client_kwargs)

        this_cluster_name = variables["ansible_rancher_cluster_name"]
        [this_cluster_id] = (
            c.status.clusterName for c in self._get_clusters(client)
            if c.metadata.name == this_cluster_name)
        assert this_cluster_id is not None

        projects = [p for p in self._get_projects(client)
                    if p.spec.clusterName == this_cluster_id]

        if display_name is not None:
            projects = [p for p in projects
                        if p.spec.displayName == display_name]

        return projects

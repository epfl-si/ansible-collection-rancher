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

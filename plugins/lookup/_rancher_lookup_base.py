from ansible.plugins.lookup import LookupBase
from ansible_collections.epfl_si.k8s.plugins.lookup.k8s import LookupModule as K8sLookup

class RancherLookupBase (LookupBase):
    def _init_rancher (self, variables, kwargs):
        self.__variables = variables
        self.__kwargs = kwargs

    def __get_custom_resource (self, kind, api_version):
        return K8sLookup(self._loader, self._templar).run(
            [],
            variables=self.__variables,
            api_version=api_version, kind=kind,
            **self.__kwargs)

    @property
    def _all_clusters (self):
        return self.__get_custom_resource('cluster', 'provisioning.cattle.io/v1')

    @property
    def _all_projects (self):
        return self.__get_custom_resource('project', 'management.cattle.io/v3')

    @property
    def _rancher_cluster_id (self):
        [cluster_id] = (
            c["status"]["clusterName"] for c in self._all_clusters
            if c["metadata"]["name"] == self.__variables["ansible_rancher_cluster_name"])
        assert cluster_id is not None
        return cluster_id

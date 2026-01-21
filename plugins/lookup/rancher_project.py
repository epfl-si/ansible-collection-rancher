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

from ansible_collections.epfl_si.rancher.plugins.lookup._rancher_lookup_base import RancherLookupBase

class LookupModule (RancherLookupBase):
    def run (self, terms, variables=None, display_name=None, **kwargs):
        self._init_rancher(variables, kwargs)

        projects = [p for p in self._all_projects
                    if p["spec"]["clusterName"] == self._rancher_cluster_id]

        if display_name is not None:
            projects = [p for p in projects
                        if p["spec"]["displayName"] == display_name]

        return projects

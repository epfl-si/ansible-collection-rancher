from ansible.plugins.lookup import LookupBase

DOCUMENTATION = """
    author: EPFL ISAS-FSD <isas-fsd@groupes.epfl.ch>
    description:
      - Returns the set of environment variables to set, so that
        Ansible tasks wield the credentials set up by the
        `epfl_si.rancher.rancher_api_call` task called with the same
        value for the `rke2_cluster_token_store` variable.
"""

class LookupModule(LookupBase):
    def run(self, terms, variables=None):
        kubeconfig = self._templar.template(
            variables["rke2_cluster_token_store"])
        env = dict(
            KUBECONFIG=kubeconfig,
            K8S_AUTH_KUBECONFIG=kubeconfig)

        # For whatever reason, Ansible wants us to return an array.
        return [env]

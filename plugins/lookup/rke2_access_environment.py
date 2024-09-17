from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):
    def run(self, terms, variables=None):
        kubeconfig = self._templar.template(
            variables["rke2_cluster_token_store"])
        env = dict(
            KUBECONFIG=kubeconfig,
            K8S_AUTH_KUBECONFIG=kubeconfig)

        # For whatever reason, Ansible wants us to return an array.
        return [env]

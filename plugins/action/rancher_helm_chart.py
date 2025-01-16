from functools import cached_property

from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin

class RancherHelmChartAction (ActionBase, RancherActionMixin):
    """Install / uninstall one Helm chart through the Rancher manager."""
    # Emphasis on *one* Helm chart, even though the Steve API call
    # accepts an array for `charts`. The comment on line 784 of
    # rancher/pkg/catalogv2/helmop/operation.go suggests that this
    # multiplicity feature in the backend is either mostly or
    # exclusively intended to hide the fact that some apps come in two
    # different Helm charts (one with the CRD and one with the rest).
    # Also, as can be seen in the code that immediately follows said
    # comment, the `getInstallCommand` method massages the `charts`
    # array into a series of `helm` shell command lines; which makes
    # it unlikely that hoisting multiplicity to the Ansible level
    # would yield any additional benefits (such as performance or
    # transactional behavior), while on the other hand the costs are
    # pretty clear (i.e. it would make error processing a nightmare.)
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        self._init_rancher(ansible_api=ansible_api)

        self.chart_name = args["chart"]
        self.release_name = args.get("release", self.chart_name)
        self.source_repository = args.get("repository", self.chart_name)
        self.timeout = args.get("timeout", "600s")

        namespace = args["namespace"]
        if isinstance(namespace, str):
            namespace = { "name": namespace }
        self.install_namespace = namespace["name"]
        namespace_is_owned = namespace.get("owned", False)

        desired_state = args.get("state", "present")
        if desired_state == "present":
            if namespace_is_owned and not self._namespace_exists:
                self._do_create_namespace(is_system=namespace.get("system", False))
            if not self._helm_chart_is_installed:
                self._do_install_helm_chart(args["version"], args["values"])
        elif desired_state == "absent":
            if self._helm_chart_is_installed:
                self._do_uninstall_helm_chart()
            if namespace_is_owned and self._namespace_exists:
                self._do_delete_namespace()
        else:
            raise ValueError(f"Unsupported value for state: {desired_state}")

        return self.result

    def _do_install_helm_chart (self, helm_version, helm_values):
        self.change(
            "epfl_si.rancher.rancher_k8s_api_call",
            {
                "method": "POST",
                "uri": f"/v1/catalog.cattle.io.clusterrepos/{self.source_repository}?action=install",
                "body": {
                    "namespace": self.install_namespace,
                    "charts": [
                        # Just one chart, Vassili — See comment above.
                        {
                            "annotations": {
                                # Further Golang RTFS suggests that
                                # Steve doesn't actually support
                                # anything else than `"cluster"`
                                # there:
                                "catalog.cattle.io/ui-source-repo-type": "cluster",
                                "catalog.cattle.io/ui-source-repo": self.source_repository,
                            },
                            "chartName": self.chart_name,
                            "releaseName": self.release_name,
                            "version": helm_version,
                            "resetValues": False,
                            "values": helm_values,
                        }
                    ],
                    "wait": True,
                    "timeout": self.timeout
                }
            }
        )

    def _do_uninstall_helm_chart (self):
        self.change(
            "epfl_si.rancher.rancher_k8s_api_call",
            {
                "method": "POST",
                "uri": f"/v1/catalog.cattle.io.apps/{self.install_namespace}/{self.chart_name}?action=uninstall",
                "body": {}
            }
        )

    def _make_k8s_ns_definition (self, namespace_name):
        return {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace_name
            }
        }

    def _do_create_namespace (self, is_system):
        definition = self._make_k8s_ns_definition(self.install_namespace)

        if is_system:
            # https://github.com/rancher/dashboard/commit/28b9165b3446a41a85f382df68953e209888573a
            definition["metadata"]["annotations"] = {
                "management.cattle.io/system-namespace": "true"
            }

        self.change("kubernetes.core.k8s",
                    dict(definition=definition))

    def _do_delete_namespace (self):
        self.change("kubernetes.core.k8s",
                    dict(state="absent",
                         definition=self._make_k8s_ns_definition(self.install_namespace)))

    @property
    def _helm_chart_is_installed (self):
        return len(self.ansible_api.jinja.lookup(
            'kubernetes.core.k8s',
            api_version='catalog.cattle.io/v1',
            kind='App',
            resource_name=self.chart_name,
            namespace=self.install_namespace)) > 0

    @property
    def _namespace_exists (self):
        return len(self.ansible_api.jinja.lookup(
            'kubernetes.core.k8s',
            api_version='v1',
            kind='namespace',
            resource_name=self.install_namespace)) > 0

ActionModule = RancherHelmChartAction

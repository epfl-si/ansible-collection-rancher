from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.ansible_api import AnsibleActions
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin

class RancherNamespaceAction (ActionBase, RancherActionMixin):
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        self._init_rancher(ansible_api=ansible_api)
        self.name = args["name"]
        self.is_system = (args.get("is_system", False)
                          # Stay compatibile with earlier misfeature:
                          or namespace.get("system", False))

        self.project = args.get("project")

        desired_state = args.get("state", "present")
        if desired_state == "present":
            self._do_create_or_update()
        elif desired_state == "absent" and self._namespace_exists:
            self._do_delete_namespace()

        return self.result

    @property
    def _namespace_exists (self):
        return len(self.ansible_api.jinja.lookup(
            'epfl_si.k8s.k8s',
            api_version='v1',
            kind='namespace',
            resource_name=self.name)) > 0

    def _do_create_or_update (self):
        definition = self._k8s_bare_definition

        def annotate (key, val):
            definition["metadata"].setdefault("annotations", {})[key] = val

        if self.is_system:
            # https://github.com/rancher/dashboard/commit/28b9165b3446a41a85f382df68953e209888573a
            annotate("management.cattle.io/system-namespace", "true")

        if self.project:
            annotate("field.cattle.io/projectId", "%s:%s" %
                     (self.project["namespace"],
                      self.project["name"]))

        self.change("epfl_si.k8s.k8s",
                    dict(definition=definition))


    def _do_delete_namespace (self):
        self.change("epfl_si.k8s.k8s",
                    dict(state="absent",
                         definition=self._k8s_bare_definition))

    @property
    def _k8s_bare_definition (self):
        return {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": self.name
            }
        }

ActionModule = RancherNamespaceAction

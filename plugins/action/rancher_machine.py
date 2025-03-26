from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_api import RancherManagerAPIClient
from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin


class RancherMachineAction (ActionBase, RancherActionMixin):
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        super(RancherMachineAction, self).run(args, ansible_api)
        self._init_rancher(ansible_api=ansible_api)

        if args["state"] != "absent":
            raise NotImplementedError("Can only delete machines for now :-P")

        the_machine = self.rancher.get_machine_by_name(self.rancher_cluster_name, args["name"])

        if the_machine is None:
            return {}

        self.rancher.delete_machine(the_machine)

        return dict(changed=True)


ActionModule = RancherMachineAction

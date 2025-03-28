from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import AnsibleActions

from ansible_collections.epfl_si.rancher.plugins.module_utils.rancher_actions import RancherActionMixin


class RancherMachineAction (ActionBase, RancherActionMixin):
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        super(RancherMachineAction, self).run(args, ansible_api)
        self._init_rancher(ansible_api=ansible_api)

        if args["state"] != "absent":
            raise NotImplementedError("Can only delete machines for now :-P")

        the_machine = self.rancher_manager.get_cluster_by_name(self.rancher_cluster_name).get_machine_by_name(args["name"])

        if not the_machine.exists():
            return {}

        the_machine.delete()
        return dict(changed=True)


ActionModule = RancherMachineAction

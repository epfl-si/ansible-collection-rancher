class TestModule(object):
    """Tests on Rancher hostvars structs.

    Intended for use in Jinja templates, through one of the following forms:

    ```
    hostvars["foo"] is control_plane_node
    ```

    ```
    hostvars.values() | selectattr("control_plane_node")
    ```
    """

    def tests (self):
        return {
            'control_plane_node': self.is_control_plane_node
        }

    def is_control_plane_node (self, node):
        return node.get("rancher_rke2_is_controlplane")

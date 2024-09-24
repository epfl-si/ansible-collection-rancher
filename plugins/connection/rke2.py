import typing as t

from ansible import constants as C
from ansible.errors import AnsibleError

from ansible.plugins.connection import ConnectionBase
from ansible.plugins.connection.ssh import Connection as SSHConnection

DOCUMENTATION = '''
    name: rke2
    short_description: connect to an RKE2 cluster
'''

class _SSHConnectionNoMagic (SSHConnection):
    """Like ansible.plugins.connection.ssh.Connection, sans the “magic global variables” atavic nonsense."""
    def get_option (self, option, *args, **kwargs):
        """Overridden to short-circuit to None when `option` is `host`.

        Here is what happens if we don't: `get_option('host')`,
        references to which are found scattered throughout
        `ansible/plugins/connection/ssh.py`, takes priority over the
        “regular” variables like `ansible_host` and
        `ansible_ssh_host`. Also, it evaluates to
        `inventory_hostname`, the one from the `DOCUMENTATION` string
        at the top of that same file. No kidding! Editing it there,
        changes the value here, but only when using an
        `ansible.plugins.connection.ssh.Connection` instance as a
        has-a object — For some unfathomable reason, which I tried and
        failed to elucidate during a whole day of debugging, the
        behavior is different, albeit still buggy, when using
        `ansible.plugins.connection.ssh.Connection` class directly (or
        in a trivial-subclass is-a relationship).

        Caller (e.g. `SSHConnection().exec_command()` will have to use
        the regular, dynamic value from variables (e.g.
        `self._play_context.remote_addr`) instead of this atavic
        global configuration cascading mechanism which, judging by the
        evidence presented above, was forsaken by its authors.

        """
        if option == 'host':
            return None

        return super(SSHConnection, self).get_option(option, *args, **kwargs)

    # The key to be used when reading `C.config` (which we still need
    # to do for other values of `option` passed to `get_option`). By
    # default, this value is computed (by a property) from the class
    # name — Talk about good OO practices 🤦
    plugin_type = "connection"


class Connection(ConnectionBase):
    """WIP - Implemented 100% by delegating to `ansible.plugins.connection.ssh`."""
    # Not sure what this is for — But the plugin loader won't pick
    # up the class if we don't override this (on account of it being
    # abstract in the parent class):
    transport = 'rke2'

    def __init__ (self, *args: t.Any, **kwargs: t.Any) -> None:
        super(Connection, self).__init__(*args, **kwargs)
        self._ssh = _SSHConnectionNoMagic(*args, **kwargs)

    def _connect (self) -> ConnectionBase:
        return self

    def close(self) -> None:
        self._ssh.close()

    def exec_command (self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        return self._ssh.exec_command(cmd, in_data, sudoable)

    def fetch_file(self, in_path: str, out_path: str) -> tuple[int, bytes, bytes]:
        return self._ssh.fetch_file(in_path, out_path)

    def put_file (self, in_path: str, out_path: str) -> tuple[int, bytes, bytes]:
        return self._ssh.put_file(in_path, out_path)

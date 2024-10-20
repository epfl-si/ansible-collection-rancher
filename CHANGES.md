# Version 0.5.0: major bugfix and API change release

- `epfl_si.rancher.rke2` connection plugin is gone
- Fix bugs and get rid of dead code

# Version 0.4.0: major feature release

- `rancher_login` can now log in to multiple clusters.
- Fix a Python interpreter mis-discovery bug (whence the interpreter discovered over ssh would “leak” over to normal connections)

# Version 0.3.1: major bugfix release

- Turn off Ansible's Python interpreter discovery when running tasks on the Rancher back-end machine.

# Version 0.3.0: major feature release

- `rancher_registration` now works before initializing the cluster (DUH!). As a consequence, it now requires `rancher_manager_url` and `cluster_name` parameters.

# Version 0.2.1: major feature release

💡 Upload of version 0.2.0 to Galaxy was botched for some reason.

- New `rancher_registration` task

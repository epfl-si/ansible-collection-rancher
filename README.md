# gitlab-ops

The DevOps toolkit that powers https://gitlab.epfl.ch/

This is also an exercise in applying our tools (Keybase, Rancher, [Ansible suitcase](https://github.com/epfl-si/ansible.suitcase)) to the single most complex infrastructure problem [we](https://search.epfl.ch/?filter=unit&q=ISAS-FSD) have: turning 5 (manually provisioned) VMs into a working GitLab cluster, from soup to nuts. Where “soup” means creating the cluster in the Rancher manager, and “nuts” means cycling individual VMs out of and back into the cluster for the occasional `apt dist-upgrade`.

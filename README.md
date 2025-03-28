# Ansible Collection — `epfl_si.rancher`

This collection contains roles, actions, modules and lookup plugins
that make it easy to manage Rancher RKE2 clusters.

Support is provided for the Rancher REST APIs (both of them: “Steve”
and ”Norman”), their authentication schemes, as well “Ansiblified”
operations for some Rancher dashboard actions such as:

- Creating RKE2 clusters
- Registering nodes into them
- Unregistering nodes, and uninstalling RKE2 from them
- Logging into clusters (like the “Download Kubeconfig” operation in the Rancher dashboard)
- Installing Helm packages (like with “Apps” → “Charts”)

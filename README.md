# Ansible Collection — `epfl_si.rancher`

This collection contains roles, actions, modules and lookup plugins
that make it easy to manage Rancher RKE2 clusters.

**This collection is of no help, unless your Rancher server and
cluster API servers are reachable directly over HTTP/S from the
operator's workstation.** Unlike e.g. `kubernetes.core.k8s`, this
collection doesn't believe in moving Python code around over some
remote shell session (ssh or otherwise) to execute it remotely.

Support is provided for the Rancher REST APIs (both of them: “Steve”
and ”Norman”), their authentication schemes, as well “Ansiblified”
operations for some Rancher dashboard actions such as:

- Creating RKE2 clusters
- Registering nodes into them
- Unregistering nodes, and uninstalling RKE2 from them
- Logging into clusters (like the “Download Kubeconfig” operation in the Rancher dashboard)
- Installing Helm packages (like with “Apps” → “Charts”)

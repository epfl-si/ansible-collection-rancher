"""Support for automation tasks (Ansible modules) against the (“old”) Rancher API

As documented at
https://ranchermanager.docs.rancher.com/v2.9/api/v3-rancher-api-guide
the rancher API server (which is also the back-end of the Rancher Web
UI) provides two main entry points that are amenable to automation,
affectionately called (I'm not making this up) Steve and Norman.

- Steve is the “new” API, introduced during the Rancher 2.5 lifecycle;
  it is Kubernetes-compatible, in the sense that Steve responds to the
  usual calls made by `kubectl`, as well as all the programming
  language-specific Kubernetes API frameworks. Steve basically
  consists of a reverse proxy written in Go that sits in front of
  multiple clusters' API servers, and federates them under one host
  name and bearer token store. (There are also some optimisations
  thrown in for browser-based clients, such as pagination, which are
  besides the point here.)

- The so-called “old” API, code-named Norman, is just a “traditional”
  Web app back-end also written in Go, which runs in the same process
  as Steve. It was tailor-made for the needs of the Rancher Web UI
  front-end. It is still used for Rancher-specific operations that do
  not map cleanly to the new way of Kubernetes. For instance,
  installing a Helm chart onto one of the managed clusters is done by
  performing an “old-school” HTTP POST to a URL that starts in `/v1/`
  and ends in `?action=install`; to which the Rancher back-end
  responds by performing the required operations itself. The
  “Kubernetes-style” alternative, which would arguably be quite
  clunkier, would consist of the Web front-end having to create a
  bunch of Kubernetes objects with HTTP PUTs, with the desired
  operations declaratively laid out in these objects' `spec:`; and
  then wait for some out-of-process operator to update their
  `status:`.

It so happens that the official Kubernetes client API for Python is
feature-complete enough to implement both Steve and Norman calls
out-of-the-box; thanks in particular to the fact that both accept the
same bearer tokens for authentication.

"""

from functools import cached_property
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client

class RancherAPIError (Exception):
    pass

class RancherAPIClient:
    """A thin wrapper around Ansible's Kubernetes API."""
    def __init__ (self, module):
        self.client = get_api_client(module=module)

    @property
    def k8s_client (self):
        return self.client.client.client  # Ansible was there 🤷

    def call_k8s_api (self, method, uri, body=None):
        (data, status, headers) = self.k8s_client.call_api(
            uri, method,   # Google was there 🤷
            auth_settings=['BearerToken'],
            response_type="object",
            body=body)

        if status not in (200, 201):
            raise RancherAPIError(data)

        return data

    call_steve = call_k8s_api

    def download_kubeconfig (self):
        return self.request(
            "GET",
            "?action=generateKubeconfig")

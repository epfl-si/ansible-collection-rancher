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
import os
from urllib.parse import urlparse

import kubernetes   # Because Ansible code has this bizarre `except ImportError` clause on it, which we really don't want to investigate (again)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client

class RancherAPIError (Exception):
    pass

class RancherAPIClient:
    """A thin wrapper around Ansible's Kubernetes API."""
    def __init__ (self,
                  module=None,
                  kubeconfig=None, context=None,
                  api_key=None, base_url=None, rancher_api_cluster_id=None, ca_cert=None, validate_certs=True):
        if module is not None:
            # Ansible-style API: pass in an AnsibleModule instance
            client = get_api_client(module=module)
        elif kubeconfig is not None:
            client = get_api_client(kubeconfig=kubeconfig, context=context)
        elif (api_key is not None) and (base_url is not None) and (rancher_api_cluster_id is not None):
            # The `kubernetes` Python client insists to test its
            # connection against (you guessed it) a
            # Kubernetes-compatible API endpoint (even if we end up
            # only making Norman calls):
            server_uri = '%s/k8s/clusters/%s' % (base_url, rancher_api_cluster_id)
            client = get_api_client(api_key=api_key, host=server_uri,
                                    ca_cert=ca_cert, validate_certs=validate_certs)
        else:
            raise ValueError("Unable to create API client from constructor arguments")

        self.client = client

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

    def call_rancher_v3_api (self, method, query_params, body=None):
        (data, status, headers) = self.k8s_client.call_api(
            '/v3/clusters/%s' % self.rancher_api_cluster_id,
            method,
            auth_settings=['BearerToken'],
            response_type="object",
            body=body,
            query_params=query_params,
            # Yeah, private parameter. No, I won't duplicate the whole
            # Python kubernetes API's token management code, just to
            # avoid using the private parameter. Sue me.
            _host=self.rancher_root_url)

        if status not in (200, 201):
            raise RancherAPIError(data)

        return data

    call_norman = call_rancher_v3_api

    @property
    def k8s_api_url (self):
        return self.k8s_client.configuration.host

    @property
    def rancher_api_cluster_id (self):
        uri_path = urlparse(self.k8s_api_url).path
        return os.path.basename(uri_path)

    @property
    def rancher_root_url (self):
        parsed = urlparse(self.k8s_api_url)
        return '%s://%s/' % (parsed.scheme, parsed.netloc)

    def download_kubeconfig (self):
        return self.call_rancher_v3_api("POST",
                                        query_params=dict(action='generateKubeconfig'))['config']

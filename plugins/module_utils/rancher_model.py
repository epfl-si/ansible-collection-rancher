"""Model classes and API stubs for the Rancher API (“Norman” and “Steve”).

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
"""

from functools import cached_property

from requests import request

class RancherManager:
    """Model class for the Rancher manager.

    An instance represents a connection to the “main” Rancher manager backend."""
    def __init__ (self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.api = RancherAPI(base_url, api_key)

    def get_cluster_by_name (self, name):
        return RancherManagedCluster.by_name(self, name)


class RancherAPI:
    """An object-oriented interface to Rancher's “Steve” and “Norman" APIs.

    An instance holds the address and credentials to one particular
    Rancher manager back-end. The same set of credentials can be used
    for both the “Steve” API of the Rancher manager cluster (the one
    named `local` in the GUI), under URLs typically starting with
    `/v1/`; and the “Norman” API where URLs typically start with
    `/v3/`.
    """
    def __init__ (self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    def call (self, method, uri, body=None, query_params=None):
        opt_args = {}
        if body:
            opt_args['json'] = body
        if query_params:
            opt_args['params'] = query_params

        response = request(method,
                           self.base_url + uri,
                           headers={
                               'Authorization': 'Bearer %s' % self.api_key
                           },
                           **opt_args)

        if response.status_code in (200, 201):
            return response.json()
        else:
            raise self.Error(response.text)

    class Error (Exception):
        pass


class RancherManagedCluster:
    """Model for one of the clusters that Rancher manages (including itself)."""

    @classmethod
    def by_name (cls, manager, cluster_name):
        """Find and return a cluster by its display name.

        If no such cluster exists, return None.

        """

        matched = [c for c in RancherManagedClusterAPI.all(manager.api)
                   if c.name == cluster_name]
        if len(matched) == 0:
            return None
        elif len(matched) == 1:
            return cls(manager, matched[0])
        else:
            raise ValueError(
                f'GET {RancherManagedClusterAPI.base_uri}: '
                f'{len(matched)} cluster(s) found with name {cluster_name}; expected at most one.')

    def __init__ (self, manager, api_object):
        self.manager = manager
        self.api_object = api_object

    @property
    def id (self):
        return self.api_object.id

    def download_kubeconfig (self):
        """Perform the same API call as the “Download Kubeconfig” button in the Rancher UI.

        Return a parsed Kubernetes `kubeconfig` struct.

        """
        return self.api_object.download_kubeconfig()

    @property
    def registration_tokens (self):
        api = self.manager.api
        cluster_id = self.id

        class RegistrationTokens:
            def first (self):
                """Raises IndexError if there are currently no valid tokens."""
                my_toks = [tok for tok in RancherClusterRegistrationTokensAPI.all(api)
                           if tok.cluster_id == cluster_id]
                return my_toks[0].data

            def make_more (self):
                RancherClusterRegistrationTokensAPI.renew(api, cluster_id)

        return RegistrationTokens()

    def get_machine_by_name (self, machine_name):
        return RancherManagedClusterMachine(self, machine_name)


class _APIBase:
    """Base class for API objects whose instances are enumerated with HTTP GET."""
    @classmethod
    def all (cls, api):
        return [cls(api, data)
                for data in api.call('GET', cls.base_uri)['data']]

    def __init__ (self, api, data):
        self.api = api
        self.data = data


class RancherManagedClusterAPI (_APIBase):
    """The “Norman” API of clusters managed by Rancher.

    Note that the “master” cluster on which the Rancher manager itself
    runs is also typically an instance called `local`.
    """

    base_uri = '/v3/clusters'

    @property
    def name (self):
        return self.data['name']

    @property
    def id (self):
        return self.data['id']

    @property
    def uri (self):
        return f'{self.base_uri}/{self.id}'

    def download_kubeconfig (self):
        """Perform the same API call as the “Download Kubeconfig” button in the Rancher UI.

        Return a parsed Kubernetes `kubeconfig` struct.

        """
        return self.api.call(
            'POST', self.uri,
            query_params=dict(action='generateKubeconfig'))['config']


class RancherClusterRegistrationTokensAPI (_APIBase):
    """The “Norman” API for registering more nodes into clusters."""
 
    base_uri = '/v3/clusterregistrationtokens'

    @property
    def cluster_id (self):
        return self.data['clusterId']

    @classmethod
    def renew (cls, api, cluster_id):
        api.call(
            'POST',
            cls.base_uri,
            body={"type":"clusterregistrationtoken",
                  "clusterId": cluster_id})
        

class RancherManagedClusterMachine:
    """Model for a machine that Rancher manages."""

    def __init__ (self, cluster, machine_name):
        self.cluster = cluster
        self.name = machine_name

    @cached_property
    def _kubernetes_sig_cluster_api (self):
        matching = [k for k in KubernetesSigClusterMachineAPI.all(self.cluster.manager.api)
                    if self.name == k.node_name]

        if len(matching) == 0:
            return None
        elif len(matching) == 1:
            return matching[0]
        else:
            raise ValueError(f'GET {KubernetesSigClusterMachineAPI.base_uri}:'
                             f' got {len(matching)} results with name {self.name}, expected at most one.')

    def exists (self):
        return self._kubernetes_sig_cluster_api is not None

    def delete (self):
        self._kubernetes_sig_cluster_api.delete()


class KubernetesSigClusterMachineAPI (_APIBase):
    """The “Steve” API of `machine.cluster.x-k8s.io` objects in Rancher.

    These are ordinary namespaced Kubernetes objects, wherein each
    managed cluster is represented by a namespace in the Rancher
    manager's API server, and the machines are objects of `Kind:
    machine` in that namespace.

    """
    base_uri = '/v1/cluster.x-k8s.io.machines'

    @property
    def node_name (self):
        return self.data.get("status", {}).get("nodeRef", {}).get("name")

    @property
    def rest_url (self):
        metadata = self.data["metadata"]
        return f'{self.base_uri}/{metadata["namespace"]}/{metadata["name"]}'

    def delete (self):
        self.api.call('DELETE', self.rest_url)

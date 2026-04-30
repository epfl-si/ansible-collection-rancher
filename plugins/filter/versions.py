"""Look up latest versions of RKE2 assets."""

import ssl
import http.client
from requests.utils import DEFAULT_CA_BUNDLE_PATH

from urllib.parse import urlparse


class HTTPStatusError (Exception):
    pass


def get_location_header (url):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(DEFAULT_CA_BUNDLE_PATH)

    parsed = urlparse(url)
    port = parsed.port or 443
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    conn = http.client.HTTPSConnection(
        parsed.hostname,
        port=port,
        context=context)

    conn.request("GET", path)
    response = conn.getresponse()

    status = response.status
    if status < 300 or status > 399:
        raise HTTPStatusError("Unexpected status %d at %s" % (status, url))

    return response.getheader("Location")

class FilterModule(object):
    def filters(self):
        return {
            'get_rke2_current_version': self.get_rke2_current_version
        }

    def get_rke2_current_version(self, channel_url):
        """Obtain the current (latest) version in an RKE2 release channel."""
        location = get_location_header(channel_url)
        return location.split("/")[-1]

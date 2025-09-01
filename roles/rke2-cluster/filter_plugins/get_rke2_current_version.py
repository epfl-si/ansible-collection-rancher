"""Obtain the current (latest) version in an RKE2 release channel."""

from urllib.request import urlopen

class FilterModule(object):
    def filters(self):
        return {
            'get_rke2_current_version': self.get_rke2_current_version
        }

    def get_rke2_current_version(self, channel_url):
        with urlopen(channel_url) as response:
            # You really want to *not* follow URLs. But for that, you
            # would need a HorseFactory or something.
            return response.geturl().split("/")[-1]

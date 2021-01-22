"""Ad-hoc helpers that are hard to write in pure Jinja."""

class FilterModule(object):
    def filters(self):
        return {
            'keys': self.keys,
            'as_volume_mounts': self.as_volume_mounts
        }
    def as_volume_mounts(self, filenames, secret_ref_name, mount_at):
        return [dict(name=secret_ref_name,
                     mountPath="%s/%s" % (mount_at, filename),
                     subPath=filename)
                for filename in filenames]
    def keys(self, d):
        return d.keys()

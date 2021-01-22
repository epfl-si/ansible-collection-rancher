"""Ad-hoc helpers that are hard or impossible to write in pure Jinja."""

class FilterModule(object):
    def filters(self):
        return {
            'as_volume_mounts': as_volume_mounts
            'keys': keys,
        }

def as_volume_mounts(filenames, secret_ref_name, mount_at):
    return [dict(name=secret_ref_name,
                 mountPath="%s/%s" % (mount_at, filename),
                 subPath=filename)
            for filename in filenames]

def keys(d):
    return d.keys()

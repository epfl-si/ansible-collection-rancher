"""Ad-hoc helpers that are hard or impossible to write in pure Jinja."""

class FilterModule(object):
    def filters(self):
        return {
            'keys': keys,
            'as_volume_mounts': as_volume_mounts,
            'merge_dict_deep': merge_dict_deep
        }

def as_volume_mounts(filenames, secret_ref_name, mount_at):
    return [dict(name=secret_ref_name,
                 mountPath="%s/%s" % (mount_at, filename),
                 subPath=filename)
            for filename in filenames]

def keys(d):
    return d.keys()

def merge_dict_deep(d1, d2):
    retval = dict()
    for k in set(d1.keys()).union(d2.keys()):
        if k not in d1:
            retval[k] = d2[k]
        elif k not in d2:
            retval[k] = d1[k]
        elif isinstance(d1[k], dict):
            if isinstance(d2[k], dict):
                retval[k] = merge_dict_deep(d1[k], d2[k])
            else:
                raise ValueError("Type mismatch: %s" % k)
        else:
            raise ValueError("Duplicate key: %s" % k)
    return retval

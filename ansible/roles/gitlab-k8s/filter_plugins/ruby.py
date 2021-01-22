"""Map Python data structures to Ruby."""

import re

class FilterModule(object):
    def filters(self):
        return {
            'to_omnibus': to_omnibus
        }

def to_omnibus(d, prefix):
    lines = _to_omnibus_lines(d, prefix)
    return "".join("%s\n" % line for line in lines)

def _to_omnibus_lines(d, prefix):
    retval = []
    for k in d.keys():
        v = d[k]
        if isinstance(v, dict):
            newprefix = "%s[%s]" % (prefix, _quote(k))
            retval.append("%s ||= {}" % newprefix)
            retval.extend(_to_omnibus_lines(d, prefix))
        elif v is None:
            retval.append("%s[%s] = nil" % (prefix, _quote(k)))
        elif isinstance(v, bool):
            retval.append("%s[%s] = %s" % (prefix, _quote(k),
                                           "true" if v else "false"))
        elif isinstance(v, int):
            retval.append("%s[%s] = %d" % (prefix, _quote(k), v))
        else:
            retval.append("%s[%s] = %s" % (prefix, _quote(k), _quote(v)))
    return retval

def _quote(s):
    return '"%s"' % re.sub(r'([\\"])', r'\\\1', s)

def pry_out_bytes(soi_disant_unicode_string_a_la_Python):
    """YA RLY.

    https://stackoverflow.com/a/27367173/435004
    """
    return soi_disant_unicode_string_a_la_Python.encode(
        'utf-8', 'surrogateescape')

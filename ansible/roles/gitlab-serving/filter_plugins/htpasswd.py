# Create the right-hand side of an htpasswd line.
from bcrypt import gensalt, hashpw, kdf
from base64 import b64encode

KDF_COST_FACTOR = 50

def b(s):
    return bytes(s, 'utf-8')

def s(b):
    return str(b, 'utf-8')

def htpasswd(passwd, salt_seed = None):
    salt = gensalt()
    if salt_seed is not None:

        salt_pieces = s(salt).split('$')

        # https://github.com/ansible/ansible/issues/36129#issuecomment-658832705
        salt_last_bits = kdf(b(passwd), b(salt_seed),
                             18,   # Resulting in a 24-character long string
                             KDF_COST_FACTOR)
        salt_pieces[3] = s(b64encode(salt_last_bits, b'./')[:21]
                           + b'.')  # Losing 2 bits of entropy, so sue me

        salt = b('$'.join(salt_pieces))

    return s(hashpw(b(passwd), salt))

class FilterModule(object):
    def filters(self):
        return {'htpasswd': htpasswd }

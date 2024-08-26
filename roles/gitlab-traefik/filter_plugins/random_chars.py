# Create the right-hand side of an htpasswd line.
from bcrypt import gensalt, hashpw, kdf
from base64 import b64encode

KDF_COST_FACTOR = 50

def b(s):
    return bytes(s, 'utf-8')

def s(b):
    return str(b, 'utf-8')

def bcrypt_salt(seed):
    # https://github.com/ansible/ansible/issues/36129#issuecomment-658832705
    salt_bits = kdf(b(seed), b(seed),
                         18,  # Will too long enough after base64-encoding
                         KDF_COST_FACTOR)

    return s(b64encode(salt_bits, b'./')[:21]
             + b'.')  # Losing 2 bits of entropy, so sue me

class FilterModule(object):
    def filters(self):
        return {'bcrypt_salt': bcrypt_salt }

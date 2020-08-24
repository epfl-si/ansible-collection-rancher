# Transform clear text list of username:password into corresponding entry
# suitable for traefik traefik.frontend.auth.basic label
# Keeps the salt in a tmp file so that runs are more or less idempotents.

from bcrypt import gensalt, hashpw

# Oops... just found that there is a standard hash filter in ansible
#         well in the end it does not simply much   :p
# from ansible.plugins.filter.core import get_encrypted_password
# from ansible.utils.encrypt import random_salt

def htpasswd(passwd):
  salt = gensalt()

  ep = hashpw(bytes(passwd, 'utf-8'), salt)
  ep = str(ep, 'utf-8')
  return ep

class FilterModule(object):
  def filters(self):
    return {'htpasswd': htpasswd }

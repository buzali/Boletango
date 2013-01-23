from platform import node

from settings_common import *

if node() == DEVELOPMENT_HOST:
    from settings_dev import *
elif node() == PRODUCTION_HOST:
    from settings_prod import *
else:
    raise Exception("Cannot determine execution mode for host '%s'.  Please check DEVELOPMENT_HOST and PRODUCTION_HOST in settings_local.py." % node())

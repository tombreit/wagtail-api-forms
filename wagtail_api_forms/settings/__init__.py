"""
Choosing the settings which fit to our current environment.
"""

from .base import env

if env.str("SETTINGS_MODE") == 'dev':
    from .dev import *  # noqa: F401, F403   # pylint: disable=unused-import
else:
    from .production import *  # noqa: F401, F403   # pylint: disable=unused-import

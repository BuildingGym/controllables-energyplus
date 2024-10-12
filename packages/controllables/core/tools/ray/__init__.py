r"""
TODO deprecate
"""

raise DeprecationWarning('!!!! this module has been deprecated!!!! use `controllables.core.tools.rllib` instead!!!')


# TODO deps
from .env import (
    ExternalMultiAgentEnv,
    ExternalEnv,
)


__all__ = [
    'ExternalMultiAgentEnv',
    'ExternalEnv',
]

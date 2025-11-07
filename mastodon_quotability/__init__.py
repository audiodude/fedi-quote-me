"""
Mastodon Quotability Manager
A library for managing quote post settings on Mastodon servers.
"""

from .auth import MastodonAuthManager
from .api import MastodonQuotabilityAPI

__version__ = "0.1.0"
__all__ = ["MastodonAuthManager", "MastodonQuotabilityAPI"]

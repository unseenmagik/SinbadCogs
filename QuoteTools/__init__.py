from .quotetools import QuoteTools
import sys


def setup(bot):
    if sys.version_info >= (3, 6, 2):
        bot.add_cog(QuoteTools())
    else:
        raise RuntimeError("This package requires python version >= 3.6.2")

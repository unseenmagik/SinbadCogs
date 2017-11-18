from discord.ext import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.i18n import CogI18n

_ = CogI18n("RoomTools", __file__)


class RoomTools:
    """
    cog for room creation
    """

    def __init__(self, bot):
        self.bot = bot
        self.ar_active = True  # todo: make configurable
        self.tmpc_active = False

    @commands.group(name="roomtools")
    async def roomtoolsgroup(self, ctx):
        help_doc = _("Various commands for user generated rooms")  # noqa: F841
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

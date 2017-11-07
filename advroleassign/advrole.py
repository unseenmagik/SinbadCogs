import discord
import itertools
from datetime import datetime, timedelta
from discord.ext import commands
from redbot.core import Config
from redbot.core.utils import chat_formatting as cf


TICK = "\N{WHITE HEAVY CHECK MARK}"


class AdvRoleError(Exception):
    pass


class SanityError(AdvRoleError):
    pass


class AdvRoleAssign:
    """
    Cog for allowing conditional self roles
    Supports requiring a specific role to request roles,
    Roles which are mutually exclusive,
    As well as different requirements for each role
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            identifier=2054884282, force_registration=True)
        self.config.register_channel(silent=False, is_log=False,
                                     is_verification=False)
        self.config.register_guild(
            required_role=None, strict_require=False,
            lockout_time=60, active=False, enforce_listener=False,
            verification_mode="react")
        self.config.register_member(lockouts={})
        self.config.register_role(
            assignable=False, requires=[],
            exclusive_to=[], lockout_override=None,
            sticky=False, is_verification=False)

    async def set_logging_channel(self, ctx, channel: discord.TextChannel):
        pass

    async def clear_lockouts(self, ctx):
        pass

    async def mock_available_for(self, ctx, user: discord.Member):
        pass

    async def toggle_listener(self, ctx):
        pass

    async def toggle_active(self, ctx):
        pass

    async def set_lockout(self, ctx):
        pass

    async def role_config(self, ctx, role: discord.Role):
        pass

    async def fully_interactive_configuration(self, ctx):
        pass

    async def list_available_roles(self, ctx):
        pass

    async def join_role(self, ctx, *, role: discord.Role):
        pass

    async def get_config_info(self, ctx):
        pass

    async def get_conflicting_roles(
            self, member: discord.Member, role: discord.Role):
        pass

    async def get_valid_roles(self, member: discord.Member):
        pass

    async def on_member_update(self, member_before, member_after):
        pass

    async def on_member_join(self, member):
        pass

    async def on_raw_reaction_add(self, member):
        pass


def unique(a):
    indices = sorted(range(len(a)), key=a.__getitem__)
    indices = set(next(it) for k, it in
                  itertools.groupby(indices, key=a.__getitem__))
    return [x for i, x in enumerate(a) if i in indices]

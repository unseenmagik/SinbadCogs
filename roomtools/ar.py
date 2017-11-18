import asyncio
from datetime import datetime, timedelta
from discord.ext import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.i18n import CogI18n

_ = CogI18n("AutoRooms", __file__)


class AutoRooms:
    # I'd put a help doc here, but this class should never be directly exposed

    def __init__(self, bot):
        self.bot = bot
        # Ensure we cleanup any mess left during a bot connection loss
        self.bot.loop.create_task(self.cleanup())
        self.auto_room_indicator = '⌛'
        self.game_room_indicator = '🎮'
        self.config = Config.get_conf(
            self, identifier=2081794476, force_registration=True)
        self.config.register_guild(read_instructions=False)
        self.config.register_guild(is_active=False)
        self.config.register_channel(is_temp=False)

    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    @checks.admin_or_permissions(manage_channels=True)
    @commands.command(
        name='autoroomtoggle', parent=roomtoolcmdgroup)  # noqa: F821
    async def aatoggle(self, ctx):
        help_doc = _("Toggle autoroom status for the guild")  # noqa: F841
        has_read = await self.config.guild(ctx.guild).read_instructions()
        if not has_read:
            await ctx.send(
                _('Warning: This cog allows users to create temporary voice '
                  'channels without requiring additional permissions.'
                  '\nThe names of these channels will either be based on their'
                  ' display name, or the game they are playing (according to '
                  'Discord). Channels are created in the same category '
                  'and with the same permissions as their origin.'
                  '\n\nFor more details on how to set this up, use '
                  '{}help AutoRooms'
                  '\n\nIf this is acceptable, reissue the command.'
                  'This warning will not be shown again').format(ctx.prefix))
            await self.config.guild(ctx.guild).read_instructions.set(True)
            return

        current_active = await self.config.guild(ctx.guild).is_active()
        await self.config.guild(ctx.guild).is_active.set(not current_active)

        if current_active:
            await self.cleanup(ctx.guild, True)
            await ctx.send(_('Autorooms have been disabled.'))
        else:
            await ctx.send(_('Autorooms have been enabled.'))

    async def on_voice_state_update(self, member, v_before, v_after):
        if v_before.channel == v_after.channel:
            return

        if v_before.channel is not None:
            channel = v_before.channel
            is_temp = await self.config.channel(channel).is_temp()
            if is_temp:
                await self.process_channel(channel)

        if v_after.channel is not None:
            is_active = await self.config.guild(
                v_after.channel.guild).is_active()
            if not is_active:
                return
            try:  # I could try/except each failure case
                if v_after.channel.name.startswith(self.auto_room_indicator):
                    await self._make_auto_room(member, v_after.channel)
                if v_after.channel.name.startswith(self.game_room_indicator):
                    await self._make_game_room(member, v_after.channel,
                                               v_before.channel)
            except Exception:   # but I don't care enough
                pass

    async def _make_auto_room(self, member, chan):

        category = chan.category

        editargs = {'bitrate': chan.bitrate, 'user_limit': chan.user_limit}
        overwrites = {}
        for perm in chan.overwrites:
            overwrites.update({perm[0]: perm[1]})

        chan_name = f'{member.display_name}\'s room'
        z = await chan.guild.create_voice_channel(
            chan_name, category=category, overwrites=overwrites)
        if z:
            await self.config.channel(z).is_temp.set(True)
        await asyncio.sleep(0.5)
        await z.edit(**editargs)
        await member.move_to(z, reason="autoroom")

    async def _make_game_room(self, member, chan, old_chan):

        category = chan.category

        editargs = {'bitrate': chan.bitrate, 'user_limit': chan.user_limit}
        overwrites = {}
        for perm in chan.overwrites:
            overwrites.update({perm[0]: perm[1]})

        if member.game is None:
            chan_name = f'{member.display_name} Has no game'
        else:
            chan_name = f'{member.game.name}'

        z = await chan.guild.create_voice_channel(
            chan_name, category=category, overwrites=overwrites)
        if z:
            await self.config.channel(z).is_temp.set(True)
        await asyncio.sleep(0.5)
        await z.edit(**editargs)
        await member.move_to(z, reason="autoroom")

    async def process_channel(self, channel, force=False):
        is_temp = await self.config.channel(channel).is_temp()
        if not is_temp:
            return
        if channel.created_at + timedelta(seconds=30) > datetime.utcnow():
            return
        if len(channel.members) == 0 or force:
            try:
                await channel.delete()
            except Exception:
                pass

    async def cleanup(self, where=None, force=False):
        if where:
            locations = [where]
        else:
            locations = self.bot.guilds
        for guild in locations:
            guild_active = await self.config.guild(guild).is_active()
            if not guild_active:
                continue
            for vc in guild.voice_channels:
                await self.process_channel(vc, force)

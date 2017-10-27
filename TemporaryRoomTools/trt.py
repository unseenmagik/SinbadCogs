import discord
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands
from redbot.core import Config


class RoomTools:
    """
    cog for managing various temporary channel types
    """
    def __init__(self, bot):
        self.bot = bot
        self.everyone_perms = discord.PermissionOverwrite(read_messages=False)
        self.joined_perms = discord.PermissionOverwrite(read_messages=True,
                                                        send_messages=True)
        self.owner_perms = discord.PermissionOverwrite(read_messages=True,
                                                       send_messages=True,
                                                       manage_channels=True,
                                                       manage_roles=True)
        self.auto_room_indicator = '⌛'
        self.game_room_indicator = '🎮'
        self.clone_indicator = '♻'
        self.temp_icon = '⏱'
        self.cleanup_task = self.bot.loop.create_task(self.periodic_cleanup())
        self.config = Config.get_conf(
            self, identifier=2081794477, force_registration=True)
        self.config.register_channel(is_temp=False)

    def get_guild_temp_category(self, guild: discord.Guild):
        for category in guild.categories:
            if category.name.lower().replace(' ', '') == 'temporarychannels':
                return category
        else:
            return None

    @commands.command(name='newtempchannel', aliases=['tmpc'])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def make_temp_channel(self, ctx, *, name):
        """
        make a new temp channel
        """
        cat = self.get_guild_temp_category(ctx.guild)
        if cat is None:
            return await ctx.send('This guild does not have a '
                                  'temporary channels category')

        x = await ctx.guild.create_voice_channel(f'{self.temp_icon} {name}')
        await asyncio.sleep(0.5)
        await x.edit(category=cat, sync_permissions=True)
        await x.set_permissions(ctx.author,
                                manage_channels=True, manage_roles=True)
        await self.config.channel(x).is_temp.set(True)

    @commands.command(name="tmptxt")
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def make_temp_text(self, ctx, *, name):
        """
        make a new temporary text channel
        """
        cat = self.get_guild_temp_category(ctx.guild)
        if cat is None:
            return await ctx.send('This guild does not have a '
                                  'temporary channels category')
        x = await ctx.guild.create_text_channel(name,
                                                (ctx.guild.default_role,
                                                 self.everyone_perms),
                                                (ctx.author, self.owner_perms),
                                                (ctx.guild.me,
                                                 self.joined_perms))

        await asyncio.sleep(0.5)
        await x.edit(category=cat)
        await self.config.channel(x).is_temp.set(True)
        await x.send(
            f"""Hi {ctx.author.mention}, I've created your channel here.
            People can join by using the following command.\n
            `{ctx.prefix}jointxt {x.id}`
            """
        )

    @commands.command(pass_context=True, no_pm=True, name="jointxt")
    async def _join_text(self, ctx, chan_id: int):
        """try to join a room"""
        author = ctx.author
        try:
            await self.bot.delete_message(ctx.message)
        except Exception:
            pass
        c = discord.utils.get(self.bot.get_all_channels(), id=chan_id)
        if c is None:
            return await ctx.send("That isn't a joinable channel")
        is_temp = await self.config.channel(c).is_temp()
        if not is_temp:
            return await ctx.send("That isn't a joinable channel")

        try:
            await c.set_permissions(author, self.joined_perms)
        except Exception as e:
            await ctx.send("Something unexpected went wrong. Good luck.")
        else:
            await ctx.send(f"Click this. It's a channel link, "
                           f"not a hashtag."
                           f"\nIf it isn't clickable, it isn't for you. "
                           f"{c.mention}")

    async def on_voice_state_update(self, member, v_before, v_after):
        if v_before.channel == v_after.channel:
            return

        if v_before.channel is not None:
            channel = v_before.channel
            is_temp = await self.config.channel(channel).is_temp()
            if is_temp:
                await self.process_channel(channel)

        if v_after.channel is not None:
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

        editargs = {'bitrate': chan.bitrate,
                    'user_limit': chan.user_limit}

        if category is not None:
            editargs.update({'category': category, 'sync_permissions': True})

        chanz = "".join([c for c in chan.name
                         if c != self.auto_room_indicator])
        chan_name = f'{self.clone_indicator}{chanz}'
        z = await chan.guild.create_voice_channel(chan_name)
        if z:
            await self.config.channel(z).is_temp.set(True)
        await asyncio.sleep(0.5)
        await z.edit(**editargs)
        await z.set_permissions(member,
                                manage_channels=True, manage_roles=True)
        await member.move_to(z, reason="autoroom")

    async def _make_game_room(self, member, chan, old_chan):

        category = chan.category

        editargs = {'bitrate': chan.bitrate, 'user_limit': chan.user_limit}

        if category is not None:
            editargs.update({'category': category, 'sync_permissions': True})

        if member.game is None:
            chan_name = f'{self.clone_indicator}Has no game'
        else:
            chan_name = f'{self.clone_indicator}{member.game.name}'

        z = await chan.guild.create_voice_channel(chan_name)
        if z:
            await self.config.channel(z).is_temp.set(True)
        await asyncio.sleep(0.5)
        await z.edit(**editargs)
        await z.set_permissions(member,
                                manage_channels=True, manage_roles=True)
        await member.move_to(z, reason="autoroom")

    async def process_channel(self, channel):
        if isinstance(channel, discord.VoiceChannel):
            if channel.created_at + timedelta(seconds=30) > datetime.utcnow():
                return
            if len(channel.members) == 0:
                try:
                    await channel.delete()
                except Exception:
                    pass
        if isinstance(channel, discord.TextChannel):
            if channel.created_at + timedelta(hours=2) > datetime.utcnow():
                return
            msg = await channel.history().get(channel=channel)
            if msg is not None:
                if msg.timestamp + timedelta(minutes=30) > datetime.utcnow():
                    return
            try:
                await channel.delete()
            except Exception:
                pass

    async def periodic_cleanup(self):
        for channel in self.bot.get_all_channels():
            is_temp = await self.config.channel(channel).is_temp()
            if is_temp:
                await self.bot.process_channel(channel)
        asyncio.sleep(600)

import asyncio
import discord
import json
import aiohttp
from discord.ext import commands
from redbot.core import Config
from redbot.core.utils import chat_formatting as cf


class Announcer:
    """
    Cog for making announcements
    """
    __author__ = "mikeshardmind"
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=5062380185, force_registration=True)
        self.config.register_channel(active=False)

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group()
    async def announcerset(self, ctx):
        """
        settings for Announcer
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @announcerset.command()
    async def addchans(self, ctx, *channels: discord.TextChannel):
        """
        takes one or more text channels to add to the announcement list
        """

        if len(channels) == 0:
            return await ctx.send_help()

        for channel in channels:
            await self.config.channel(channel).active.set(True)
        await ctx.send("Channels added")

    @announcerset.command()
    async def remchans(self, ctx, *channels: discord.TextChannel):
        """
        takes one or more text channels to remove from the announcement list
        """

        if len(channels) == 0:
            return await ctx.send_help()

        for channel in channels:
            await self.config.channel(channel).active.set(False)
        await ctx.send("Channels removed")

    @announcerset.command()
    async def clearchans(self, ctx):
        """
        clears the list of channels to which announcements are sent
        """

        await self.config.clear_all_channels()
        await ctx.send("Announcement channel list has been cleared")

    @announcerset.command()
    async def listchans(self, ctx):
        """
        lists the channels to which announcements are being sent
        """

        chans = await self.config.all_channels()
        chans = {k: v for k, v in chans.items() if v['active']}
        if len(chans) == 0:
            return await ctx.send("No channels in list")
        output = "Channels:"
        for k, v in chans.items():
            output += f'<#{k}>'

        for page in cf.pagify(output):
            await ctx.send(page)

    @commands.command()
    async def announce(self, ctx, *, announcement: str):
        """
        make an announcement
        """

        settings = await self.config.all_channels()
        channels = [c for c in self.bot.get_all_channels if c.id in
                    {k: v for k, v in settings.items() if v['active']}]

        no_perms = []

        for channel in channels:
            if not channel.permissions_for(channel.guild.me).send_messages:
                no_perms.append(channel)
                continue

            await channel.send(announcement)
            await asyncio.sleep(1)

        if len(no_perms) > 0:
            output = "I did not have permission to send the announcement in " \
                     "The following channels: "
            for channel in no_perms:
                output += f'\n{channel.mention} in {channel.guild.name}'
            for page in cf.pagify(output):
                await ctx.send(page)

    @announcerset.command()
    async def v2import(self, ctx):
        """
        import existing settings from Redv2 by uploading a json
        be careful with this, it may provide unexpected results if
        given a JSON that does not belong to the v2 version of my
        announcer cog
        """
        if not ctx.message.attachments:
            return await ctx.send("You must use this command as "
                                  "part of an upload")

        gateway = ctx.message.attachments[0]['url']
        payload = {}
        payload['limit'] = 1
        headers = {'user-agent': 'Python-Red-Discordbot'}
        session = aiohttp.ClientSession()
        async with session.get(gateway, params=payload, headers=headers) as r:
            f = await r.read()
            try:
                v2settings = json.load(f)
            except json.decoder.JSONDecodeError:
                v2settings = None
        session.close()

        if v2settings is None:
            return await ctx.send("That wasn't a valid JSON")

        channels = []
        for k, v in v2settings.items():
            try:
                channels.append(int(v['channel']))
            except AttributeError:
                pass

        for channel_id in channels:
            chan = discord.utils.get(self.bot.get_all_channels, id=channel_id)
            if chan is None:
                continue
            await self.config.channel(chan).active.set(True)

        await ctx.send("Settings imported")

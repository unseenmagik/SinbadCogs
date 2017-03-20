import os
import sys
from datetime import date, datetime, timedelta
import asyncio
#import logging #not logging anything currently
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks

#log = logging.getLogger('red.TempChannels') #not logging anything currently

class TempChannels:
    """
    allows creating temporary channels
    channels are auto-removed when they become empty
    or if nobody has entered them within 5 minutes of creation
    requires server admin or manage channels to enable
    once enabled all users can use it
    """

    #todo: give the person who added the channel the Manage channel permission for that channel
    __author__ = "mikeshardmind"
    __version__ = "1.3"

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/tempchannels/settings.json')

    @commands.group(name="tempchannels", aliases=["tmpc"], pass_context=True, no_pm=True)
    async def tempchannels(self, ctx):
        """Cog for allowing users to make temporary channels"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @tempchannels.group(name="tempset", pass_context=True, no_pm=True)
    async def tempset(self, ctx):
        """Configuration settings"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)



    def initial_config(self, server_id):
        """makes an entry for the server, defaults to turned off"""

        if server_id not in self.settings: #trust but verify
            self.settings[server_id] = {'toggleactive': False,
                                        'toggleowner': False,
                                        'channels': [],
                                        'cache': []
                                       }
            self.save_json()

    @checks.admin_or_permissions(Manage_channels=True)
    @tempset.command(name="toggleactive", pass_context=True, no_pm=True)
    async def tempchanneltoggle(self, ctx):
        """toggles the temp channels commands on/off for all users
        this requires the "Manage Channels" permission
        """
        server = ctx.message.server
        if server.id not in self.settings:
            self.initial_config(server.id)

        if self.settings[server.id]['toggleactive'] is True:
            self.settings[server.id]['toggleactive'] = False
            self.save_json()
            await self.bot.say('Creation of temporary channels is now disabled.')
        else:
            self.settings[server.id]['toggleactive'] = True
            self.save_json()
            await self.bot.say('Creation of temporary channels is now enabled.')

    @checks.admin_or_permissions(Manage_channels=True)
    @tempset.command(name="toggleowner", pass_context=True, no_pm=True)
    async def toggleowner(self, ctx):
        """toggles if the creator of the temp channel owns it
        requires the "Manage Channels" permission
        Defaults to false"""
        server = ctx.message.server
        if server.id not in self.settings:
            self.initial_config(server.id)

        if self.settings[server.id]['toggleowner'] is True:
            self.settings[server.id]['toggleowner'] = False
            self.save_json()
            await self.bot.say('Users no longer own the temp channels they make.')
        else:
            self.settings[server.id]['toggleowner'] = True
            self.save_json()
            await self.bot.say('Users now own the temp channels they make.')

    @tempchannels.command(name="new", pass_context=True, no_pm=True)
    async def newtemp(self, ctx, name: str):
        """makes a new temporary channel
        channel name should be enclosed in quotation marks"""
        server = ctx.message.server
        perms = ctx.message.server.get_member(self.bot.user.id).server_permissions

        if server.id not in self.settings:
            self.initial_config(server.id)

        if perms.manage_channels is False:
            await self.bot.say('I do not have permission to do that')
        elif self.settings[server.id]['toggleactive'] is False:
            await self.bot.say('This command is currently turned off.')
        else:
            channel = await self.bot.create_channel(server, name, type=discord.ChannelType.voice)
            if self.settings[server.id]['toggleowner'] is True:
                overwrite = discord.PermissionOverwrite()
                overwrite.manage_channels = True
                overwrite.manage_roles = True
                await self.bot.edit_channel_permissions(channel, ctx.message.author, overwrite)
            self.settings[server.id]['channels'].append(channel.id)
            self.save_json()


    #Minimum permissions required to remove the channels forcefully is manage_channels
    @checks.admin_or_permissions(Manage_channels=True)
    @tempchannels.command(name="purge", pass_context=True, no_pm=True)
    async def _purgetemps(self, ctx):
        """purges this server's temp channels even if in use"""
        server = ctx.message.server


        if server.id in self.settings:
            channels = self.settings[server.id]['channels']
            for channel_id in channels:
                channel = server.get_channel(channel_id)
                if channel is not None:
                    await asyncio.sleep(1)
                    await self.bot.delete_channel(channel)
                    channels.remove(channel.id)
                    self.save_json()
                await asyncio.sleep(1)
            await self.bot.say('Temporary Channels Purged')
        else:
            await self.bot.say('No Entires for this server.')
        self.settingscleanup(server)


    def save_json(self):
        dataIO.save_json("data/tempchannels/settings.json", self.settings)


    async def autoempty(self, memb_before, memb_after):
        """This cog is Self Cleaning"""
        server = memb_after.server
        channels = self.settings[server.id]['channels']
        cache = self.settings[server.id]['cache']

        #this prevents channels from being deleted before being used
        if memb_after.voice.voice_channel is not None:
            channel = memb_after.voice.voice_channel
            if channel.id in channels:
                if channel.id not in cache:
                    cache.append(channel.id)
                    self.save_json()

        #check to see if any temp rooms are empty when someone leaves a chat room
        channel = memb_before.voice.voice_channel
        if channel.id in cache:
            if len(channel.voice_members) == 0:
                await self.bot.delete_channel(channel)
                cache.remove(channel.id)
                channels.remove(channel.id)
                self.save_json()

        #unused temp channels should dissapear even if unused after 5 minutes
        for channel_id in channels:
            channel = server.get_channel(channel_id)
            if channel is not None:
                if len(server.get_channel(channel_id).voice_members) == 0:
                    tnow = datetime.utcnow() #.strftime('%Y-%m-%d %H:%M:%S')
                    ctime = server.get_channel(channel_id).created_at #.strftime('%Y-%m-%d %H:%M:%S')
                    tdelta = tnow - ctime
                    if tdelta.seconds > 300:
                        await self.bot.delete_channel(channel)
                        channels.remove(channel.id)
                        self.save_json()
                        await asyncio.sleep(1)

        self.settingscleanup(server)


    def settingscleanup(self, server):
        """cleanup of settings"""
        #can't clean a mess that doesn't exist
        if server.id in self.settings:
            channels = self.settings[server.id]['channels']
            cache = self.settings[server.id]['cache']
            for channel_id in channels:
                channel = server.get_channel(channel_id)
                if channel is None:
                    channels.remove(channel_id)
                    self.save_json()
            for channel_id in cache:
                if channel_id not in channels:
                    cache.remove(channel_id)
                    self.save_json()



def check_folder():
    f = 'data/tempchannels'
    if not os.path.exists(f):
        os.makedirs(f)

def check_file():
    f = 'data/tempchannels/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})

def setup(bot):
    check_folder()
    check_file()
    n = TempChannels(bot)
    bot.add_listener(n.autoempty, 'on_voice_state_update')
    bot.add_cog(n)

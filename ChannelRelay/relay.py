import discord
import itertools
import re
from discord.ext import commands
from redbot.core import Config
from redbot.core.utils import chat_formatting as cf


class ChannelRelay:
    """
    Can create multi-way channel relays
    """
    __author__ = "mikeshardmind"
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=9499802970, force_registration=True)
        self.config.register_channel(links=None)
        self.cached = False
        self.relaycache = {}

    async def __local_check(self, ctx):
        # I could make this slightly more permissive, but considering the
        # use case in mind here, I'd rather not.
        return await self.bot.is_owner(ctx.author)

    @commands.group()
    async def relayset(self, ctx):
        """
        configuration settings for ChannelRelay
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @relayset.command()
    async def makerelay(self, ctx, *channels: discord.TextChannel):
        """
        makes a relay from 2 or more text channels
        """
        channels = unique(channels)
        if len(channels) < 2:
            return await ctx.send_help()

        chans = await self.config.all_channels()
        chans = {k: v for k, v in chans.items() if v['links']}

        if any(c.id in chans for c in channels):
            return await ctx.send(f'I cannot make a relay using a channel '
                                  f'which is already part of a relay'
                                  f'\nUse `{ctx.prefix}relayset list` '
                                  f'to review existing relays')

        for channel in channels:
            await self.config.channel(channel).links.set(
                [c.id for c in channels if c != channel])
        await self.build_cache()
        await ctx.send("Relay formed")

    @relayset.command()
    async def clearrelays(self, ctx):
        """
        This command clears all existing relays
        """
        await self.config.clear_all_channels()
        self.relaycache = {}
        await ctx.send("All relays have been cleared")

    @relayset.command()
    async def removerelay(self, ctx, *channels: discord.TextChannel):
        """
        Removes relays by contained channel(s)
        """

        if len(channels) == 0:
            await ctx.send_help()
        channels = unique(channels)

        chans = await self.config.all_channels()
        if any(c.id not in {k: v for k, v in chans.items()
                            if v['links']} for c in channels):
            return await ctx.send(f'''one or more of those channels is not in a
                                      relay. \nUse {ctx.prefix}relayset list
                                      for more information about existing
                                      relays''')

        to_clear = []
        for channel in channels:
            to_clear.append(channel.id)
            to_clear.extend(chans[channel.id]['links'])
        to_clear = unique(to_clear)
        for channel in to_clear:
            await self.config.channel(channel).clear()
        await self.build_cache()
        await ctx.send("Relays cleared")

    @relayset.command(name="list")
    async def relaylist(self, ctx):
        """
        lists existing relays
        """
        chans = await self.config.all_channels()
        chans = {k: v for k, v in chans.items() if v['links']}
        relays = []
        if len(chans) == 0:
            return await ctx.send('No active relays')

        for k, v in chans.items():
            relays.append(sorted([k].extend(v)))
        relays = unique(relays)

        output = 'Active relays:'
        for i in range(0, len(relays)):
            channel_mentions = [f'<#{cid}>' for cid in relays[i]]
            output += f'\nRelay #{i}: {channel_mentions}'

        for page in cf.pagify(output):
            await ctx.send(page)

    async def build_cache(self):
        chans = await self.config.all_channels()
        chans = {k: v for k, v in chans.items() if v['links']}
        self.relaycache = {}
        for k, v in chans.items():
            channels = [c for c in self.bot.get_all_channels if c.id in v]
            self.relaycache[k] = channels

    async def on_message(self, message):
        if message.author.bot:
            return
        if not self.cached:
            await self.build_cache()

        if message.channel.id in self.relaycache:
            for channel in self.relaycache[message.channel.id]:
                try:
                    await channel.send(embed=quote_from_message(message))
                except Exception:
                    pass


def role_mention_cleanup(self, message: discord.message):
    # this function is a butchered version of discord.py's
    # discord.message.clean_content
    # I specifically want only role mentions removed from this
    if message.server is None:
        return message.content

    transformations = {
        re.escape('<@&{0.id}>'.format(role)): '@' + role.name
        for role in message.role_mentions
    }

    def repl(obj):
        return transformations.get(re.escape(obj.group(0)), '')

    pattern = re.compile('|'.join(transformations.keys()))
    result = pattern.sub(repl, message.content)

    return result


def quote_from_message(message: discord.Message):
    channel = message.channel
    guild = message.guild
    content = role_mention_cleanup(message)
    author = message.author
    avatar = author.avatar_url
    em = discord.Embed(description=content, color=author.color,
                       timestamp=message.timestamp)
    em.set_author(name=f'{author.display_name}', icon_url=avatar)
    footer = f'Said in {guild.name} #{channel.name}'
    em.set_footer(text=footer, icon_url=guild.icon_url)
    if message.attachments:
        a = message.attachments[0]
        fname = a['filename']
        url = a['url']
        if fname.split('.')[-1] in ['png', 'jpg', 'gif', 'jpeg']:
            em.set_image(url=url)
        else:
            em.add_field(name='Message has an attachment',
                         value=f'[{fname}]({url})', inline=True)
    return em


def unique(a):
    indices = sorted(range(len(a)), key=a.__getitem__)
    indices = set(next(it) for k, it in
                  itertools.groupby(indices, key=a.__getitem__))
    return [x for i, x in enumerate(a) if i in indices]

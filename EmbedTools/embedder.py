import discord
import asyncio
from datetime import datetime
from discord.ext import commands
from redbot.core import Config, checks


class Embedder:
    """
    make embeds that can be called later
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=2081794460, force_registration=True)
        self.config.register_channel(embeds={})
        self.config.register_guild(embeds={})
        self.config.register_global(embeds={})

    @commands.group(name="embedmake")
    async def embed_make(self, ctx):
        """
        commands for making embeds
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @checks.is_owner()
    @embed_make.command(name="global")
    async def make_global_embed(self, ctx, *, name: str):
        """
        make a globally accessible embed
        """

        try:
            em = await self.interactive_embed(ctx)
        except RuntimeError as e:
            return await ctx.send(e)
        if em is None:
            return
        embeds = await self.config.embeds()
        embeds.update({name: em})

    async def interactive_embed(self, ctx):
        author = ctx.author
        try:
            dm = await author.send("Please respond to this message "
                                   "with the title of your embed. If "
                                   "you do not want a title, wait 30s")
        except Exception:
            raise RuntimeError("I could not message you to begin the "
                               "interactive prompt")
            return

        def pred(m):
            return m.author == ctx.author and m.channel == dm.channel
        try:
            msg = await self.bot.wait_for('message', check=pred, timeout=30)
            title = msg.clean_content
        except asyncio.TimeoutError:
            await author.send("Okay, this one won't have a title.")

        dm = await author.send("Please respond to this message "
                               "with the content of your embed.")

        try:
            msg = await self.bot.wait_for('message', check=pred, timeout=120)
            content = msg.clean_content
        except asyncio.TimeoutError:
            await author.send("I won't wait forever. Try again later")
            return None

        em = {"title": title,
              "content": content,
              "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M'),
              "author": ctx.author.id}

        return em

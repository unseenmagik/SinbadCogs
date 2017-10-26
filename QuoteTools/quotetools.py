import discord
from discord.ext import commands
from typing import Union


class QuoteTools:
    """
    various tools for quoting people
    """
    __author__ = "mikeshardmind"
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx, message_id: int):
        """
        quote a message by ID
        """
        try:
            msg = await self.find_message(message_id)
        except discord.NotFound:
            ctx.send("Couldn't find that one.")
        else:
            try:
                em = self.quote_from_message(msg)
                ctx.send(embed=em)
            except Exception:
                ctx.send("I don't have permission to do that")

    async def find_message(self, message_id: int,
                           chan: Union[int, discord.TextChannel]=None):

        if chan is not None:
            if isinstance(chan, int):
                channel = discord.utils.get(self.bot.get_all_channels, id=chan)
            else:
                channel = chan

        if channel:
            try:
                msg = channel.get_message(message_id)
            except Exception:
                raise
            else:
                return msg
        else:
            for channel in self.bot.get_all_channels:
                try:
                    msg = channel.get_message(message_id)
                except Exception:
                    pass
                else:
                    return msg
            else:
                raise discord.NotFound

    def quote_from_message(message: discord.Message):
        channel = message.channel
        guild = message.guild
        content = message.clean_content
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

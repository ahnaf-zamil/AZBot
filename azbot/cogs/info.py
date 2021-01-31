from discord.ext import commands
from azbot import AZBot
from datetime import datetime

import time
import discord


class Information(commands.Cog):
    def __init__(self, bot: AZBot) -> None:
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        """Shows the latency for the bot"""
        start = time.monotonic()
        msg = await ctx.send("Pinging...")
        millis = (time.monotonic() - start) * 1000

        # Since sharded bots will have more than one latency, this will average them
        heartbeat = ctx.bot.latency * 1000

        # Embed creation
        em = discord.Embed(title="📡 Latency 📡", color=discord.Color.blue())
        em.add_field(name="HTTP API", value=f"`{int(millis):,.2f}ms`", inline=True)
        em.add_field(name="WSS API", value=f"`{int(heartbeat):,.2f}ms`", inline=True)
        em.set_footer(text=str(self.bot.user), icon_url=self.bot.user.avatar_url_as())
        em.timestamp = datetime.now().astimezone()

        await msg.edit(embed=em)


# Setup function for loading the cog
def setup(bot: AZBot):
    bot.add_cog(Information(bot))

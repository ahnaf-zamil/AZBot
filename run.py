from azbot import AZBot
from dotenv import load_dotenv
from discord.ext import commands

import logging
import os
import discord


# setting up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s[%(lineno)d] - %(levelname)s: %(message)s",
    datefmt="%m/%d/%y %H:%M:%S",
)

# loading .env config into system vars
load_dotenv(verbose=True)

# configuring intents
intents = discord.Intents.default()
intents.members = True

bot = AZBot(
    command_prefix=os.getenv("PREFIX"), intents=intents, token=os.getenv("TOKEN")
)


@bot.command()
async def test(ctx: commands.Context):
    await ctx.reply(str(bot.uptime))


# Run bot
bot.run()

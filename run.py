from azbot import AZBot
from dotenv import load_dotenv

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

# Instantiate bot
bot = AZBot(
    command_prefix=os.getenv("PREFIX"), intents=intents, token=os.getenv("TOKEN")
)

# Loading cogs
for i in os.listdir("./azbot/cogs"):
    if i.endswith(".py"):  # if it's a python file
        bot.load_extension(f"azbot.cogs.{i[:-3]}")


# Run bot
bot.run()

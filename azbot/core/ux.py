from colorama import Fore, Style, init
from discord.ext import commands
from azbot.about import __version__, __author__

import logging
import typing

__all__: typing.Final = ["draw_line", "startup_banner"]


try:
    # Initializing coloroma for windows
    init()
except:
    pass


def draw_line(logger: logging.Logger):
    """Draws a line on the console screen"""
    logger.log(
        logging.INFO,
        f"{Fore.CYAN}-------------------------------------{Style.RESET_ALL}",
    )


def startup_banner(logger):
    """Prints the startup banner"""
    draw_line(logger)
    logger.info(
        f"{Fore.YELLOW}{Style.BRIGHT}            __________        _   {Style.RESET_ALL}"
    )
    logger.info(
        f"{Fore.YELLOW}{Style.BRIGHT}     /\    |___  /  _ \      | |  {Style.RESET_ALL}"
    )
    logger.info(
        f"{Fore.YELLOW}{Style.BRIGHT}    /  \      / /| |_) | ___ | |_ {Style.RESET_ALL}"
    )
    logger.info(
        f"{Fore.YELLOW}{Style.BRIGHT}   / /\ \    / / |  _ < / _ \| __|{Style.RESET_ALL}"
    )
    logger.info(
        f"{Fore.YELLOW}{Style.BRIGHT}  / ____ \  / /__| |_) | (_) | |_ {Style.RESET_ALL}"
    )
    logger.info(
        f"{Fore.YELLOW}{Style.BRIGHT} /_/    \_\/_____|____/ \___/ \__|{Style.RESET_ALL}"
    )
    logger.info("")
    draw_line(logger)
    logger.info(f"{Fore.YELLOW}{Style.BRIGHT}v{__version__}{Style.RESET_ALL}")
    logger.info(f"{Fore.YELLOW}{Style.BRIGHT}Author: {__author__}{Style.RESET_ALL}")
    draw_line(logger)


async def bot_ready(logger, bot: commands.Bot):
    """Display's bot ready message on console"""
    draw_line(logger)
    logger.info(f"{Fore.CYAN}{Style.BRIGHT}Bot is ready{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}{Style.BRIGHT}Username:{Style.RESET_ALL} {bot.user.name}")
    logger.info(
        f"{Fore.CYAN}{Style.BRIGHT}Discriminator:{Style.RESET_ALL} {bot.user.discriminator}"
    )
    logger.info(f"{Fore.CYAN}{Style.BRIGHT}ID:{Style.RESET_ALL} {bot.user.id}")
    draw_line(logger)

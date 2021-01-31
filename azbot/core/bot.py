from discord.ext import commands
from datetime import datetime

from azbot.core.ux import startup_banner, bot_ready
from azbot.core.utils import Uptime

import typing
import discord
import logging


__all__: typing.Final = ["AZBot"]


class AZBot(commands.Bot):
    def __init__(
        self,
        command_prefix: typing.AnyStr,
        intents: discord.Intents,
        token: typing.AnyStr,
        *,
        logger: logging.Logger = None
    ) -> None:
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
        )

        self._logger = logger
        self._token = token
        self.prefix = command_prefix
        self.start_time = datetime.utcnow()

        startup_banner(self.logger)

    def run(self) -> None:
        """Runs the bot"""
        token = self._token
        super().run(token)

    # Properties
    @property
    def logger(self) -> logging.Logger:
        """Returns the bot's logger if exists, else it creates one"""
        if not self._logger:
            self._logger = logging.getLogger("AzBot")
        return self._logger

    @property
    def uptime(self) -> Uptime:
        """Returns the bot's current uptime"""
        delta_uptime = datetime.utcnow() - self.start_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        return Uptime(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # Events
    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await bot_ready(self.logger, self)

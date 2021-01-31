from discord.ext import commands

import re
import typing
import discord
import lavalink

url_rx = re.compile(r"https?://(?:www\.)?.+")


class Music(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        if not hasattr(
            bot, "lavalink"
        ):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(703153123450945557)
            bot.lavalink.add_node(
                "127.0.0.1", 2333, "youshallnotpass", "eu", "default-node"
            )  # Host, Port, Password, Region, Name
            bot.add_listener(bot.lavalink.voice_update_handler, "on_socket_response")

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self) -> None:
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx: commands.Context) -> bool:
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voicechannel.

        return guild_check

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    async def ensure_voice(self, ctx: commands.Context) -> None:
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(
            ctx.guild.id, endpoint=str(ctx.guild.region)
        )
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ("play",)

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError("Join a voicechannel first.")

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError("Not connected.")

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if (
                not permissions.connect or not permissions.speak
            ):  # Check user limit too?
                raise commands.CommandInvokeError(
                    "I need the `CONNECT` and `SPEAK` permissions."
                )

            player.store("channel", ctx.channel.id)
            await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError("You need to be in my voicechannel.")

    async def track_hook(self, event) -> None:
        if isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)

    async def connect_to(self, guild_id: int, channel_id: str) -> None:
        """Connects to the given voicechannel ID. A channel_id of `None` means disconnect. """
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id, self_deaf=True)
        # The above looks dirty, we could alternatively use `bot.shards[shard_id].ws` but that assumes
        # the bot instance is an AutoShardedBot.

    @commands.command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Searches and plays a song from a given query. """
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip("<>")

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f"ytsearch:{query}"

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results["tracks"]:
            return await ctx.send("Nothing found!")

        embed = discord.Embed(color=discord.Color.blue())
        if results["loadType"] == "PLAYLIST_LOADED":
            tracks = results["tracks"]
            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author.id, track=track)

            embed.title = "Playlist Enqueued!"
            embed.description = (
                f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
            )
        else:
            track = results["tracks"][0]
            if not player.is_playing:
                embed.title = "Playing now:"
            else:
                embed.title = "Added to queue:"
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
        await ctx.send(embed=embed)
        if not player.is_playing:
            await player.play()

    @commands.command(aliases=["stop"])
    async def disconnect(self, ctx: commands.Context) -> None:
        """Disconnects the bot from the voice channel and clears it's queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # Don't disconnect if not connected
            return await ctx.send(
                "I am not connected to any voice channels in this server :c"
            )

        if not ctx.author.voice or (
            player.is_connected
            and ctx.author.voice.channel.id != int(player.channel_id)
        ):
            # Those who aren't in the voice channel, they can't disconnect the bot
            return await ctx.send(
                "You are not in my voice channel, so you can't disconnect me"
            )
        # Clearing queue4
        player.queue.clear()
        # Stops the current track
        await player.stop()
        # Disconnect from the voice channel
        await ctx.message.add_reaction("⏹️")
        await self.connect_to(ctx.guild.id, None)
        await ctx.send(f"Disconnected from **<#{ctx.author.voice.channel.id}>**.")

    @commands.command(aliases=["q"])
    async def queue(self, ctx: commands.Context) -> None:
        """Shows the music queue for this server"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # Don't disconnect if not connected
            return await ctx.send(
                "I am not connected to any voice channels in this server :c"
            )

        queue = player.queue
        description = ""
        if len(queue):
            for i, v in enumerate(queue, start=1):
                requester = ctx.guild.get_member(v.requester)
                description += f"{i}. [**{v.title}**]({v.uri}) (Requested by {requester.mention})\n"
        else:
            description = "Queue is empty."
        em = discord.Embed(
            title="Music Queue", color=discord.Color.blue(), description=description
        )
        await ctx.send(embed=em)

    @commands.command()
    async def pause(self, ctx: commands.Context) -> None:
        """Pauses the current track"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # Don't disconnect if not connected
            return await ctx.send(
                "I am not connected to any voice channels in this server :c"
            )
        if not ctx.author.voice or (
            player.is_connected
            and ctx.author.voice.channel.id != int(player.channel_id)
        ):
            # Those who aren't in the voice channel, they can't pause the bot
            return await ctx.send(
                "You are not in my voice channel, so you can't pause me"
            )
        await ctx.message.add_reaction("⏸️")
        if not player.paused:
            await player.set_pause(True)
        else:
            await ctx.send("I am already paused.")

    @commands.command()
    async def resume(self, ctx: commands.Context) -> None:
        """Resumes the current track"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # Don't disconnect if not connected
            return await ctx.send(
                "I am not connected to any voice channels in this server :c"
            )
        if not ctx.author.voice or (
            player.is_connected
            and ctx.author.voice.channel.id != int(player.channel_id)
        ):
            # Those who aren't in the voice channel, they can't pause the bot
            return await ctx.send(
                "You are not in my voice channel, so you can't resume me"
            )
        await ctx.message.add_reaction("⏯️")
        if player.paused:
            await player.set_pause(False)
        else:
            await ctx.send("I am not paused.")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx: commands.Context) -> None:
        """Shows the track that is currently playing"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # Don't disconnect if not connected
            return await ctx.send(
                "I am not connected to any voice channels in this server :c"
            )
        playing = player.current
        em = discord.Embed(
            title="Now Playing",
            color=discord.Color.blue(),
            description=f"[**{playing.title}**]({playing.uri}) (Requested by {ctx.guild.get_member(playing.requester).mention})\n",
        )
        await ctx.send(embed=em)

    @commands.command()
    async def volume(
        self, ctx: commands.Context, *, level: typing.Optional[int] = None
    ) -> None:
        """Changes the bot's volume level"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # Don't disconnect if not connected
            return await ctx.send(
                "I am not connected to any voice channels in this server :c"
            )

        if not level:
            await ctx.send(f"The current volume is: **{player.volume}**")
        else:
            if level > 100:
                return await ctx.send("Volume level cannot exceed 100.")
            await player.set_volume(level)
            return await ctx.send(f"Set volume level to **{level}**.")

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        """Skips to the next track in the queue, if any"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            # Don't disconnect if not connected
            return await ctx.send(
                "I am not connected to any voice channels in this server :c"
            )
        if not ctx.author.voice or (
            player.is_connected
            and ctx.author.voice.channel.id != int(player.channel_id)
        ):
            # Those who aren't in the voice channel, they can't pause the bot
            return await ctx.send(
                "You are not in my voice channel, so you can't skip the current track"
            )
        await player.skip()
        await ctx.message.add_reaction("⏭️")
        await ctx.send("Skipped..")


def setup(bot):
    bot.add_cog(Music(bot))

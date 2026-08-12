import os
from typing import Optional, Union, cast

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.cog import _cog_special_method


BOOST_CHANNEL_ID = int(os.getenv("BOOST_CHANNEL_ID", "0"))


class Boosts(commands.Cog):
    """Handles everything related to server boosts."""

    def __init__(self, bot: commands.Bot):
        self.bot: Optional[commands.Bot] = bot
        self.boost_channel_id: int = BOOST_CHANNEL_ID

    async def cog_load(self) -> None:
        """Log when the boosts cog is loaded."""
        bot_name = getattr(self.bot, "user", None)
        print(f"📦 Boosts cog loaded for {bot_name or 'bot'}.")

    @_cog_special_method
    async def cog_unload(self) -> None:
        """Log when the boosts cog is unloaded."""
        print("📦 Boosts cog unloaded.")
        self.bot = None

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Allow prefix commands only when the bot is ready."""
        return self.bot is not None and self.bot.is_ready()

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """Log prefix command invocation."""
        print(f"📦 Boosts cog running command: {ctx.command}")

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        """Log when a prefix command finishes."""
        print(f"📦 Boosts cog finished command: {ctx.command}")

    async def cog_command_error(
        self,
        ctx: commands.Context,
        error: Exception,
    ) -> None:
        """Handle errors raised by prefix commands."""

        print(f"📦 Boosts cog command error in {ctx.command}: {error}")

        if isinstance(error, commands.CommandNotFound):
            return

        if ctx.interaction is not None:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(
                    "An error occurred while running boosts commands.",
                    ephemeral=True,
                )
            return

        try:
            await ctx.send(
                "📦 Something went wrong while running that command."
            )
        except discord.HTTPException:
            pass

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """Handle errors raised by slash commands."""

        print(f"📦 Boosts cog slash command error: {error}")

        if interaction.response.is_done():
            return

        await interaction.response.send_message(
            "An error occurred while running boosts commands.",
            ephemeral=True,
        )

    def get_boost_channel(
        self,
        guild: Optional[discord.Guild],
    ) -> Optional[discord.abc.Messageable]:
        """Resolve the configured boost announcement channel."""

        if guild is None:
            return None

        channel_id = self.boost_channel_id

        if channel_id == 0:
            return None

        channel = guild.get_channel(channel_id)

        if channel is None or not isinstance(
            channel,
            discord.abc.Messageable,
        ):
            return None

        return cast(discord.abc.Messageable, channel)

    async def send_boost_message(
        self,
        channel: discord.abc.Messageable,
        member: Union[discord.Member, discord.User],
        boost_count: int,
        boost_level: int = 0,
    ):
        """Send the Cardboard Box boost announcement."""

        guild = getattr(channel, "guild", None)

        if guild is None:
            return

        # Use the supplied level, but fall back to Discord's
        # current server level if one wasn't supplied.
        boost_level = boost_level or guild.premium_tier

        embed = discord.Embed(
            title="📦 someone brought something for the box",
            description=(
                f"**{member.mention}** just boosted the box. 🪽\n\n"
                "thanks for helping keep our little corner warm.\n"
                "make yourself comfortable — there's always room in the box."
            ),
            color=0xC9A66B,
        )

        embed.add_field(
            name="box status",
            value=(
                f"📦 `{boost_count} boost"
                f"{'s' if boost_count != 1 else ''}`\n"
                f"🪽 `Level {boost_level}`"
            ),
            inline=False,
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        embed.set_footer(
            text="Clouddyie's Cardboard Box  ·  📦🪽"
        )

        await channel.send(embed=embed)

    # ---------------------------------------------------------
    # SLASH COMMAND
    # ---------------------------------------------------------

    @app_commands.command(
        name="testboost",
        description="Test the server's boost announcement.",
    )
    async def testboost_slash(
        self,
        interaction: discord.Interaction,
    ):
        """Test the boost announcement using /testboost."""

        if interaction.guild is None:
            await interaction.response.send_message(
                "📦 This command must be used in a server.",
                ephemeral=True,
            )
            return

        channel = self.get_boost_channel(interaction.guild)

        if channel is None:
            await interaction.response.send_message(
                "📦 I couldn't find the boost channel.",
                ephemeral=True,
            )
            return

        boost_count = interaction.guild.premium_subscription_count
        boost_level = interaction.guild.premium_tier

        await self.send_boost_message(
            channel,
            interaction.user,
            boost_count,
            boost_level,
        )

        await interaction.response.send_message(
            "📦 Test boost sent!",
            ephemeral=True,
        )

    # ---------------------------------------------------------
    # PREFIX COMMAND
    # ---------------------------------------------------------

    @commands.command(name="testboost")
    @commands.guild_only()
    async def testboost_prefix(
        self,
        ctx: commands.Context,
    ):
        """Test the boost announcement using the server prefix."""

        if ctx.guild is None:
            return

        channel = self.get_boost_channel(ctx.guild)

        if channel is None:
            await ctx.send(
                "📦 I couldn't find the boost channel."
            )
            return

        boost_count = ctx.guild.premium_subscription_count
        boost_level = ctx.guild.premium_tier

        await self.send_boost_message(
            channel,
            ctx.author,
            boost_count,
            boost_level,
        )

        await ctx.send(
            "📦 Test boost sent!"
        )

    # ---------------------------------------------------------
    # REAL BOOST DETECTION
    # ---------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):
        """Detect when a member starts boosting."""

        # A member went from not boosting → boosting.
        if (
            before.premium_since is None
            and after.premium_since is not None
        ):
            boost_count = after.guild.premium_subscription_count
            boost_level = after.guild.premium_tier

            if self.bot is None:
                return

            channel = self.get_boost_channel(after.guild)

            if channel is None:
                return

            await self.send_boost_message(
                channel,
                after,
                boost_count,
                boost_level,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Boosts(bot))
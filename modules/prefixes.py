import os
import sqlite3
from typing import Optional

import discord
from discord.ext import commands


DEFAULT_PREFIX = "d!"
DATABASE_PATH = os.getenv("DATABASE_PATH", "moderation.db")


db = sqlite3.connect(DATABASE_PATH)
db.row_factory = sqlite3.Row

db.execute("""
CREATE TABLE IF NOT EXISTS prefixes (
    guild_id INTEGER PRIMARY KEY,
    prefix TEXT NOT NULL
)
""")
db.commit()


def get_server_prefix(guild_id: int) -> str:
    """Get the configured prefix for a server."""
    row = db.execute(
        "SELECT prefix FROM prefixes WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()

    if row is None:
        return DEFAULT_PREFIX

    return str(row["prefix"])


def set_server_prefix(guild_id: int, prefix: str) -> None:
    """Set the prefix for a server."""
    db.execute(
        """
        INSERT INTO prefixes (guild_id, prefix)
        VALUES (?, ?)
        ON CONFLICT(guild_id)
        DO UPDATE SET prefix = excluded.prefix
        """,
        (guild_id, prefix),
    )
    db.commit()


def reset_server_prefix(guild_id: int) -> None:
    """Reset a server back to the default prefix."""
    db.execute(
        "DELETE FROM prefixes WHERE guild_id = ?",
        (guild_id,),
    )
    db.commit()


def get_prefix(
    bot: commands.Bot,
    message: discord.Message,
):
    """Return the prefixes that should work for this message."""
    if message.guild is None:
        return DEFAULT_PREFIX

    server_prefix = get_server_prefix(message.guild.id)

    # d! always remains available so the prefix can never accidentally
    # become impossible to change.
    if server_prefix == DEFAULT_PREFIX:
        return DEFAULT_PREFIX

    return [server_prefix, DEFAULT_PREFIX]


class Prefixes(commands.Cog):
    """Handles server-specific command prefixes."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="prefix")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix(
        self,
        ctx: commands.Context,
        action: Optional[str] = None,
        new_prefix: Optional[str] = None,
    ):
        """View or change the server prefix."""
        guild = ctx.guild
        if guild is None:
            return

        current_prefix = get_server_prefix(guild.id)

        if action is None:
            await ctx.send(
                f"🪽 The current prefix is `{current_prefix}`."
            )
            return

        action = action.lower()

        if action == "set":
            if not new_prefix:
                await ctx.send(
                    "📦 Please give me the new prefix.\n"
                    "Example: `d!prefix set c!`"
                )
                return

            if len(new_prefix) > 5:
                await ctx.send(
                    "📦 That prefix is a little too long. "
                    "Please keep it to 5 characters or fewer."
                )
                return

            if new_prefix.isspace():
                await ctx.send(
                    "📦 The prefix can't be only spaces."
                )
                return

            set_server_prefix(guild.id, new_prefix)

            await ctx.send(
                f"🪽 Prefix changed from `{current_prefix}` "
                f"to `{new_prefix}`."
            )
            return

        if action == "reset":
            reset_server_prefix(guild.id)

            await ctx.send(
                f"📦 Prefix reset to `{DEFAULT_PREFIX}`."
            )
            return

        await ctx.send(
            "📦 I don't know that prefix action.\n\n"
            f"`{current_prefix}prefix` — show the current prefix\n"
            f"`{current_prefix}prefix set c!` — change it\n"
            f"`{current_prefix}prefix reset` — reset to `{DEFAULT_PREFIX}`"
        )

    @prefix.error
    async def prefix_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ):
        """Handle prefix command errors."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "📦 You need **Manage Server** permission "
                "to change the prefix."
            )
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "📦 You're missing something.\n"
                "Try `d!prefix` to see how the command works."
            )
            return

        print(f"📦 Prefix command error: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Prefixes(bot))
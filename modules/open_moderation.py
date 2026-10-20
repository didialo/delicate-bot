import discord

from discord import app_commands
from discord.ext import commands

from database import database


PUBLIC_ACTIONS = {
    "WARN",
    "KICK",
    "BAN",
    "MUTE",
    "UNBAN",
    "UNMUTE",
}


def initialize_tables():
    database.db.execute(
        """
        CREATE TABLE IF NOT EXISTS open_moderation_settings (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            enabled_actions TEXT NOT NULL DEFAULT ''
        )
        """
    )

    database.db.execute(
        """
        CREATE TABLE IF NOT EXISTS open_moderation_cases (
            guild_id INTEGER NOT NULL,
            case_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            published_at INTEGER NOT NULL,
            PRIMARY KEY (guild_id, case_id)
        )
        """
    )

    database.db.commit()


def get_settings(guild_id: int):
    return database.db.execute(
        """
        SELECT *
        FROM open_moderation_settings
        WHERE guild_id = ?
        """,
        (guild_id,),
    ).fetchone()


def escape_public_text(value, limit=900):
    text = discord.utils.escape_mentions(str(value or "No reason provided."))
    return text[:limit]


class OpenModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    openmoderation = app_commands.Group(
        name="openmoderation",
        description="Configure public moderation records.",
    )

    @openmoderation.command(
        name="setup",
        description="Set the public moderation channel.",
    )
    @app_commands.describe(
        channel="Channel where public moderation records will appear."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_public_moderation(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        database.db.execute(
            """
            INSERT INTO open_moderation_settings (
                guild_id,
                channel_id,
                enabled_actions
            )
            VALUES (?, ?, '')
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id
            """,
            (interaction.guild.id, channel.id),
        )
        database.db.commit()

        await interaction.response.send_message(
            f"Open Moderation is configured to use {channel.mention}. "
            "No actions are public yet. Use `/openmoderation config` "
            "to select which actions may be published.",
            ephemeral=True,
        )

    @openmoderation.command(
        name="config",
        description="Choose which moderation actions are public.",
    )
    @app_commands.describe(
        actions=(
            "Comma-separated actions: WARN, KICK, BAN, MUTE, "
            "UNBAN, UNMUTE. Use NONE to disable publication."
        )
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def configure_public_actions(
        self,
        interaction: discord.Interaction,
        actions: str,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        settings = get_settings(interaction.guild.id)

        if settings is None or settings["channel_id"] is None:
            await interaction.response.send_message(
                "Run `/openmoderation setup` first.",
                ephemeral=True,
            )
            return

        requested = {
            item.strip().upper()
            for item in actions.split(",")
            if item.strip()
        }

        if requested == {"NONE"}:
            requested.clear()
        else:
            invalid = requested - PUBLIC_ACTIONS

            if invalid:
                await interaction.response.send_message(
                    "Invalid actions: "
                    + ", ".join(sorted(invalid))
                    + ". Valid actions: "
                    + ", ".join(sorted(PUBLIC_ACTIONS))
                    + ".",
                    ephemeral=True,
                )
                return

        database.db.execute(
            """
            UPDATE open_moderation_settings
            SET enabled_actions = ?
            WHERE guild_id = ?
            """,
            (
                ",".join(sorted(requested)),
                interaction.guild.id,
            ),
        )
        database.db.commit()

        if requested:
            result = ", ".join(sorted(requested))
        else:
            result = "None; public publishing is disabled."

        await interaction.response.send_message(
            f"Public moderation actions updated: {result}",
            ephemeral=True,
        )

    @app_commands.command(
        name="cases",
        description="View publicly published moderation cases.",
    )
    async def public_cases(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        rows = database.db.execute(
            """
            SELECT
                c.id,
                c.action,
                c.user_name,
                c.created_at
            FROM open_moderation_cases AS p
            JOIN cases AS c
                ON c.id = p.case_id
                AND c.guild_id = p.guild_id
            WHERE p.guild_id = ?
            ORDER BY p.case_id DESC
            LIMIT 10
            """,
            (interaction.guild.id,),
        ).fetchall()

        if not rows:
            await interaction.response.send_message(
                "There are no publicly published moderation cases.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Public Moderation Cases",
            color=discord.Color.blurple(),
            description="Most recently published moderation records.",
        )

        for row in rows:
            created = f"<t:{row['created_at']}:R>"
            embed.add_field(
                name=f"Case #{row['id']} · {row['action']}",
                value=(
                    f"**User:** "
                    f"{escape_public_text(row['user_name'], 100)}\n"
                    f"**Date:** {created}\n"
                    f"**Lookup:** `/case case_id:{row['id']}`"
                ),
                inline=False,
            )

        embed.set_footer(
            text=f"{interaction.guild.name} · Public records"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_moderation_case_created(
        self,
        guild,
        case_id,
        action,
        member,
        moderator,
        reason,
        duration=None,
    ):
        if guild is None:
            return

        settings = get_settings(guild.id)

        if settings is None or settings["channel_id"] is None:
            return

        enabled_actions = {
            item.strip().upper()
            for item in settings["enabled_actions"].split(",")
            if item.strip()
        }

        if action.upper() not in enabled_actions:
            return

        channel = guild.get_channel(settings["channel_id"])

        if not isinstance(channel, discord.TextChannel):
            return

        duration_text = duration or "Not applicable"

        embed = discord.Embed(
            title=f"Public Moderation Record · Case #{case_id}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
            description=(
                f"**Action:** {action.upper()}\n"
                f"**User:** {escape_public_text(member, 150)}\n"
                f"**User ID:** `{member.id}`\n"
                f"**Moderator:** {escape_public_text(moderator, 150)}\n"
                f"**Reason:** {escape_public_text(reason)}\n"
                f"**Duration:** {escape_public_text(duration_text, 100)}"
            ),
        )

        embed.set_footer(
            text=f"Case #{case_id} · {guild.name}"
        )

        try:
            message = await channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            return

        database.db.execute(
            """
            INSERT OR REPLACE INTO open_moderation_cases (
                guild_id,
                case_id,
                channel_id,
                message_id,
                published_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                guild.id,
                case_id,
                channel.id,
                message.id,
                int(discord.utils.utcnow().timestamp()),
            ),
        )
        database.db.commit()


async def setup(bot):
    initialize_tables()
    await bot.add_cog(OpenModeration(bot))


import json
import re
import time

import discord
from discord.ext import commands

from database import database


def format_timestamp(timestamp):
    if not timestamp:
        return "Unknown"
    return f"<t:{int(timestamp)}:R>"


def parse_duration(value):
    """Convert durations such as 30m, 1h, 2d or 1w to seconds."""
    match = re.fullmatch(
        r"\s*(\d+)\s*(s|m|h|d|w)\s*",
        value.lower(),
    )

    if not match:
        raise ValueError(
            "Use a duration such as `30m`, `1h`, `2d` or `1w`."
        )

    amount = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
    }

    seconds = amount * multipliers[unit]

    if amount < 1 or seconds > 365 * 86400:
        raise ValueError("Duration must be between 1 second and 365 days.")

    return seconds


class SpecialSystems(commands.Cog):
    """Snapshots, staff handoffs, system health and member timelines."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        database.db.execute(
            """
            CREATE TABLE IF NOT EXISTS server_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                creator_id INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                snapshot_json TEXT NOT NULL
            )
            """
        )

        database.db.execute(
            """
            CREATE TABLE IF NOT EXISTS foster_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                guardian_id INTEGER NOT NULL,
                duration TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_snapshots_guild
            ON server_snapshots (guild_id, created_at)
            """
        )

        database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_foster_active
            ON foster_assignments (guild_id, member_id, active)
            """
        )

        database.db.commit()
        print("Delicate Systems loaded.")

    # ---------------------------------------------------------
    # SNAPSHOT
    # ---------------------------------------------------------

    @commands.hybrid_command(
        name="snapshot",
        description="Save a snapshot of the current server state.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def snapshot(self, ctx, *, name: str = "Manual snapshot"):
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a server.")

        guild = ctx.guild
        now = int(time.time())

        settings_row = database.db.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?",
            (guild.id,),
        ).fetchone()

        settings = dict(settings_row) if settings_row else {}

        data = {
            "guild_id": guild.id,
            "guild_name": guild.name,
            "member_count": guild.member_count,
            "channel_count": len(guild.channels),
            "role_count": len(guild.roles),
            "boost_count": guild.premium_subscription_count or 0,
            "boost_level": guild.premium_tier,
            "settings": settings,
        }

        name = name.strip()[:100] or "Manual snapshot"

        database.db.execute(
            """
            INSERT INTO server_snapshots (
                guild_id, name, creator_id, created_at, snapshot_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                guild.id,
                name,
                ctx.author.id,
                now,
                json.dumps(data),
            ),
        )
        database.db.commit()

        embed = discord.Embed(
            title="Server snapshot saved",
            description=f"**Name:** {discord.utils.escape_markdown(name)}",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Members", value=str(data["member_count"] or 0))
        embed.add_field(name="Channels", value=str(data["channel_count"]))
        embed.add_field(name="Roles", value=str(data["role_count"]))
        embed.add_field(name="Boosts", value=str(data["boost_count"]))
        embed.add_field(name="Boost level", value=str(data["boost_level"]))
        embed.set_footer(text=f"Created by {ctx.author} • {now}")

        await ctx.send(embed=embed)

    # ---------------------------------------------------------
    # STAFF HANDOFF
    # ---------------------------------------------------------

    @commands.hybrid_command(
        name="handoff",
        description="Create a staff shift handoff summary.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def handoff(self, ctx):
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a server.")

        guild_id = ctx.guild.id

        active_cases = database.db.execute(
            """
            SELECT COUNT(*)
            FROM cases
            WHERE guild_id = ? AND active = 1
            """,
            (guild_id,),
        ).fetchone()[0]

        active_warnings = database.db.execute(
            """
            SELECT COUNT(*)
            FROM warnings
            WHERE guild_id = ? AND active = 1
            """,
            (guild_id,),
        ).fetchone()[0]

        pending_suggestions = database.db.execute(
            """
            SELECT COUNT(*)
            FROM suggestions
            WHERE guild_id = ? AND UPPER(status) = 'PENDING'
            """,
            (guild_id,),
        ).fetchone()[0]

        recent = database.db.execute(
            """
            SELECT created_at, action, user_name, moderator_name, reason
            FROM (
                SELECT created_at, action, user_name, moderator_name, reason
                FROM cases
                WHERE guild_id = ?

                UNION ALL

                SELECT created_at, 'WARN' AS action,
                       user_name, moderator_name, reason
                FROM warnings
                WHERE guild_id = ?
            )
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (guild_id, guild_id),
        ).fetchall()

        embed = discord.Embed(
            title="Staff shift handoff",
            description=(
                f"**Server:** {ctx.guild.name}\n"
                f"**Generated:** <t:{int(time.time())}:F>\n"
                f"**Prepared by:** {ctx.author.mention}"
            ),
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="Open moderation cases",
            value=str(active_cases),
            inline=True,
        )
        embed.add_field(
            name="Active warnings",
            value=str(active_warnings),
            inline=True,
        )
        embed.add_field(
            name="Pending suggestions",
            value=str(pending_suggestions),
            inline=True,
        )

        if recent:
            lines = []
            for row in recent:
                reason = (row["reason"] or "No reason")[:120]
                lines.append(
                    f"**{row['action']}** — "
                    f"{discord.utils.escape_markdown(row['user_name'])}\n"
                    f"Moderator: "
                    f"{discord.utils.escape_markdown(row['moderator_name'])}\n"
                    f"{discord.utils.escape_markdown(reason)} · "
                    f"{format_timestamp(row['created_at'])}"
                )

            embed.add_field(
                name="Recent moderation activity",
                value="\n\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(
                name="Recent moderation activity",
                value="No moderation activity recorded.",
                inline=False,
            )

        await ctx.send(embed=embed)

    # ---------------------------------------------------------
    # HEARTBEAT
    # ---------------------------------------------------------

    @commands.hybrid_command(
        name="heartbeat",
        description="Check Delicate's internal systems.",
    )
    @commands.has_guild_permissions(manage_guild=True)

    async def heartbeat(self, ctx):
        if ctx.guild is None:
            return await ctx.send(
                "This command can only be used in a server."
            )

        guild_id = ctx.guild.id
        healthy = "💗 healthy"
        unavailable = "♡ unavailable"
        not_configured = "♡ not configured"

        def check_setting(settings, key):
            channel_or_role_id = settings.get(key)
            if not channel_or_role_id:
                return not_configured

            if key.endswith("_channel_id"):
                channel = ctx.guild.get_channel(int(channel_or_role_id))
                return healthy if channel else unavailable

            if key.endswith("_role_id"):
                role = ctx.guild.get_role(int(channel_or_role_id))
                return healthy if role else unavailable

            return healthy

        try:
            database_ok = database.database_ready()
        except Exception:
            database_ok = False

        try:
            settings_row = database.db.execute(
                "SELECT * FROM guild_settings WHERE guild_id = ?",
                (guild_id,),
            ).fetchone()
            settings = dict(settings_row) if settings_row else {}
            settings_ok = True
        except Exception:
            settings = {}
            settings_ok = False

        database_status = healthy if database_ok else unavailable

        if settings_ok:
            logging_status = check_setting(settings, "log_channel_id")
            staff_status = check_setting(settings, "staff_role_id")
            suggestions_status = check_setting(
                settings, "suggestion_channel_id"
            )
            boosts_status = check_setting(settings, "boost_channel_id")
            rewards_status = check_setting(settings, "tag_reward_role_id")
        else:
            logging_status = unavailable
            staff_status = unavailable
            suggestions_status = unavailable
            boosts_status = unavailable
            rewards_status = unavailable

        worker_status = unavailable
        for cog in self.bot.cogs.values():
            for attribute_name in dir(cog):
                if "expir" not in attribute_name.lower():
                    continue

                try:
                    attribute = getattr(cog, attribute_name)
                    if hasattr(attribute, "is_running"):
                        worker_status = (
                            healthy if attribute.is_running() else unavailable
                        )
                        break
                except Exception:
                    continue

            if worker_status == healthy:
                break

        latency_ms = round(self.bot.latency * 1000)

        lines = [
            "♡ **DELICATE HEARTBEAT**",
            "",
            f"`database` .......... {database_status}",
            f"`logging` ........... {logging_status}",
            f"`staff` ............. {staff_status}",
            f"`suggestions` ....... {suggestions_status}",
            f"`boosts` ............ {boosts_status}",
            f"`rewards` ........... {rewards_status}",
            f"`worker` ............ {worker_status}",
            "",
            f"Gateway latency: **{latency_ms} ms**",
        ]

        await ctx.send("\n".join(lines))

    # ---------------------------------------------------------
    # FOSTER
    # ---------------------------------------------------------

    @commands.hybrid_command(
        name="foster",
        description="Assign a temporary staff guardian to a member.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def foster(
        self,
        ctx,
        member: discord.Member,
        guardian: discord.Member,
        duration: str,
    ):
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a server.")

        if member.bot:
            return await ctx.send("You cannot assign a foster guardian to a bot.")

        if guardian.bot:
            return await ctx.send("The guardian must be a server member.")

        try:
            seconds = parse_duration(duration)
        except ValueError as error:
            return await ctx.send(str(error))

        now = int(time.time())
        expires_at = now + seconds

        database.db.execute(
            """
            UPDATE foster_assignments
            SET active = 0
            WHERE guild_id = ? AND member_id = ? AND active = 1
            """,
            (ctx.guild.id, member.id),
        )

        database.db.execute(
            """
            INSERT INTO foster_assignments (
                guild_id, member_id, guardian_id, duration,
                created_at, expires_at, active
            )
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                ctx.guild.id,
                member.id,
                guardian.id,
                duration,
                now,
                expires_at,
            ),
        )
        database.db.commit()

        embed = discord.Embed(
            title="Foster guardian assigned",
            color=discord.Color.green(),
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Guardian", value=guardian.mention, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(
            name="Expires",
            value=f"<t:{expires_at}:F> (<t:{expires_at}:R>)",
            inline=False,
        )
        embed.set_footer(text=f"Assigned by {ctx.author}")

        await ctx.send(embed=embed)

    # ---------------------------------------------------------
    # ECHO
    # ---------------------------------------------------------

    @commands.hybrid_command(
        name="echo",
        description="Show a member's recent moderation history.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def echo(self, ctx, member: discord.Member):
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a server.")

        history = database.get_user_history(
            ctx.guild.id,
            member.id,
            limit=10,
        )

        embed = discord.Embed(
            title="Moderation timeline",
            description=f"Recent events for {member.mention}",
            color=discord.Color.blurple(),
        )

        if not history:
            embed.description += "\n\nNo moderation events were found."
            return await ctx.send(embed=embed)

        for row in history:
            source = row["source"]
            status = "Active" if row["active"] else "Inactive"
            title = f"{row['action']} · {source.title()} · {status}"

            reason = row["reason"] or "No reason provided"
            moderator = row["moderator_name"] or "Unknown"

            value = (
                f"**Reason:** {reason[:700]}\n"
                f"**Moderator:** {moderator}\n"
                f"**When:** {format_timestamp(row['created_at'])}"
            )

            if row["duration"]:
                value += f"\n**Duration:** {row['duration']}"

            embed.add_field(
                name=title[:256],
                value=value[:1024],
                inline=False,
            )

        embed.set_footer(text="Showing up to 10 recent events")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SpecialSystems(bot))

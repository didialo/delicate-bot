import asyncio
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

from modules.prefixes import get_prefix

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GUILD_ID = int(os.getenv("GUILD_ID", "0") or 0)
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0") or 0)
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0") or 0)
DATABASE_PATH = os.getenv("DATABASE_PATH", "moderation.db")
BOOST_CHANNEL_ID = int(os.getenv("BOOST_CHANNEL_ID", "0") or 0)

# Default prefix is handled by modules.prefixes.py:
# d!

# ============================================================
# COLORS
# ============================================================

COLOR_BAN = int(os.getenv("COLOR_BAN", "14423100"))
COLOR_KICK = int(os.getenv("COLOR_KICK", "16763187"))
COLOR_MUTE = int(os.getenv("COLOR_MUTE", "11513775"))
COLOR_WARN = int(os.getenv("COLOR_WARN", "16772724"))
COLOR_UNBAN = int(os.getenv("COLOR_UNBAN", "11976299"))
COLOR_HISTORY = int(os.getenv("COLOR_HISTORY", "13224393"))

# ============================================================
# WARNING ESCALATION
# ============================================================
#
# 3 active warnings -> 1h timeout
# 5 active warnings -> 1d timeout
# 7 active warnings -> permanent ban
#

WARN_ESCALATION = [
    (3, "MUTE", "1h"),
    (5, "MUTE", "1d"),
    (7, "BAN", "perm"),
]

# ============================================================
# ENV VALIDATION
# ============================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing from .env")

if not LOG_CHANNEL_ID:
    raise RuntimeError("LOG_CHANNEL_ID is missing from .env")

# ============================================================
# DATABASE
# ============================================================

db = sqlite3.connect(DATABASE_PATH)
db.row_factory = sqlite3.Row

db.execute(
    """
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        moderator_id INTEGER NOT NULL,
        moderator_name TEXT NOT NULL,
        reason TEXT NOT NULL,
        duration TEXT,
        expires_at INTEGER,
        created_at INTEGER NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )
    """
)

db.execute(
    """
    CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        moderator_id INTEGER NOT NULL,
        moderator_name TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        escalation_case_id INTEGER
    )
    """
)

db.commit()


# ============================================================
# DATABASE HELPERS
# ============================================================

def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def create_case(
    guild_id: int,
    action: str,
    user: discord.Member | discord.User,
    moderator: discord.Member,
    reason: str,
    duration: Optional[str] = None,
    expires_at: Optional[int] = None,
) -> int:
    cur = db.execute(
        """
        INSERT INTO cases (
            guild_id,
            action,
            user_id,
            user_name,
            moderator_id,
            moderator_name,
            reason,
            duration,
            expires_at,
            created_at,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            guild_id,
            action,
            user.id,
            str(user),
            moderator.id,
            str(moderator),
            reason,
            duration,
            expires_at,
            now_ts(),
        ),
    )

    db.commit()

    last = cur.lastrowid
    return int(last) if last is not None else 0


def close_case(case_id: int) -> None:
    db.execute(
        "UPDATE cases SET active = 0 WHERE id = ?",
        (case_id,),
    )
    db.commit()


def add_warning(
    guild_id: int,
    user: discord.Member,
    moderator: discord.Member,
    reason: str,
) -> int:
    cur = db.execute(
        """
        INSERT INTO warnings (
            guild_id,
            user_id,
            user_name,
            moderator_id,
            moderator_name,
            reason,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            guild_id,
            user.id,
            str(user),
            moderator.id,
            str(moderator),
            reason,
            now_ts(),
        ),
    )

    db.commit()

    last = cur.lastrowid
    return int(last) if last is not None else 0


def active_warning_count(guild_id: int, user_id: int) -> int:
    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM warnings
        WHERE guild_id = ?
        AND user_id = ?
        AND active = 1
        """,
        (guild_id, user_id),
    ).fetchone()

    return int(row["count"])


def get_user_history(
    guild_id: int,
    user_id: int,
    limit: int = 10,
):
    return db.execute(
        """
        SELECT *
        FROM (
            SELECT
                id,
                action,
                user_id,
                user_name,
                moderator_id,
                moderator_name,
                reason,
                duration,
                expires_at,
                created_at,
                active,
                'case' AS source
            FROM cases
            WHERE guild_id = ?
            AND user_id = ?
            AND action != 'WARN'

            UNION ALL

            SELECT
                id,
                'WARN' AS action,
                user_id,
                user_name,
                moderator_id,
                moderator_name,
                reason,
                NULL AS duration,
                NULL AS expires_at,
                created_at,
                active,
                'warning' AS source
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
        )
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (
            guild_id,
            user_id,
            guild_id,
            user_id,
            limit,
        ),
    ).fetchall()


def get_expired_cases():
    return db.execute(
        """
        SELECT *
        FROM cases
        WHERE active = 1
        AND expires_at IS NOT NULL
        AND expires_at <= ?
        ORDER BY id ASC
        """,
        (now_ts(),),
    ).fetchall()


# ============================================================
# GENERAL HELPERS
# ============================================================

def parse_duration(value: str) -> Optional[timedelta]:
    value = value.strip().lower()

    if value in {"perm", "permanent", "forever"}:
        return None

    matches = re.findall(r"(\d+)\s*([smhdw])", value)

    if not matches:
        raise ValueError(
            "Use a duration such as `30m`, `2h`, `7d`, or `1d12h`."
        )

    normalized = re.sub(r"\s+", "", value)
    rebuilt = "".join(f"{number}{unit}" for number, unit in matches)

    if normalized != rebuilt:
        raise ValueError(
            "Use a duration such as `30m`, `2h`, `7d`, or `1d12h`."
        )

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
    }

    seconds = sum(
        int(number) * multipliers[unit]
        for number, unit in matches
    )

    if seconds <= 0:
        raise ValueError("Duration must be greater than zero.")

    return timedelta(seconds=seconds)


def format_duration(value: Optional[str]) -> str:
    if not value or value.lower() in {
        "perm",
        "permanent",
        "forever",
    }:
        return "permanent"

    return value


def ts(value: Optional[int]) -> str:
    if not value:
        return "—"

    return f"<t:{value}:F>"


def color_for(action: str) -> int:
    return {
        "BAN": COLOR_BAN,
        "KICK": COLOR_KICK,
        "MUTE": COLOR_MUTE,
        "WARN": COLOR_WARN,
        "UNBAN": COLOR_UNBAN,
        "UNMUTE": COLOR_UNBAN,
        "HISTORY": COLOR_HISTORY,
    }.get(action, COLOR_HISTORY)


def emoji_for(action: str) -> str:
    return {
        "BAN": "🔨",
        "KICK": "👢",
        "MUTE": "🔇",
        "WARN": "⚠️",
        "UNBAN": "↩️",
        "UNMUTE": "↩️",
    }.get(action, "📦")


def pretty_action(action: str) -> str:
    return f"{emoji_for(action)} {action}"


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
)


# ============================================================
# PERMISSION HELPERS
# ============================================================

def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True

    if STAFF_ROLE_ID:
        if any(role.id == STAFF_ROLE_ID for role in member.roles):
            return True

    permissions = member.guild_permissions

    return (
        permissions.ban_members
        or permissions.kick_members
        or permissions.moderate_members
        or permissions.manage_messages
    )


def can_act_on(
    moderator: discord.Member,
    target: discord.Member,
) -> bool:
    if target.id in {
        moderator.id,
        moderator.guild.owner_id,
    }:
        return False

    return (
        moderator.guild_permissions.administrator
        or target.top_role < moderator.top_role
    )


async def bot_can_act_on(
    guild: discord.Guild,
    target: discord.Member,
) -> bool:
    me = guild.me

    if me is None:
        return False

    return target.top_role < me.top_role


def prefix_staff_check():
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            return False

        if not isinstance(ctx.author, discord.Member):
            return False

        return is_staff(ctx.author)

    return commands.check(predicate)


# ============================================================
# LOGGING
# ============================================================

async def get_log_channel(
    guild: discord.Guild,
):
    channel = guild.get_channel(LOG_CHANNEL_ID)

    if isinstance(channel, discord.TextChannel):
        return channel

    try:
        channel = await guild.fetch_channel(LOG_CHANNEL_ID)

        if isinstance(channel, discord.TextChannel):
            return channel

    except (
        discord.NotFound,
        discord.Forbidden,
        discord.HTTPException,
    ):
        pass

    return None


async def send_log(
    guild: discord.Guild,
    case_id: int,
    action: str,
    member: discord.Member | discord.User,
    moderator: discord.Member,
    reason: str,
    duration: Optional[str] = None,
    extra: Optional[str] = None,
):
    channel = await get_log_channel(guild)

    if channel is None:
        return

    duration_line = (
        f"\n**Duration:** `{format_duration(duration)}`"
        if duration
        else ""
    )

    extra_line = (
        f"\n**{extra}**"
        if extra
        else ""
    )

    embed = discord.Embed(
        color=color_for(action),
        description=(
            f"**{pretty_action(action)}** ・ {member.mention}\n"
            f"> **Reason:** {reason}\n"
            f"> **By:** {moderator.mention}"
            f"{duration_line}"
            f"{extra_line}"
        ),
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_footer(
        text=f"Case #{case_id}  ·  Clouddyie's Cardboard Box"
    )

    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        pass


# ============================================================
# SLASH COMMAND ERROR HELPER
# ============================================================

async def respond_error(
    interaction: discord.Interaction,
    message: str,
):
    content = f"⚠️ {message}"

    if interaction.response.is_done():
        await interaction.followup.send(
            content,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            content,
            ephemeral=True,
        )


# ============================================================
# SLASH STAFF CHECK
# ============================================================

def staff_only():
    async def predicate(
        interaction: discord.Interaction,
    ) -> bool:
        if not interaction.guild:
            return False

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            return False

        return is_staff(interaction.user)

    return app_commands.check(predicate)


# ============================================================
# ESCALATION
# ============================================================

async def apply_escalation(
    interaction: discord.Interaction,
    member: discord.Member,
    warning_count: int,
) -> Optional[int]:
    matching = [
        item
        for item in WARN_ESCALATION
        if warning_count >= item[0]
    ]

    if not matching:
        return None

    _, action, duration = max(
        matching,
        key=lambda item: item[0],
    )

    guild = interaction.guild
    moderator = interaction.user

    if guild is None:
        return None

    if not isinstance(moderator, discord.Member):
        return None

    if not await bot_can_act_on(guild, member):
        return None

    reason = (
        f"Automatic escalation after "
        f"{warning_count} active warnings."
    )

    if action == "MUTE":
        parsed = parse_duration(duration)

        if parsed is None:
            return None

        if parsed > timedelta(days=28):
            return None

        until = discord.utils.utcnow() + parsed

        try:
            await member.timeout(
                until,
                reason=reason,
            )
        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            return None

        case_id = create_case(
            guild.id,
            "MUTE",
            member,
            moderator,
            reason,
            duration,
            int(until.timestamp()),
        )

        await send_log(
            guild,
            case_id,
            "MUTE",
            member,
            moderator,
            reason,
            duration,
            extra=(
                f"Automatic escalation at "
                f"{warning_count} warnings"
            ),
        )

        return case_id

    if action == "BAN":
        try:
            await guild.ban(
                member,
                reason=reason,
                delete_message_seconds=0,
            )
        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            return None

        case_id = create_case(
            guild.id,
            "BAN",
            member,
            moderator,
            reason,
            "perm",
            None,
        )

        await send_log(
            guild,
            case_id,
            "BAN",
            member,
            moderator,
            reason,
            "perm",
            extra=(
                f"Automatic escalation at "
                f"{warning_count} warnings"
            ),
        )

        return case_id

    return None


# ============================================================
# SLASH COMMANDS
# ============================================================

@bot.tree.command(
    name="ban",
    description="Ban a member, temporarily or permanently.",
)
@app_commands.describe(
    member="Member to ban",
    duration="30m, 2h, 7d, 1d12h, or perm",
    reason="Reason",
)
@staff_only()
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    duration: str,
    reason: str,
):
    guild = interaction.guild
    moderator = interaction.user

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            interaction,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            interaction,
            "My role is not high enough to ban this member.",
        )
        return

    try:
        parsed = parse_duration(duration)
    except ValueError as exc:
        await respond_error(
            interaction,
            str(exc),
        )
        return

    expires_at = (
        int(
            (
                datetime.now(timezone.utc)
                + parsed
            ).timestamp()
        )
        if parsed
        else None
    )

    try:
        await guild.ban(
            member,
            reason=reason,
            delete_message_seconds=0,
        )
    except discord.Forbidden:
        await respond_error(
            interaction,
            "I don't have permission to ban that member.",
        )
        return
    except discord.HTTPException:
        await respond_error(
            interaction,
            "Discord returned an error while banning that member.",
        )
        return

    case_id = create_case(
        guild.id,
        "BAN",
        member,
        moderator,
        reason,
        duration,
        expires_at,
    )

    await send_log(
        guild,
        case_id,
        "BAN",
        member,
        moderator,
        reason,
        duration,
    )

    await interaction.response.send_message(
        f"🔨 Banned **{member}** for "
        f"**{format_duration(duration)}** · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


@bot.tree.command(
    name="kick",
    description="Kick a member from the server.",
)
@app_commands.describe(
    member="Member to kick",
    reason="Reason",
)
@staff_only()
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str,
):
    guild = interaction.guild
    moderator = interaction.user

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            interaction,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            interaction,
            "My role is not high enough to kick this member.",
        )
        return

    try:
        await guild.kick(
            member,
            reason=reason,
        )
    except discord.Forbidden:
        await respond_error(
            interaction,
            "I don't have permission to kick that member.",
        )
        return
    except discord.HTTPException:
        await respond_error(
            interaction,
            "Discord returned an error while kicking that member.",
        )
        return

    case_id = create_case(
        guild.id,
        "KICK",
        member,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "KICK",
        member,
        moderator,
        reason,
    )

    await interaction.response.send_message(
        f"👢 Kicked **{member}** · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


@bot.tree.command(
    name="mute",
    description="Timeout a member for a set amount of time.",
)
@app_commands.describe(
    member="Member to mute",
    duration="30m, 2h, 7d (max 28d)",
    reason="Reason",
)
@staff_only()
async def mute(
    interaction: discord.Interaction,
    member: discord.Member,
    duration: str,
    reason: str,
):
    guild = interaction.guild
    moderator = interaction.user

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            interaction,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            interaction,
            "My role is not high enough to timeout this member.",
        )
        return

    try:
        parsed = parse_duration(duration)
    except ValueError as exc:
        await respond_error(
            interaction,
            str(exc),
        )
        return

    if parsed is None:
        await respond_error(
            interaction,
            "Timeouts require a duration.",
        )
        return

    if parsed > timedelta(days=28):
        await respond_error(
            interaction,
            "Discord timeouts cannot exceed 28 days.",
        )
        return

    until = discord.utils.utcnow() + parsed

    try:
        await member.timeout(
            until,
            reason=reason,
        )
    except discord.Forbidden:
        await respond_error(
            interaction,
            "I don't have permission to timeout that member.",
        )
        return
    except discord.HTTPException:
        await respond_error(
            interaction,
            "Discord returned an error while muting that member.",
        )
        return

    case_id = create_case(
        guild.id,
        "MUTE",
        member,
        moderator,
        reason,
        duration,
        int(until.timestamp()),
    )

    await send_log(
        guild,
        case_id,
        "MUTE",
        member,
        moderator,
        reason,
        duration,
    )

    await interaction.response.send_message(
        f"🔇 Muted **{member}** for **{duration}** · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


@bot.tree.command(
    name="warn",
    description="Give a member a warning.",
)
@app_commands.describe(
    member="Member to warn",
    reason="Reason for the warning",
)
@staff_only()
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str,
):
    guild = interaction.guild
    moderator = interaction.user

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            interaction,
            "You cannot warn this member.",
        )
        return

    warning_id = add_warning(
        guild.id,
        member,
        moderator,
        reason,
    )

    count = active_warning_count(
        guild.id,
        member.id,
    )

    case_id = create_case(
        guild.id,
        "WARN",
        member,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "WARN",
        member,
        moderator,
        reason,
        extra=(
            f"Active warnings: **{count}** "
            f"· Warning #{warning_id}"
        ),
    )

    escalation_case = await apply_escalation(
        interaction,
        member,
        count,
    )

    escalation_text = ""

    if escalation_case:
        escalation = db.execute(
            """
            SELECT action, duration
            FROM cases
            WHERE id = ?
            """,
            (escalation_case,),
        ).fetchone()

        if escalation:
            escalation_text = (
                f"\n⚡ **Automatic escalation:** "
                f"{escalation['action']} "
                f"({format_duration(escalation['duration'])}) "
                f"· Case `#{escalation_case}`."
            )

    await interaction.response.send_message(
        f"⚠️ Warned **{member}**. "
        f"They now have **{count} active warning(s)** · "
        f"Warning `#{warning_id}` · "
        f"Case `#{case_id}`."
        f"{escalation_text}",
        ephemeral=True,
    )


@bot.tree.command(
    name="unban",
    description="Unban a user by Discord ID.",
)
@app_commands.describe(
    user_id="Discord user ID",
    reason="Reason",
)
@staff_only()
async def unban(
    interaction: discord.Interaction,
    user_id: str,
    reason: str = "Ban removed",
):
    guild = interaction.guild
    moderator = interaction.user

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    try:
        user = await bot.fetch_user(int(user_id))
    except (
        ValueError,
        discord.NotFound,
        discord.HTTPException,
    ):
        await respond_error(
            interaction,
            "I couldn't find that Discord user ID.",
        )
        return

    try:
        await guild.unban(
            user,
            reason=reason,
        )
    except discord.NotFound:
        await respond_error(
            interaction,
            "That user is not currently banned.",
        )
        return
    except discord.Forbidden:
        await respond_error(
            interaction,
            "I don't have permission to unban members.",
        )
        return
    except discord.HTTPException:
        await respond_error(
            interaction,
            "Discord returned an error while unbanning that user.",
        )
        return

    case_id = create_case(
        guild.id,
        "UNBAN",
        user,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "UNBAN",
        user,
        moderator,
        reason,
    )

    await interaction.response.send_message(
        f"↩️ Unbanned **{user}** · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


@bot.tree.command(
    name="unmute",
    description="Remove a member's timeout.",
)
@app_commands.describe(
    member="Member whose timeout should be removed",
    reason="Reason",
)
@staff_only()
async def unmute(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "Mute removed",
):
    guild = interaction.guild
    moderator = interaction.user

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            interaction,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            interaction,
            "My role is not high enough to remove this timeout.",
        )
        return

    try:
        await member.timeout(
            None,
            reason=reason,
        )
    except discord.Forbidden:
        await respond_error(
            interaction,
            "I don't have permission to remove timeouts.",
        )
        return
    except discord.HTTPException:
        await respond_error(
            interaction,
            "Discord returned an error while removing the timeout.",
        )
        return

    case_id = create_case(
        guild.id,
        "UNMUTE",
        member,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "UNMUTE",
        member,
        moderator,
        reason,
    )

    await interaction.response.send_message(
        f"↩️ Removed **{member}**'s timeout · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


@bot.tree.command(
    name="history",
    description="Show a member's recent moderation history.",
)
@app_commands.describe(
    member="Member whose history you want to see",
    limit="Number of entries, 1-20",
)
@staff_only()
async def history(
    interaction: discord.Interaction,
    member: discord.Member,
    limit: app_commands.Range[int, 1, 20] = 10,
):
    guild = interaction.guild

    assert guild is not None

    rows = get_user_history(
        guild.id,
        member.id,
        int(limit),
    )

    warning_count = active_warning_count(
        guild.id,
        member.id,
    )

    embed = discord.Embed(
        title=f"📦 Moderation History · {member}",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Active warnings:** `{warning_count}`\n"
            f"**Showing:** `{len(rows)}` recent entries"
        ),
        color=COLOR_HISTORY,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    if not rows:
        embed.add_field(
            name="No history",
            value=(
                "This member has no recorded "
                "moderation history."
            ),
            inline=False,
        )
    else:
        lines = []

        for row in rows:
            action = row["action"]
            when = ts(row["created_at"])

            duration = (
                f" · `{format_duration(row['duration'])}`"
                if row["duration"]
                else ""
            )

            status = (
                "active"
                if row["active"]
                else "closed"
            )

            lines.append(
                f"{emoji_for(action)} "
                f"**{action}** `#{row['id']}`"
                f"{duration} · {when}\n"
                f"> {row['reason']} · "
                f"by <@{row['moderator_id']}> · "
                f"`{status}`"
            )

        embed.add_field(
            name="Recent activity",
            value="\n\n".join(lines),
            inline=False,
        )

    embed.set_footer(
        text="Clouddyie's Cardboard Box  ·  Staff only"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True,
    )


@bot.tree.command(
    name="case",
    description="Look up a moderation case.",
)
@app_commands.describe(
    case_id="Case number",
)
@staff_only()
async def case(
    interaction: discord.Interaction,
    case_id: int,
):
    row = db.execute(
        "SELECT * FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()

    if row is None:
        await respond_error(
            interaction,
            f"Case `#{case_id}` does not exist.",
        )
        return

    embed = discord.Embed(
        title=(
            f"📦 Case #{case_id} · "
            f"{row['action']}"
        ),
        color=color_for(row["action"]),
        description=(
            f"**User:** <@{row['user_id']}> "
            f"(`{row['user_name']}`)\n"
            f"**Moderator:** <@{row['moderator_id']}>\n"
            f"**Reason:** {row['reason']}\n"
            f"**Duration:** "
            f"{format_duration(row['duration']) if row['duration'] else '—'}\n"
            f"**Created:** {ts(row['created_at'])}\n"
            f"**Expires:** {ts(row['expires_at'])}\n"
            f"**Status:** "
            f"{'active' if row['active'] else 'closed'}"
        ),
    )

    embed.set_footer(
        text="Clouddyie's Cardboard Box"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True,
    )


# ============================================================
# PREFIX COMMANDS
# ============================================================

@bot.command(name="ban")
@commands.guild_only()
@prefix_staff_check()
async def prefix_ban(
    ctx: commands.Context,
    member: discord.Member,
    duration: str,
    *,
    reason: str,
):
    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await ctx.send(
            "⚠️ You cannot moderate this member."
        )
        return

    if not await bot_can_act_on(guild, member):
        await ctx.send(
            "⚠️ My role is not high enough to ban this member."
        )
        return

    try:
        parsed = parse_duration(duration)
    except ValueError as exc:
        await ctx.send(f"⚠️ {exc}")
        return

    expires_at = (
        int(
            (
                datetime.now(timezone.utc)
                + parsed
            ).timestamp()
        )
        if parsed
        else None
    )

    try:
        await guild.ban(
            member,
            reason=reason,
            delete_message_seconds=0,
        )
    except discord.Forbidden:
        await ctx.send(
            "⚠️ I don't have permission to ban that member."
        )
        return
    except discord.HTTPException:
        await ctx.send(
            "⚠️ Discord returned an error while banning that member."
        )
        return

    case_id = create_case(
        guild.id,
        "BAN",
        member,
        moderator,
        reason,
        duration,
        expires_at,
    )

    await send_log(
        guild,
        case_id,
        "BAN",
        member,
        moderator,
        reason,
        duration,
    )

    await ctx.send(
        f"🔨 Banned **{member}** for "
        f"**{format_duration(duration)}** · "
        f"Case `#{case_id}`."
    )


@bot.command(name="kick")
@commands.guild_only()
@prefix_staff_check()
async def prefix_kick(
    ctx: commands.Context,
    member: discord.Member,
    *,
    reason: str,
):
    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await ctx.send(
            "⚠️ You cannot moderate this member."
        )
        return

    if not await bot_can_act_on(guild, member):
        await ctx.send(
            "⚠️ My role is not high enough to kick this member."
        )
        return

    try:
        await guild.kick(
            member,
            reason=reason,
        )
    except discord.Forbidden:
        await ctx.send(
            "⚠️ I don't have permission to kick that member."
        )
        return
    except discord.HTTPException:
        await ctx.send(
            "⚠️ Discord returned an error while kicking that member."
        )
        return

    case_id = create_case(
        guild.id,
        "KICK",
        member,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "KICK",
        member,
        moderator,
        reason,
    )

    await ctx.send(
        f"👢 Kicked **{member}** · "
        f"Case `#{case_id}`."
    )


@bot.command(name="mute")
@commands.guild_only()
@prefix_staff_check()
async def prefix_mute(
    ctx: commands.Context,
    member: discord.Member,
    duration: str,
    *,
    reason: str,
):
    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await ctx.send(
            "⚠️ You cannot moderate this member."
        )
        return

    if not await bot_can_act_on(guild, member):
        await ctx.send(
            "⚠️ My role is not high enough to timeout this member."
        )
        return

    try:
        parsed = parse_duration(duration)
    except ValueError as exc:
        await ctx.send(f"⚠️ {exc}")
        return

    if parsed is None:
        await ctx.send(
            "⚠️ Timeouts require a duration."
        )
        return

    if parsed > timedelta(days=28):
        await ctx.send(
            "⚠️ Discord timeouts cannot exceed 28 days."
        )
        return

    until = discord.utils.utcnow() + parsed

    try:
        await member.timeout(
            until,
            reason=reason,
        )
    except discord.Forbidden:
        await ctx.send(
            "⚠️ I don't have permission to timeout that member."
        )
        return
    except discord.HTTPException:
        await ctx.send(
            "⚠️ Discord returned an error while muting that member."
        )
        return

    case_id = create_case(
        guild.id,
        "MUTE",
        member,
        moderator,
        reason,
        duration,
        int(until.timestamp()),
    )

    await send_log(
        guild,
        case_id,
        "MUTE",
        member,
        moderator,
        reason,
        duration,
    )

    await ctx.send(
        f"🔇 Muted **{member}** for **{duration}** · "
        f"Case `#{case_id}`."
    )


@bot.command(name="warn")
@commands.guild_only()
@prefix_staff_check()
async def prefix_warn(
    ctx: commands.Context,
    member: discord.Member,
    *,
    reason: str,
):
    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await ctx.send(
            "⚠️ You cannot warn this member."
        )
        return

    warning_id = add_warning(
        guild.id,
        member,
        moderator,
        reason,
    )

    count = active_warning_count(
        guild.id,
        member.id,
    )

    case_id = create_case(
        guild.id,
        "WARN",
        member,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "WARN",
        member,
        moderator,
        reason,
        extra=(
            f"Active warnings: **{count}** "
            f"· Warning #{warning_id}"
        ),
    )

    # Prefix commands don't have an Interaction,
    # so escalation is handled directly here.

    escalation_case = None

    matching = [
        item
        for item in WARN_ESCALATION
        if count >= item[0]
    ]

    if matching and await bot_can_act_on(guild, member):
        _, action, duration = max(
            matching,
            key=lambda item: item[0],
        )

        escalation_reason = (
            f"Automatic escalation after "
            f"{count} active warnings."
        )

        if action == "MUTE":
            parsed = parse_duration(duration)

            if (
                parsed is not None
                and parsed <= timedelta(days=28)
            ):
                until = discord.utils.utcnow() + parsed

                try:
                    await member.timeout(
                        until,
                        reason=escalation_reason,
                    )

                    escalation_case = create_case(
                        guild.id,
                        "MUTE",
                        member,
                        moderator,
                        escalation_reason,
                        duration,
                        int(until.timestamp()),
                    )

                    await send_log(
                        guild,
                        escalation_case,
                        "MUTE",
                        member,
                        moderator,
                        escalation_reason,
                        duration,
                        extra=(
                            f"Automatic escalation at "
                            f"{count} warnings"
                        ),
                    )
                except (
                    discord.Forbidden,
                    discord.HTTPException,
                ):
                    pass

        elif action == "BAN":
            try:
                await guild.ban(
                    member,
                    reason=escalation_reason,
                    delete_message_seconds=0,
                )

                escalation_case = create_case(
                    guild.id,
                    "BAN",
                    member,
                    moderator,
                    escalation_reason,
                    "perm",
                    None,
                )

                await send_log(
                    guild,
                    escalation_case,
                    "BAN",
                    member,
                    moderator,
                    escalation_reason,
                    "perm",
                    extra=(
                        f"Automatic escalation at "
                        f"{count} warnings"
                    ),
                )
            except (
                discord.Forbidden,
                discord.HTTPException,
            ):
                pass

    escalation_text = ""

    if escalation_case:
        escalation = db.execute(
            """
            SELECT action, duration
            FROM cases
            WHERE id = ?
            """,
            (escalation_case,),
        ).fetchone()

        if escalation:
            escalation_text = (
                f"\n⚡ **Automatic escalation:** "
                f"{escalation['action']} "
                f"({format_duration(escalation['duration'])}) "
                f"· Case `#{escalation_case}`."
            )

    await ctx.send(
        f"⚠️ Warned **{member}**. "
        f"They now have **{count} active warning(s)** · "
        f"Warning `#{warning_id}` · "
        f"Case `#{case_id}`."
        f"{escalation_text}"
    )


@bot.command(name="unban")
@commands.guild_only()
@prefix_staff_check()
async def prefix_unban(
    ctx: commands.Context,
    user_id: str,
    *,
    reason: str = "Ban removed",
):
    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    try:
        user = await bot.fetch_user(int(user_id))
    except (
        ValueError,
        discord.NotFound,
        discord.HTTPException,
    ):
        await ctx.send(
            "⚠️ I couldn't find that Discord user ID."
        )
        return

    try:
        await guild.unban(
            user,
            reason=reason,
        )
    except discord.NotFound:
        await ctx.send(
            "⚠️ That user is not currently banned."
        )
        return
    except discord.Forbidden:
        await ctx.send(
            "⚠️ I don't have permission to unban members."
        )
        return
    except discord.HTTPException:
        await ctx.send(
            "⚠️ Discord returned an error while unbanning that user."
        )
        return

    case_id = create_case(
        guild.id,
        "UNBAN",
        user,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "UNBAN",
        user,
        moderator,
        reason,
    )

    await ctx.send(
        f"↩️ Unbanned **{user}** · "
        f"Case `#{case_id}`."
    )


@bot.command(name="unmute")
@commands.guild_only()
@prefix_staff_check()
async def prefix_unmute(
    ctx: commands.Context,
    member: discord.Member,
    *,
    reason: str = "Mute removed",
):
    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await ctx.send(
            "⚠️ You cannot moderate this member."
        )
        return

    if not await bot_can_act_on(guild, member):
        await ctx.send(
            "⚠️ My role is not high enough to remove this timeout."
        )
        return

    try:
        await member.timeout(
            None,
            reason=reason,
        )
    except discord.Forbidden:
        await ctx.send(
            "⚠️ I don't have permission to remove timeouts."
        )
        return
    except discord.HTTPException:
        await ctx.send(
            "⚠️ Discord returned an error while removing the timeout."
        )
        return

    case_id = create_case(
        guild.id,
        "UNMUTE",
        member,
        moderator,
        reason,
    )

    await send_log(
        guild,
        case_id,
        "UNMUTE",
        member,
        moderator,
        reason,
    )

    await ctx.send(
        f"↩️ Removed **{member}**'s timeout · "
        f"Case `#{case_id}`."
    )


@bot.command(name="history")
@commands.guild_only()
@prefix_staff_check()
async def prefix_history(
    ctx: commands.Context,
    member: discord.Member,
    limit: int = 10,
):
    guild = ctx.guild

    assert guild is not None

    limit = max(1, min(limit, 20))

    rows = get_user_history(
        guild.id,
        member.id,
        limit,
    )

    warning_count = active_warning_count(
        guild.id,
        member.id,
    )

    embed = discord.Embed(
        title=f"📦 Moderation History · {member}",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Active warnings:** `{warning_count}`\n"
            f"**Showing:** `{len(rows)}` recent entries"
        ),
        color=COLOR_HISTORY,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    if not rows:
        embed.add_field(
            name="No history",
            value=(
                "This member has no recorded "
                "moderation history."
            ),
            inline=False,
        )
    else:
        lines = []

        for row in rows:
            action = row["action"]
            when = ts(row["created_at"])

            duration = (
                f" · `{format_duration(row['duration'])}`"
                if row["duration"]
                else ""
            )

            status = (
                "active"
                if row["active"]
                else "closed"
            )

            lines.append(
                f"{emoji_for(action)} "
                f"**{action}** `#{row['id']}`"
                f"{duration} · {when}\n"
                f"> {row['reason']} · "
                f"by <@{row['moderator_id']}> · "
                f"`{status}`"
            )

        embed.add_field(
            name="Recent activity",
            value="\n\n".join(lines),
            inline=False,
        )

    embed.set_footer(
        text="Clouddyie's Cardboard Box  ·  Staff only"
    )

    await ctx.send(embed=embed)


@bot.command(name="case")
@commands.guild_only()
@prefix_staff_check()
async def prefix_case(
    ctx: commands.Context,
    case_id: int,
):
    row = db.execute(
        "SELECT * FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()

    if row is None:
        await ctx.send(
            f"⚠️ Case `#{case_id}` does not exist."
        )
        return

    embed = discord.Embed(
        title=(
            f"📦 Case #{case_id} · "
            f"{row['action']}"
        ),
        color=color_for(row["action"]),
        description=(
            f"**User:** <@{row['user_id']}> "
            f"(`{row['user_name']}`)\n"
            f"**Moderator:** <@{row['moderator_id']}>\n"
            f"**Reason:** {row['reason']}\n"
            f"**Duration:** "
            f"{format_duration(row['duration']) if row['duration'] else '—'}\n"
            f"**Created:** {ts(row['created_at'])}\n"
            f"**Expires:** {ts(row['expires_at'])}\n"
            f"**Status:** "
            f"{'active' if row['active'] else 'closed'}"
        ),
    )

    embed.set_footer(
        text="Clouddyie's Cardboard Box"
    )

    await ctx.send(embed=embed)


# ============================================================
# PREFIX COMMAND ERROR HANDLER
# ============================================================

@bot.event
async def on_command_error(
    ctx: commands.Context,
    error: commands.CommandError,
):
    if hasattr(ctx.command, "on_error"):
        return

    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "⚠️ You don't have permission to use that command."
        )
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            "⚠️ You don't have permission to use that command."
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"⚠️ You're missing `{error.param.name}`."
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            "⚠️ I couldn't understand one of the arguments. "
            "Make sure you mentioned the correct member."
        )
        return

    print(
        f"Prefix command error in "
        f"{getattr(ctx.command, 'name', 'unknown')}: {error}"
    )


# ============================================================
# SLASH COMMAND ERROR HANDLER
# ============================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    if isinstance(
        error,
        app_commands.CheckFailure,
    ):
        await respond_error(
            interaction,
            "You don't have permission to use that command.",
        )
        return

    print(f"Slash command error: {error}")

    await respond_error(
        interaction,
        "Something went wrong while running that command.",
    )


# ============================================================
# TEMPORARY MODERATION EXPIRATION
# ============================================================

@tasks.loop(seconds=30)
async def expiration_worker():
    for row in get_expired_cases():
        guild = bot.get_guild(row["guild_id"])

        if guild is None:
            continue

        try:
            if row["action"] == "BAN":
                try:
                    await guild.unban(
                        discord.Object(
                            id=row["user_id"]
                        ),
                        reason=(
                            f"Temporary ban expired "
                            f"| Case #{row['id']}"
                        ),
                    )
                except discord.NotFound:
                    pass

            elif row["action"] == "MUTE":
                member = guild.get_member(
                    row["user_id"]
                )

                if member:
                    try:
                        await member.timeout(
                            None,
                            reason=(
                                f"Temporary mute expired "
                                f"| Case #{row['id']}"
                            ),
                        )
                    except discord.NotFound:
                        pass

            close_case(row["id"])

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            continue


@expiration_worker.before_loop
async def before_expiration_worker():
    await bot.wait_until_ready()


# ============================================================
# COMMAND SYNC
# ============================================================

async def sync_commands():
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)

        bot.tree.copy_global_to(
            guild=guild
        )

        synced = await bot.tree.sync(
            guild=guild
        )

        print(
            f"Synced {len(synced)} command(s) "
            f"to guild {GUILD_ID}."
        )

    else:
        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} global command(s)."
        )


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="keeping things cozy ୨୧",
        ),
    )

    if bot.user is not None:
        print(
            f"Logged in as {bot.user} "
            f"(ID: {bot.user.id})"
        )
    else:
        print(
            "Logged in, but bot.user is None"
        )

    if not expiration_worker.is_running():
        expiration_worker.start()

    await sync_commands()


# ============================================================
# STARTUP
# ============================================================

async def main():
    async with bot:
        await bot.load_extension(
            "modules.boosts"
        )

        await bot.load_extension(
            "modules.prefixes"
        )

        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

from database import database
from modules import tickets


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GUILD_ID = int(os.getenv("GUILD_ID", "0") or 0)

COLOR_BAN = int(os.getenv("COLOR_BAN", "14423100"))
COLOR_KICK = int(os.getenv("COLOR_KICK", "16763187"))
COLOR_MUTE = int(os.getenv("COLOR_MUTE", "11513775"))
COLOR_WARN = int(os.getenv("COLOR_WARN", "16772724"))
COLOR_UNBAN = int(os.getenv("COLOR_UNBAN", "11976299"))
COLOR_HISTORY = int(os.getenv("COLOR_HISTORY", "13224393"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing from .env")

# ============================================================
# BOT START TIME
# ============================================================

bot_start_time = datetime.now(timezone.utc)

# ============================================================
# WARNING ESCALATION
# ============================================================

WARN_ESCALATION = [
    (3, "MUTE", "1h"),
    (5, "MUTE", "1d"),
    (7, "BAN", "perm"),
]


# ============================================================
# GENERAL HELPERS
# ============================================================

def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


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

    rebuilt = "".join(
        f"{number}{unit}"
        for number, unit in matches
    )

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
        raise ValueError(
            "Duration must be greater than zero."
        )

    return timedelta(seconds=seconds)


def format_duration(value: Optional[str]) -> str:
    if not value:
        return "permanent"

    if value.lower() in {
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
intents.message_content = True

bot = commands.Bot(
    command_prefix="d!",
    intents=intents,
    help_command=None,
)

# ============================================================
# RESPONSE HELPERS
# ============================================================

async def send_response(
    ctx: commands.Context,
    content: Optional[str] = None,
    *,
    embed: Optional[discord.Embed] = None,
    ephemeral: bool = False,
):
    """
    Sends a response for both prefix and slash/hybrid commands.
    """

    if ctx.interaction is not None:
        if ctx.interaction.response.is_done():
            kwargs = {}
            if content is not None:
                kwargs["content"] = content
            if embed is not None:
                kwargs["embed"] = embed
            kwargs["ephemeral"] = ephemeral
            return await ctx.interaction.followup.send(**kwargs)

        kwargs = {}
        if content is not None:
            kwargs["content"] = content
        if embed is not None:
            kwargs["embed"] = embed
        kwargs["ephemeral"] = ephemeral
        return await ctx.interaction.response.send_message(**kwargs)

    kwargs = {}
    if content is not None:
        kwargs["content"] = content
    if embed is not None:
        kwargs["embed"] = embed
    return await ctx.send(**kwargs)


async def respond_error(
    ctx: commands.Context,
    message: str,
):
    await send_response(
        ctx,
        f"⚠️ {message}",
        ephemeral=True,
    )


# ============================================================
# LOGGING
# ============================================================

async def get_log_channel(
    guild: discord.Guild,
) -> Optional[discord.TextChannel]:

    channel_id = database.get_guild_setting(
        guild.id,
        "log_channel_id",
    )

    if not channel_id:
        return None

    channel = guild.get_channel(channel_id)

    if isinstance(channel, discord.TextChannel):
        return channel

    try:
        channel = await guild.fetch_channel(channel_id)

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
            f"**{pretty_action(action)}** ・ "
            f"{member.mention}\n"
            f"> **Reason:** {reason}\n"
            f"> **By:** {moderator.mention}"
            f"{duration_line}"
            f"{extra_line}"
        ),
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_footer(
        text=f"Case #{case_id}  ·  {guild.name}"
    )

    try:
        await channel.send(embed=embed)

    except discord.HTTPException:
        pass

# ============================================================
# CHANNEL MODERATION
# ============================================================

@bot.hybrid_command(
    name="hide",
    description="Hide the current channel from regular members.",
)
@app_commands.default_permissions(
    manage_channels=True,
)
@app_commands.checks.has_permissions(
    manage_channels=True,
)
@commands.has_permissions(
    manage_channels=True,
)
async def hidechannel(
    ctx: commands.Context,
) -> None:
    """Hide the channel where the command was used."""

    if ctx.guild is None:
        await respond_error(
            ctx,
            "This command can only be used in a server.",
        )
        return

    if not isinstance(
        ctx.channel,
        discord.TextChannel,
    ):
        await respond_error(
            ctx,
            "This command can only be used in a text channel.",
        )
        return

    channel = ctx.channel

    everyone_overwrite = channel.overwrites_for(
        ctx.guild.default_role,
    )

    everyone_overwrite.view_channel = False

    try:
        await channel.set_permissions(
            ctx.guild.default_role,
            overwrite=everyone_overwrite,
            reason=(
                f"Channel hidden by "
                f"{ctx.author}"
            ),
        )

        # Preserve access for the configured staff role.
        staff_role_id = database.get_guild_setting(
            ctx.guild.id,
            "staff_role_id",
        )

        if staff_role_id:
            staff_role = ctx.guild.get_role(
                staff_role_id,
            )

            if staff_role is not None:
                staff_overwrite = channel.overwrites_for(
                    staff_role,
                )

                staff_overwrite.view_channel = True

                await channel.set_permissions(
                    staff_role,
                    overwrite=staff_overwrite,
                    reason=(
                        "Preserving staff access "
                        "to hidden channel"
                    ),
                )

    except discord.Forbidden:
        await respond_error(
            ctx,
            "I don't have permission to change this channel.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while hiding this channel.",
        )
        return

    await send_response(
        ctx,
        "✦ **channel hidden** ୨୧\n"
        "♡ this channel is now hidden from regular members.",
        ephemeral=True,
    )


@bot.hybrid_command(
    name="unhide",
    description="Unhide the current channel for regular members.",
)
@app_commands.default_permissions(
    manage_channels=True,
)
@app_commands.checks.has_permissions(
    manage_channels=True,
)
@commands.has_permissions(
    manage_channels=True,
)
async def unhidechannel(
    ctx: commands.Context,
):
    """Unhide the channel where the command was used."""

    if ctx.guild is None:
        await respond_error(
            ctx,
            "This command can only be used in a server.",
        )
        return

    if not isinstance(
        ctx.channel,
        discord.TextChannel,
    ):
        await respond_error(
            ctx,
            "This command can only be used in a text channel.",
        )
        return

    channel = ctx.channel

    everyone_overwrite = channel.overwrites_for(
        ctx.guild.default_role,
    )

    everyone_overwrite.view_channel = None

    try:
        await channel.set_permissions(
            ctx.guild.default_role,
            overwrite=everyone_overwrite,
            reason=(
                f"Channel unhidden by "
                f"{ctx.author}"
            ),
        )

    except discord.Forbidden:
        await respond_error(
            ctx,
            "I don't have permission to change this channel.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while unhiding this channel.",
        )
        return

    await send_response(
        ctx,
        "✦ **channel visible** ୨୧\n"
        "♡ this channel is visible to regular members again.",
        ephemeral=True,
    )


@bot.hybrid_command(
    name="lock",
    description="Lock the current channel.",
)
@app_commands.default_permissions(
    manage_channels=True,
)
@app_commands.checks.has_permissions(
    manage_channels=True,
)
@commands.has_permissions(
    manage_channels=True,
)
async def lockchannel(
    ctx: commands.Context,
):
    """Lock the channel where the command was used."""

    if ctx.guild is None:
        await respond_error(
            ctx,
            "This command can only be used in a server.",
        )
        return

    if not isinstance(
        ctx.channel,
        discord.TextChannel,
    ):
        await respond_error(
            ctx,
            "This command can only be used in a text channel.",
        )
        return

    channel = ctx.channel

    everyone_overwrite = channel.overwrites_for(
        ctx.guild.default_role,
    )

    everyone_overwrite.send_messages = False

    try:
        await channel.set_permissions(
            ctx.guild.default_role,
            overwrite=everyone_overwrite,
            reason=(
                f"Channel locked by "
                f"{ctx.author}"
            ),
        )

    except discord.Forbidden:
        await respond_error(
            ctx,
            "I don't have permission to change this channel.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while locking this channel.",
        )
        return

    await send_response(
        ctx,
        "✦ **channel locked** ୨୧\n"
        "♡ this channel is now read-only for regular members.",
        ephemeral=True,
    )


@bot.hybrid_command(
    name="unlock",
    description="Unlock the current channel.",
)
@app_commands.default_permissions(
    manage_channels=True,
)
@app_commands.checks.has_permissions(
    manage_channels=True,
)
@commands.has_permissions(
    manage_channels=True,
)
async def unlockchannel(
    ctx: commands.Context,
):
    """Unlock the channel where the command was used."""

    if ctx.guild is None:
        await respond_error(
            ctx,
            "This command can only be used in a server.",
        )
        return

    if not isinstance(
        ctx.channel,
        discord.TextChannel,
    ):
        await respond_error(
            ctx,
            "This command can only be used in a text channel.",
        )
        return

    channel = ctx.channel

    everyone_overwrite = channel.overwrites_for(
        ctx.guild.default_role,
    )

    everyone_overwrite.send_messages = None

    try:
        await channel.set_permissions(
            ctx.guild.default_role,
            overwrite=everyone_overwrite,
            reason=(
                f"Channel unlocked by "
                f"{ctx.author}"
            ),
        )

    except discord.Forbidden:
        await respond_error(
            ctx,
            "I don't have permission to change this channel.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while unlocking this channel.",
        )
        return

    await send_response(
        ctx,
        "✦ **channel unlocked** ୨୧\n"
        "♡ regular members can send messages here again.",
        ephemeral=True,
    )

# ============================================================
# PERMISSION HELPERS
# ============================================================

def is_staff_member(
    member: discord.Member,
) -> bool:

    if member.guild_permissions.administrator:
        return True

    staff_role_id = database.get_guild_setting(
        member.guild.id,
        "staff_role_id",
    )

    if staff_role_id:
        if any(
            role.id == staff_role_id
            for role in member.roles
        ):
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

    if moderator.guild_permissions.administrator:
        return True

    return target.top_role < moderator.top_role


async def bot_can_act_on(
    guild: discord.Guild,
    target: discord.Member,
) -> bool:

    me = guild.me

    if me is None:
        return False

    if target.id == guild.owner_id:
        return False

    return target.top_role < me.top_role


# ============================================================
# STAFF CHECK
# ============================================================

async def require_staff(
    ctx: commands.Context,
) -> bool:

    if ctx.guild is None:
        await respond_error(
            ctx,
            "This command can only be used in a server.",
        )
        return False

    if not isinstance(ctx.author, discord.Member):
        return False

    if not is_staff_member(ctx.author):
        await respond_error(
            ctx,
            "You do not have permission to use this command.",
        )
        return False

    return True

# ============================================================
# GENERAL COMMANDS
# ============================================================

@bot.hybrid_command(
    name="invite",
    description="Get Delicate's invite link.",
)
async def invite(ctx: commands.Context):
    invite_url = (
        "https://discord.com/oauth2/authorize"
        "?client_id=1536625530441441280"
        "&permissions=8"
        "&integration_type=0"
        "&scope=bot+applications.commands"
    )

    embed = discord.Embed(
        description=(
            "**✦ bring delicate along**\n"
            "**want me in another little corner of Discord? ♡**\n\n"
            f"[**invite delicate**]({invite_url})\n\n"
            "**i'll be ready to help with moderation, server setup, "
            "and keeping things cozy. ୨୧**"
        )
    )

    embed.set_footer(
        text="delicate · keeping things cozy ୨୧"
    )

    await ctx.send(embed=embed)
# ============================================================
# HELP
# ============================================================

@bot.hybrid_command(
    name="help",
    description="Show Delicate's commands and features.",
)
async def help_command(
    ctx: commands.Context,
):
    """Show Delicate's commands automatically."""

    commands_list = []

    for command in sorted(
        bot.walk_commands(),
        key=lambda cmd: cmd.name.lower(),
    ):
        if command.hidden:
            continue

        description = (
            command.description
            or "No description available."
        )

        commands_list.append(
            f"`/{command.name}` · `d!{command.name}`\n"
            f"> {description}"
        )

    if not commands_list:
        commands_list.append(
            "No commands are currently available."
        )

    embed = discord.Embed(
        title="✦ delicate",
        description=(
            "a little moderation bot made to keep things "
            "safe, calm, and cozy. ୨୧\n\n"
            "### commands\n"
            + "\n\n".join(commands_list)
        ),
        color=COLOR_HISTORY,
    )

    embed.set_footer(
        text="delicate · keeping things cozy ୨୧"
    )

    await send_response(
        ctx,
        embed=embed,
    )

# ============================================================
# PING
# ============================================================

@bot.hybrid_command(
    name="ping",
    description="Check Delicate's connection and system status.",
)
async def ping(ctx: commands.Context) -> None:
    """Show Delicate's current connection and system information."""

    import platform
    import time
    import psutil

    start = time.perf_counter()

    # --------------------------------------------------------
    # Gateway latency
    # --------------------------------------------------------

    gateway_ms = round(bot.latency * 1000)

    # --------------------------------------------------------
    # Uptime
    # --------------------------------------------------------

    uptime_delta = (
        datetime.now(timezone.utc) - bot_start_time
    )

    total_seconds = max(
        0,
        int(uptime_delta.total_seconds()),
    )

    days, remainder = divmod(
        total_seconds,
        86400,
    )
    hours, remainder = divmod(
        remainder,
        3600,
    )
    minutes, seconds = divmod(
        remainder,
        60,
    )

    uptime_parts = []

    if days:
        uptime_parts.append(f"{days}d")

    if hours or days:
        uptime_parts.append(f"{hours}h")

    if minutes or hours or days:
        uptime_parts.append(f"{minutes}m")

    uptime_parts.append(f"{seconds}s")

    uptime = " ".join(uptime_parts)

    # --------------------------------------------------------
    # Delicate process memory
    # --------------------------------------------------------

    process = psutil.Process()

    memory_mb = (
        process.memory_info().rss
        / (1024 ** 2)
    )

    # --------------------------------------------------------
    # System information
    # --------------------------------------------------------

    processor = (
        platform.processor()
        or platform.uname().processor
        or platform.machine()
        or "Unknown processor"
    )

    operating_system = (
        f"{platform.system()} "
        f"{platform.release()}"
    )

    python_version = platform.python_version()

    # --------------------------------------------------------
    # Processing time
    # --------------------------------------------------------

    response_ms = max(
        1,
        round(
            (time.perf_counter() - start) * 1000
        ),
    )

    # --------------------------------------------------------
    # Embed
    # --------------------------------------------------------

    embed = discord.Embed(
        color=0xE8DFF5,
        description=(
            "📦 **delicate · little status box ୨୧**\n\n"
            "♡ everything seems to be packed safely.\n\n"
            "╭───────────────╮\n"
            f"│ ✦ **processing** `{response_ms}ms`\n"
            f"│ ♡ **gateway**    `{gateway_ms}ms`\n"
            f"│ ୨୧ **uptime**     `{uptime}`\n"
            "╰───────────────╯"
        ),
        timestamp=datetime.now(timezone.utc),
    )

    if bot.user is not None:
        embed.set_author(
            name="delicate",
            icon_url=bot.user.display_avatar.url,
        )

    embed.add_field(
        name="♡ runtime",
        value=(
            f"`Python {python_version}`\n"
            f"`discord.py {discord.__version__}`"
        ),
        inline=True,
    )

    embed.add_field(
        name="✦ memory",
        value=f"`{memory_mb:.2f} MB used`",
        inline=True,
    )

    embed.add_field(
        name="୨୧ environment",
        value=(
            f"`{processor}`\n"
            f"`{operating_system}`"
        ),
        inline=False,
    )

    embed.set_footer(
        text="delicate  ·  systems cozy & operational  ♡"
    )

    await send_response(
        ctx,
        embed=embed,
    )

# ============================================================
# SETTINGS
# ============================================================

@bot.hybrid_command(
    name="setlog",
    description="Set the moderation log channel.",
)
@app_commands.describe(
    channel="Channel where moderation logs should be sent.",
)
@commands.has_permissions(administrator=True)
async def setlog(
    ctx: commands.Context,
    channel: discord.TextChannel,
):
    if ctx.guild is None:
        return

    database.set_guild_setting(
        ctx.guild.id,
        "log_channel_id",
        channel.id,
    )

    await send_response(
        ctx,
        f"✅ Moderation logs will now be sent to "
        f"{channel.mention}.",
        ephemeral=True,
    )


@bot.hybrid_command(
    name="setboost",
    description="Set the boost notification channel.",
)
@app_commands.describe(
    channel="Channel where boost notifications should be sent.",
)
@commands.has_permissions(administrator=True)
async def setboost(
    ctx: commands.Context,
    channel: discord.TextChannel,
):
    if ctx.guild is None:
        return

    database.set_guild_setting(
        ctx.guild.id,
        "boost_channel_id",
        channel.id,
    )

    await send_response(
        ctx,
        f"✅ Boost notifications will now use "
        f"{channel.mention}.",
        ephemeral=True,
    )


@bot.hybrid_command(
    name="setstaff",
    description="Set the staff role.",
)
@app_commands.describe(
    role="Role that should be treated as staff.",
)
@commands.has_permissions(administrator=True)
async def setstaff(
    ctx: commands.Context,
    role: discord.Role,
):
    if ctx.guild is None:
        return

    database.set_guild_setting(
        ctx.guild.id,
        "staff_role_id",
        role.id,
    )

    await send_response(
        ctx,
        f"✅ Staff role set to {role.mention}.",
        ephemeral=True,
    )


@bot.hybrid_command(
    name="settings",
    description="Show Delicate's settings for this server.",
)
@commands.has_permissions(administrator=True)
async def settings(
    ctx: commands.Context,
):
    if ctx.guild is None:
        return

    guild_id = ctx.guild.id

    log_id = database.get_guild_setting(
        guild_id,
        "log_channel_id",
    )

    boost_id = database.get_guild_setting(
        guild_id,
        "boost_channel_id",
    )

    staff_id = database.get_guild_setting(
        guild_id,
        "staff_role_id",
    )

    embed = discord.Embed(
        title=f"⚙️ Delicate Settings · {ctx.guild.name}",
        color=COLOR_HISTORY,
    )

    embed.add_field(
        name="Moderation logs",
        value=(
            f"<#{log_id}>"
            if log_id
            else "Not configured"
        ),
        inline=False,
    )

    embed.add_field(
        name="Boost channel",
        value=(
            f"<#{boost_id}>"
            if boost_id
            else "Not configured"
        ),
        inline=False,
    )

    embed.add_field(
        name="Staff role",
        value=(
            f"<@&{staff_id}>"
            if staff_id
            else "Using Discord moderation permissions"
        ),
        inline=False,
    )

    ticket_id = database.get_guild_setting(
        guild_id,
    
        "ticket_channel_id",
    )

    embed.add_field(
        name="Ticket panel",
        value=(
            f"<#{ticket_id}>"
            if ticket_id
            else "Not configured"
        ),
        inline=False,
    )

    await send_response(
        ctx,
        embed=embed,
        ephemeral=True,
    )


# ============================================================
# WARNING ESCALATION
# ============================================================

async def apply_escalation(
    ctx: commands.Context,
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

    guild = ctx.guild
    moderator = ctx.author

    if guild is None:
        return None

    if not isinstance(moderator, discord.Member):
        return None

    if not await bot_can_act_on(
        guild,
        member,
    ):
        return None

    reason = (
        "Automatic escalation after "
        f"{warning_count} active warnings."
    )

    # --------------------------------------------------------
    # AUTOMATIC MUTE
    # --------------------------------------------------------

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

        case_id = database.create_case(
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
                "Automatic escalation at "
                f"{warning_count} warnings"
            ),
        )

        return case_id

    # --------------------------------------------------------
    # AUTOMATIC BAN
    # --------------------------------------------------------

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

        case_id = database.create_case(
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
                "Automatic escalation at "
                f"{warning_count} warnings"
            ),
        )

        return case_id

    return None


# ============================================================
# BAN
# ============================================================

@bot.hybrid_command(
    name="ban",
    description="Ban a member temporarily or permanently.",
)
@app_commands.describe(
    member="Member to ban",
    duration="30m, 2h, 7d, 1d12h, or perm",
    reason="Reason",
)
async def ban(
    ctx: commands.Context,
    member: discord.Member,
    duration: str,
    reason: str,
):
    if not await require_staff(ctx):
        return

    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            ctx,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            ctx,
            "My role is not high enough to ban this member.",
        )
        return

    try:
        parsed = parse_duration(duration)

    except ValueError as exc:
        await respond_error(ctx, str(exc))
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
            ctx,
            "I don't have permission to ban that member.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while banning that member.",
        )
        return

    case_id = database.create_case(
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

    await send_response(
        ctx,
        f"🔨 Banned **{member}** for "
        f"**{format_duration(duration)}** · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


# ============================================================
# KICK
# ============================================================

@bot.hybrid_command(
    name="kick",
    description="Kick a member from the server.",
)
@app_commands.describe(
    member="Member to kick",
    reason="Reason",
)
async def kick(
    ctx: commands.Context,
    member: discord.Member,
    reason: str,
):
    if not await require_staff(ctx):
        return

    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            ctx,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            ctx,
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
            ctx,
            "I don't have permission to kick that member.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while kicking that member.",
        )
        return

    case_id = database.create_case(
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

    await send_response(
        ctx,
        f"👢 Kicked **{member}** · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


# ============================================================
# MUTE
# ============================================================

@bot.hybrid_command(
    name="mute",
    description="Timeout a member.",
)
@app_commands.describe(
    member="Member to mute",
    duration="30m, 2h, 7d (max 28d)",
    reason="Reason",
)
async def mute(
    ctx: commands.Context,
    member: discord.Member,
    duration: str,
    reason: str,
):
    if not await require_staff(ctx):
        return

    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            ctx,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            ctx,
            "My role is not high enough to timeout this member.",
        )
        return

    try:
        parsed = parse_duration(duration)

    except ValueError as exc:
        await respond_error(ctx, str(exc))
        return

    if parsed is None:
        await respond_error(
            ctx,
            "Timeouts require a duration.",
        )
        return

    if parsed > timedelta(days=28):
        await respond_error(
            ctx,
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
            ctx,
            "I don't have permission to timeout that member.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while muting that member.",
        )
        return

    case_id = database.create_case(
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

    await send_response(
        ctx,
        f"🔇 Muted **{member}** for "
        f"**{duration}** · Case `#{case_id}`.",
        ephemeral=True,
    )


# ============================================================
# WARN
# ============================================================

@bot.hybrid_command(
    name="warn",
    description="Give a member a warning.",
)
@app_commands.describe(
    member="Member to warn",
    reason="Reason for the warning",
)
async def warn(
    ctx: commands.Context,
    member: discord.Member,
    reason: str,
):
    if not await require_staff(ctx):
        return

    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            ctx,
            "You cannot warn this member.",
        )
        return

    warning_id = database.add_warning(
        guild.id,
        member,
        moderator,
        reason,
    )

    count = database.active_warning_count(
        guild.id,
        member.id,
    )

    case_id = database.create_case(
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
            f"Active warnings: **{count}**"
            f"  ·  Warning #{warning_id}"
        ),
    )

    escalation_case = await apply_escalation(
        ctx,
        member,
        count,
    )

    escalation_text = ""

    if escalation_case:
        escalation = database.db.execute(
            """
            SELECT action, duration
            FROM cases
            WHERE id = ?
            """,
            (escalation_case,),
        ).fetchone()

        if escalation is not None:
            escalation_text = (
                f"\n⚡ **Automatic escalation:** "
                f"{escalation['action']} "
                f"({format_duration(escalation['duration'])}) "
                f"· Case `#{escalation_case}`."
            )

            # Your database already has this column.
            database.db.execute(
                """
                UPDATE warnings
                SET escalation_case_id = ?
                WHERE id = ?
                """,
                (
                    escalation_case,
                    warning_id,
                ),
            )
            database.db.commit()

    await send_response(
        ctx,
        f"⚠️ Warned **{member}**. "
        f"They now have **{count} active warning(s)** "
        f"· Warning `#{warning_id}` "
        f"· Case `#{case_id}`."
        f"{escalation_text}",
        ephemeral=True,
    )


# ============================================================
# UNBAN
# ============================================================

@bot.hybrid_command(
    name="unban",
    description="Unban a user by Discord ID.",
)
@app_commands.describe(
    user_id="Discord user ID",
    reason="Reason",
)
async def unban(
    ctx: commands.Context,
    user_id: str,
    reason: str = "Ban removed",
):
    if not await require_staff(ctx):
        return

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
        await respond_error(
            ctx,
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
            ctx,
            "That user is not currently banned.",
        )
        return

    except discord.Forbidden:
        await respond_error(
            ctx,
            "I don't have permission to unban members.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while unbanning that user.",
        )
        return

    case_id = database.create_case(
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

    await send_response(
        ctx,
        f"↩️ Unbanned **{user}** · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


# ============================================================
# UNMUTE
# ============================================================

@bot.hybrid_command(
    name="unmute",
    description="Remove a member's timeout.",
)
@app_commands.describe(
    member="Member whose timeout should be removed",
    reason="Reason",
)
async def unmute(
    ctx: commands.Context,
    member: discord.Member,
    reason: str = "Mute removed",
):
    if not await require_staff(ctx):
        return

    guild = ctx.guild
    moderator = ctx.author

    assert guild is not None
    assert isinstance(moderator, discord.Member)

    if not can_act_on(moderator, member):
        await respond_error(
            ctx,
            "You cannot moderate this member.",
        )
        return

    if not await bot_can_act_on(guild, member):
        await respond_error(
            ctx,
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
            ctx,
            "I don't have permission to remove timeouts.",
        )
        return

    except discord.HTTPException:
        await respond_error(
            ctx,
            "Discord returned an error while removing the timeout.",
        )
        return

    case_id = database.create_case(
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

    await send_response(
        ctx,
        f"↩️ Removed **{member}**'s timeout · "
        f"Case `#{case_id}`.",
        ephemeral=True,
    )


# ============================================================
# HISTORY
# ============================================================

@bot.hybrid_command(
    name="history",
    description="Show a member's moderation history.",
)
@app_commands.describe(
    member="Member whose history you want to see",
    limit="Number of entries, 1-20",
)
async def history(
    ctx: commands.Context,
    member: discord.Member,
    limit: int = 10,
):
    if not await require_staff(ctx):
        return

    if limit < 1 or limit > 20:
        await respond_error(
            ctx,
            "Limit must be between 1 and 20.",
        )
        return

    guild = ctx.guild

    assert guild is not None

    rows = database.get_user_history(
        guild.id,
        member.id,
        int(limit),
    )

    warning_count = database.active_warning_count(
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
        url=member.display_avatar.url,
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
                f"**{action}** "
                f"`#{row['id']}`"
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
        text=f"{guild.name}  ·  Staff only"
    )

    await send_response(
        ctx,
        embed=embed,
        ephemeral=True,
    )


# ============================================================
# CASE
# ============================================================

@bot.hybrid_command(
    name="case",
    description="Look up a moderation case.",
)
@app_commands.describe(
    case_id="Case number",
)
async def case(
    ctx: commands.Context,
    case_id: int,
):
    if not await require_staff(ctx):
        return

    guild = ctx.guild

    assert guild is not None

    row = database.db.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        AND guild_id = ?
        """,
        (
            case_id,
            guild.id,
        ),
    ).fetchone()

    if row is None:
        await respond_error(
            ctx,
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
            f"**User:** "
            f"<@{row['user_id']}> "
            f"(`{row['user_name']}`)\n"
            f"**Moderator:** "
            f"<@{row['moderator_id']}>\n"
            f"**Reason:** "
            f"{row['reason']}\n"
            f"**Duration:** "
            f"{format_duration(row['duration']) if row['duration'] else '—'}\n"
            f"**Created:** "
            f"{ts(row['created_at'])}\n"
            f"**Expires:** "
            f"{ts(row['expires_at'])}\n"
            f"**Status:** "
            f"{'active' if row['active'] else 'closed'}"
        ),
    )

    embed.set_footer(
        text=guild.name
    )

    await send_response(
        ctx,
        embed=embed,
        ephemeral=True,
    )


# ============================================================
# EXPIRATION WORKER
# ============================================================

@tasks.loop(seconds=30)
async def expiration_worker():

    for row in database.get_expired_cases():
        guild = bot.get_guild(row["guild_id"])

        if guild is None:
            continue

        try:

            # ------------------------------------------------
            # TEMPORARY BAN
            # ------------------------------------------------

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

            # ------------------------------------------------
            # TEMPORARY MUTE
            # ------------------------------------------------

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

            database.close_case(
                row["id"]
            )

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            continue


@expiration_worker.before_loop
async def before_expiration_worker():
    await bot.wait_until_ready()


# ============================================================
# PREFIX COMMAND ERROR HANDLER
# ============================================================

@bot.event
async def on_command_error(
    ctx: commands.Context,
    error: commands.CommandError,
):

    if isinstance(
        error,
        commands.CommandNotFound,
    ):
        return

    if isinstance(
        error,
        commands.MissingPermissions,
    ):
        await respond_error(
            ctx,
            "You don't have permission to use that command.",
        )
        return

    if isinstance(
        error,
        commands.MissingRequiredArgument,
    ):
        await respond_error(
            ctx,
            "You're missing a required argument. "
            f"Try `d!{ctx.command.name if ctx.command else 'help'} --help`.",
        )
        return

    if isinstance(
        error,
        commands.BadArgument,
    ):
        await respond_error(
            ctx,
            "One of the arguments you provided is invalid.",
        )
        return

    print(
        f"Command error in "
        f"{getattr(ctx.command, 'name', 'unknown')}: "
        f"{error}"
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
        app_commands.MissingPermissions,
    ):
        message = (
            "⚠️ You don't have permission "
            "to use that command."
        )

    elif isinstance(
        error,
        app_commands.CheckFailure,
    ):
        message = (
            "⚠️ You don't have permission "
            "to use that command."
        )

    elif isinstance(
        error,
        app_commands.TransformerError,
    ):
        message = (
            "⚠️ One of the arguments you provided "
            "is invalid."
        )

    else:
        print(
            "Slash command error: "
            f"{error}"
        )
        message = (
            "⚠️ Something went wrong while "
            "running that command."
        )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                message,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
            )

    except discord.HTTPException:
        pass

# ============================================================
# INVITE / GUILD JOIN DM
# ============================================================

async def find_guild_inviter(
    guild: discord.Guild,
) -> Optional[discord.User | discord.Member]:
    """Find the user who added Delicate using the audit log."""

    if bot.user is None:
        return None

    try:
        async for entry in guild.audit_logs(
            limit=10,
            action=discord.AuditLogAction.bot_add,
        ):
            if entry.target is None:
                continue

            if getattr(entry.target, "id", None) != bot.user.id:
                continue

            if entry.user is None:
                continue

            if entry.created_at < (
                discord.utils.utcnow() - timedelta(minutes=2)
            ):
                continue

            return entry.user

    except (
        discord.Forbidden,
        discord.HTTPException,
    ):
        return None

    return None


async def send_guild_join_dm(
    guild: discord.Guild,
    inviter: discord.User | discord.Member,
) -> None:
    """Send Delicate's private welcome DM to the person who added it."""

    embed = discord.Embed(
        title="✦ delicate is here",
        description=(
            f"hey, **{inviter.display_name}** ♡\n\n"
            f"thank you for bringing me into **{guild.name}**!\n"
            "i'm ready to help keep things safe, calm, and cozy.\n\n"
            "**getting started**\n"
            "`d!settings` — view the server settings\n"
            "`d!setlog` — choose a moderation log channel\n"
            "`d!setboost` — choose a boost notification channel\n"
            "`d!setstaff` — choose the staff role\n\n"
            "most setup commands require administrator permissions.\n"
            "you can also use the matching slash commands."
        ),
        color=COLOR_HISTORY,
    )

    embed.set_footer(
        text="delicate · keeping things cozy ୨୧"
    )

    try:
        await inviter.send(embed=embed)

        print(
            f"Sent invite DM to {inviter} for {guild.name}"
        )

    except (
        discord.Forbidden,
        discord.HTTPException,
    ):
        print(
            f"Could not DM inviter {inviter} for {guild.name}"
        )

        # ============================================================
# TEST INVITE DM
# ============================================================

@bot.hybrid_command(
    name="testinvitedm",
    description="Test Delicate's server invite welcome DM.",
)
@commands.is_owner()
async def testinvitedm(ctx: commands.Context):
    """Test the invite welcome DM without inviting Delicate."""

    if ctx.guild is None:
        if ctx.interaction is not None:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(
                    "⚠️ This command must be used in a server.",
                    ephemeral=True,
                )
        else:
            await ctx.send(
                "⚠️ This command must be used in a server."
            )

        return

    # Acknowledge slash interactions immediately.
    if ctx.interaction is not None:
        await ctx.interaction.response.defer(
            ephemeral=True,
        )

    await send_guild_join_dm(
        ctx.guild,
        ctx.author,
    )

    if ctx.interaction is not None:
        await ctx.interaction.followup.send(
            "✦ Invite DM test sent to your DMs.",
            ephemeral=True,
        )
    else:
        await ctx.send(
            "✦ Invite DM test sent to your DMs."
        )


# ============================================================
# REAL GUILD JOIN
# ============================================================

@bot.event
async def on_guild_join(guild: discord.Guild):
    """DM the person who invited Delicate."""

    print(
        f"Joined guild {guild.name} "
        f"(ID: {guild.id})"
    )

    inviter: Optional[discord.User | discord.Member] = None

    # Give Discord a moment to create the audit-log entry.
    for _ in range(5):
        inviter = await find_guild_inviter(guild)

        if inviter is not None:
            break

        await asyncio.sleep(2)

    if inviter is None:
        print(
            f"Could not determine who invited Delicate "
            f"to {guild.name}."
        )
        return

    await send_guild_join_dm(
        guild,
        inviter,
    )

# ============================================================
# BOT EVENTS
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
 

# ============================================================
# SETUP HOOK
# ============================================================

@bot.event
async def setup_hook():
    await tickets.setup(bot)

    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)

        bot.tree.clear_commands(
            guild=guild,
        )

        await bot.tree.sync(
            guild=guild,
        )

        print(
            f"Cleared stale guild commands from "
            f"guild {GUILD_ID}."
        )

    synced = await bot.tree.sync()

    print(
        f"Synced {len(synced)} "
        f"global command(s)."
    )

# ============================================================
# ABOUT
# ============================================================

@bot.hybrid_command(
    name="about",
    description="A little bit about Delicate.",
)
async def about_command(ctx: commands.Context) -> None:
    """Show Delicate's generated information card."""

    guild_count = len(bot.guilds)

    user_count = sum(
        guild.member_count or 0
        for guild in bot.guilds
    )

    command_count = len(bot.commands)

    latency = (
        round(bot.latency * 1000)
        if bot.latency is not None
        else 0
    )

    # --------------------------------------------------------
    # DATABASE STATISTICS
    # --------------------------------------------------------

    try:
        case_row = database.db.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(active), 0) AS active
            FROM cases
            """
        ).fetchone()

        warning_row = database.db.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(active), 0) AS active
            FROM warnings
            """
        ).fetchone()

        tracked_users_row = database.db.execute(
            """
            SELECT COUNT(DISTINCT user_id) AS count
            FROM (
                SELECT user_id FROM cases
                UNION
                SELECT user_id FROM warnings
            )
            """
        ).fetchone()

        database_status = "online"

        total_cases = int(
            case_row["total"] or 0
            if case_row
            else 0
        )

        active_cases = int(
            case_row["active"] or 0
            if case_row
            else 0
        )

        total_warnings = int(
            warning_row["total"] or 0
            if warning_row
            else 0
        )

        active_warnings = int(
            warning_row["active"] or 0
            if warning_row
            else 0
        )

        tracked_users = int(
            tracked_users_row["count"] or 0
            if tracked_users_row
            else 0
        )

    except Exception:
        database_status = "error"

        total_cases = 0
        active_cases = 0
        total_warnings = 0
        active_warnings = 0
        tracked_users = 0

    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

    embed = discord.Embed(
        color=0xE8DFF5,
        description=(
            "✦ **delicate** ୨୧\n\n"
            "♡ a little information about me.\n"
            "୨୧ built to keep things safe, simple, and sweet.\n\n"

            "╭───────────────╮\n"
            f"│ ✦ **servers**  `{guild_count:,}`\n"
            f"│ ♡ **users**    `{user_count:,}`\n"
            f"│ ୨୧ **commands** `{command_count:,}`\n"
            f"│ ✦ **latency**  `{latency}ms`\n"
            "╰───────────────╯"
        ),
        timestamp=datetime.now(timezone.utc),
    )

    if bot.user is not None:
        embed.set_author(
            name="delicate",
            icon_url=bot.user.display_avatar.url,
        )

    embed.add_field(
        name="♡ about",
        value=(
            "Delicate is a moderation bot focused on "
            "keeping servers organized, protected, and easy to manage."
        ),
        inline=False,
    )

    embed.add_field(
        name="✦ moderation database",
        value=(
            f"**Cases:** `{total_cases:,}`\n"
            f"**Active cases:** `{active_cases:,}`\n"
            f"**Warnings:** `{total_warnings:,}`\n"
            f"**Active warnings:** `{active_warnings:,}`\n"
            f"**Tracked users:** `{tracked_users:,}`"
        ),
        inline=False,
    )

    embed.add_field(
        name="୨୧ database status",
        value=f"`{database_status}`",
        inline=True,
    )

    embed.add_field(
        name="✦ developer",
        value="`Clouddyie`",
        inline=True,
    )

    embed.add_field(
        name="୨୧ library",
        value="`discord.py`",
        inline=True,
    )

    embed.add_field(
        name="♡ command style",
        value="`hybrid`",
        inline=True,
    )

    embed.set_footer(
        text="delicate  ·  made softly, built carefully  ♡"
    )

    await send_response(
        ctx,
        embed=embed,
    )

# ============================================================
# MAIN
# ============================================================

async def main():

    async with bot:
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

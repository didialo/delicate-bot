import io
import re
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from database import database


TICKET_TOPIC_PREFIX = "delicate-ticket:"


class TicketPanelView(discord.ui.View):
    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="open a ticket",
        style=discord.ButtonStyle.primary,
        emoji="🎟️",
        custom_id="delicate:ticket:open",
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.cog.open_ticket(interaction)


class TicketCloseView(discord.ui.View):
    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="close ticket",
        style=discord.ButtonStyle.danger,
        emoji="×",
        custom_id="delicate:ticket:close",
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.cog.close_ticket(interaction)


class Tickets(commands.Cog):
    """Private support tickets with transcript logging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        database.db.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_settings (
                guild_id INTEGER PRIMARY KEY,
                panel_channel_id INTEGER
            )
            """
        )
        database.db.commit()

        self.bot.add_view(TicketPanelView(self))
        self.bot.add_view(TicketCloseView(self))

        print("🎟️ Tickets cog loaded.")

    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------

    def get_panel_channel_id(
        self,
        guild_id: int,
    ) -> Optional[int]:
        row = database.db.execute(
            """
            SELECT panel_channel_id
            FROM ticket_settings
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

        if row is None:
            return None

        if row["panel_channel_id"] is None:
            return None

        return int(row["panel_channel_id"])

    def set_panel_channel_id(
        self,
        guild_id: int,
        channel_id: int,
    ):
        database.db.execute(
            """
            INSERT INTO ticket_settings (
                guild_id,
                panel_channel_id
            )
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET panel_channel_id = excluded.panel_channel_id
            """,
            (
                guild_id,
                channel_id,
            ),
        )

        database.db.commit()

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def get_staff_role(
        self,
        guild: discord.Guild,
    ) -> Optional[discord.Role]:
        role_id = database.get_guild_setting(
            guild.id,
            "staff_role_id",
        )

        if not role_id:
            return None

        return guild.get_role(role_id)

    def find_open_ticket(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> Optional[discord.TextChannel]:
        topic = f"{TICKET_TOPIC_PREFIX}{user_id}"

        for channel in guild.text_channels:
            if channel.topic == topic:
                return channel

        return None

    @staticmethod
    def safe_channel_name(
        user: discord.User | discord.Member,
    ) -> str:
        name = user.display_name.lower()

        name = re.sub(
            r"[^a-z0-9]+",
            "-",
            name,
        ).strip("-")

        name = name[:35] or "user"

        return f"ticket-{name}"

    def panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="✦ need a little help?",
            description=(
                "something going wrong? need a hand? ♡\n\n"
                "open a private ticket and someone from the "
                "staff team will be with you soon.\n\n"
                "`♡` only you and the staff team can see your ticket\n"
                "`♡` please explain what you need when you open one"
            ),
            color=0xC9A66B,
        )

        embed.set_footer(
            text="delicate · keeping things cozy ୨୧"
        )

        return embed

    def ticket_embed(
        self,
        member: discord.User | discord.Member,
    ) -> discord.Embed:
        embed = discord.Embed(
            title="✦ welcome in",
            description=(
                f"hi {member.mention}! ♡\n\n"
                "someone from the staff team will be with you soon.\n"
                "please explain what you need help with and include "
                "any useful details. ୨୧"
            ),
            color=0xC9A66B,
        )

        embed.set_footer(
            text="delicate · keeping things cozy ୨୧"
        )

        return embed

    # ---------------------------------------------------------
    # OPEN TICKET
    # ---------------------------------------------------------

    async def open_ticket(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "⚠️ Tickets can only be opened inside a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        guild = interaction.guild
        member = interaction.user

        existing = self.find_open_ticket(
            guild,
            member.id,
        )

        if existing is not None:
            await interaction.followup.send(
                f"You already have an open ticket: "
                f"{existing.mention}",
                ephemeral=True,
            )
            return

        panel_id = self.get_panel_channel_id(
            guild.id
        )

        panel_channel = (
            guild.get_channel(panel_id)
            if panel_id
            else None
        )

        if not isinstance(
            panel_channel,
            discord.TextChannel,
        ):
            await interaction.followup.send(
                "⚠️ Tickets haven't been configured yet.",
                ephemeral=True,
            )
            return

        staff_role = self.get_staff_role(guild)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
            ),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
        }

        if staff_role is not None:
            overwrites[staff_role] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                    manage_messages=True,
                )
            )

        try:
            channel = await guild.create_text_channel(
                name=self.safe_channel_name(member),
                category=panel_channel.category,
                topic=f"{TICKET_TOPIC_PREFIX}{member.id}",
                overwrites=overwrites,
                reason=(
                    f"Ticket opened by "
                    f"{member} ({member.id})"
                ),
            )

            await channel.send(
                content=member.mention,
                embed=self.ticket_embed(member),
                view=TicketCloseView(self),
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "⚠️ I don't have permission to create "
                "private ticket channels.",
                ephemeral=True,
            )
            return

        except discord.HTTPException:
            await interaction.followup.send(
                "⚠️ Discord returned an error while "
                "creating the ticket.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"✦ your ticket is ready: {channel.mention}",
            ephemeral=True,
        )

    # ---------------------------------------------------------
    # TRANSCRIPT
    # ---------------------------------------------------------

    async def make_transcript(
        self,
        channel: discord.TextChannel,
    ) -> str:
        lines = [
            "Delicate ticket transcript",
            f"Server: {channel.guild.name} ({channel.guild.id})",
            f"Channel: #{channel.name} ({channel.id})",
            "=" * 72,
        ]

        async for message in channel.history(
            limit=None,
            oldest_first=True,
        ):
            timestamp = message.created_at.isoformat()

            author = (
                f"{message.author} "
                f"({message.author.id})"
            )

            content = (
                message.clean_content
                or "[no text]"
            )

            lines.append(
                f"[{timestamp}] {author}: {content}"
            )

            for attachment in message.attachments:
                lines.append(
                    f"    attachment: {attachment.url}"
                )

        return "\n".join(lines)

    # ---------------------------------------------------------
    # CLOSE TICKET
    # ---------------------------------------------------------

    async def close_ticket(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "⚠️ This can only be used inside a server.",
                ephemeral=True,
            )
            return

        if not isinstance(
            interaction.channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "⚠️ This isn't a ticket channel.",
                ephemeral=True,
            )
            return

        channel = interaction.channel
        topic = channel.topic or ""

        if not topic.startswith(
            TICKET_TOPIC_PREFIX
        ):
            await interaction.response.send_message(
                "⚠️ This isn't a Delicate ticket channel.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        transcript = await self.make_transcript(
            channel
        )

        transcript_file = discord.File(
            io.BytesIO(
                transcript.encode("utf-8")
            ),
            filename=(
                f"{channel.name}-transcript.txt"
            ),
        )

        log_channel_id = database.get_guild_setting(
            interaction.guild.id,
            "log_channel_id",
        )

        log_channel = (
            interaction.guild.get_channel(
                log_channel_id
            )
            if log_channel_id
            else None
        )

        try:
            if isinstance(
                log_channel,
                discord.TextChannel,
            ):
                await log_channel.send(
                    content=(
                        f"🎟️ **Ticket closed** · "
                        f"`{channel.name}`\n"
                        f"Closed by: "
                        f"{interaction.user.mention}"
                    ),
                    file=transcript_file,
                )

            await interaction.followup.send(
                "✦ ticket closed.",
                ephemeral=True,
            )

            await channel.delete(
                reason=(
                    f"Ticket closed by "
                    f"{interaction.user} "
                    f"({interaction.user.id})"
                ),
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "⚠️ I don't have permission "
                "to close this ticket.",
                ephemeral=True,
            )

        except discord.HTTPException:
            await interaction.followup.send(
                "⚠️ Discord returned an error while "
                "closing the ticket.",
                ephemeral=True,
            )

    # ---------------------------------------------------------
    # /setticket + d!setticket
    # ---------------------------------------------------------

    @app_commands.command(
        name="setticket",
        description="Set the ticket panel channel.",
    )
    @app_commands.describe(
        channel="Channel where the ticket panel should be posted.",
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def setticket_slash(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "⚠️ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        self.set_panel_channel_id(
            interaction.guild.id,
            channel.id,
        )

        await channel.send(
            embed=self.panel_embed(),
            view=TicketPanelView(self),
        )

        await interaction.response.send_message(
            f"✅ Ticket panel posted in {channel.mention}.",
            ephemeral=True,
        )

    @commands.command(
        name="setticket",
        help="Set the ticket panel channel.",
    )
    @commands.has_permissions(
        administrator=True
    )

    @commands.guild_only()
    async def setticket_prefix(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
    ):
        if ctx.guild is None:
            return

        self.set_panel_channel_id(
            ctx.guild.id,
            channel.id,
        )

        await channel.send(
            embed=self.panel_embed(),
            view=TicketPanelView(self),
        )

        await ctx.send(
            f"✅ Ticket panel posted in {channel.mention}."
        )

    # ---------------------------------------------------------
    # /ticket + d!ticket
    # ---------------------------------------------------------

    @app_commands.command(
        name="ticket",
        description="Post the configured ticket panel.",
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def ticket_slash(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "⚠️ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        panel_id = self.get_panel_channel_id(
            interaction.guild.id
        )

        panel_channel = (
            interaction.guild.get_channel(panel_id)
            if panel_id
            else None
        )

        if not isinstance(
            panel_channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "⚠️ Configure tickets first with "
                "`/setticket #channel`.",
                ephemeral=True,
            )
            return

        await panel_channel.send(
            embed=self.panel_embed(),
            view=TicketPanelView(self),
        )

        await interaction.response.send_message(
            f"✅ Ticket panel posted in "
            f"{panel_channel.mention}.",
            ephemeral=True,
        )

    @commands.command(
        name="ticket",
        help="Post the configured ticket panel.",
    )

    @commands.has_permissions(
        administrator=True
    )
    @commands.guild_only()
    async def ticket_prefix(
        self,
        ctx: commands.Context,
    ):
        if ctx.guild is None:
            await ctx.send(
                "⚠️ This command can only be used in a server."
            )
            return

        panel_id = self.get_panel_channel_id(
            ctx.guild.id
        )

        panel_channel = (
            ctx.guild.get_channel(panel_id)
            if panel_id
            else None
        )

        if not isinstance(
            panel_channel,
            discord.TextChannel,
        ):
            await ctx.send(
                "⚠️ Configure tickets first with "
                "`d!setticket #channel`."
            )
            return

        await panel_channel.send(
            embed=self.panel_embed(),
            view=TicketPanelView(self),
        )

        await ctx.send(
            f"✅ Ticket panel posted in "
            f"{panel_channel.mention}."
        )

    # ---------------------------------------------------------
    # /closeticket + d!closeticket
    # ---------------------------------------------------------

    @app_commands.command(
        name="closeticket",
        description="Close the current ticket.",
    )
    async def closeticket_slash(
        self,
        interaction: discord.Interaction,
    ):
        await self.close_ticket(interaction)

    @commands.command(
        name="closeticket",
        help="Close the current ticket.",
    )

    @commands.guild_only()
    async def closeticket_prefix(
        self,
        ctx: commands.Context,
    ):
        if not isinstance(
            ctx.channel,
            discord.TextChannel,
        ):
            await ctx.send(
                "⚠️ This isn't a ticket channel."
            )
            return

        topic = ctx.channel.topic or ""

        if not topic.startswith(
            TICKET_TOPIC_PREFIX
        ):
            await ctx.send(
                "⚠️ This isn't a Delicate ticket channel."
            )
            return

        transcript = await self.make_transcript(
            ctx.channel
        )

        transcript_file = discord.File(
            io.BytesIO(
                transcript.encode("utf-8")
            ),
            filename=(
                f"{ctx.channel.name}-transcript.txt"
            ),
        )

        log_channel_id = (
            database.get_guild_setting(
                ctx.guild.id,
                "log_channel_id",
            )
            if ctx.guild
            else None
        )

        log_channel = (
            ctx.guild.get_channel(
                log_channel_id
            )
            if log_channel_id and ctx.guild
            else None
        )

        try:
            if isinstance(
                log_channel,
                discord.TextChannel,
            ):
                await log_channel.send(
                    content=(
                        f"🎟️ **Ticket closed** · "
                        f"`{ctx.channel.name}`\n"
                        f"Closed by: {ctx.author.mention}"
                    ),
                    file=transcript_file,
                )

            await ctx.send(
                "✦ ticket closed."
            )

            await ctx.channel.delete(
                reason=(
                    f"Ticket closed by "
                    f"{ctx.author} "
                    f"({ctx.author.id})"
                ),
            )

        except discord.Forbidden:
            await ctx.send(
                "⚠️ I don't have permission "
                "to close this ticket."
            )

        except discord.HTTPException:
            await ctx.send(
                "⚠️ Discord returned an error while "
                "closing the ticket."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
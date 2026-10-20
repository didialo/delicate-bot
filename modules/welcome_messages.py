
import discord

from discord import app_commands
from discord.ext import commands

from urllib.parse import urlparse

from database import database


DEFAULT_TEXT = (
    "Welcome {user} to **{server}**! "
    "You are member #{member_count}."
)

DEFAULT_EMBED_TITLE = "Welcome!"
DEFAULT_EMBED_DESCRIPTION = (
    "Welcome {user} to **{server}**! "
    "You are member #{member_count}."
)
DEFAULT_EMBED_COLOR = 0x5865F2


def initialize_tables():
    database.db.execute(
        """
        CREATE TABLE IF NOT EXISTS welcome_message_settings (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            enabled INTEGER NOT NULL DEFAULT 0,
            mode TEXT NOT NULL DEFAULT 'text',
            message_text TEXT NOT NULL DEFAULT '',
            embed_title TEXT NOT NULL DEFAULT 'Welcome!',
            embed_description TEXT NOT NULL DEFAULT '',
            embed_color INTEGER NOT NULL DEFAULT 5793266,
            embed_footer TEXT NOT NULL DEFAULT '',
            thumbnail_url TEXT NOT NULL DEFAULT '',
            image_url TEXT NOT NULL DEFAULT ''
        )
        """
    )

    existing_columns = {
        row["name"]
        for row in database.db.execute(
            "PRAGMA table_info(welcome_message_settings)"
        ).fetchall()
    }

    migrations = {
        "embed_footer": "TEXT NOT NULL DEFAULT ''",
        "thumbnail_url": "TEXT NOT NULL DEFAULT ''",
        "image_url": "TEXT NOT NULL DEFAULT ''",
    }

    for column, definition in migrations.items():
        if column not in existing_columns:
            database.db.execute(
                f"ALTER TABLE welcome_message_settings "
                f"ADD COLUMN {column} {definition}"
            )

    database.db.commit()


def get_settings(guild_id: int):
    return database.db.execute(
        """
        SELECT *
        FROM welcome_message_settings
        WHERE guild_id = ?
        """,
        (guild_id,),
    ).fetchone()


def render_template(template: str, member: discord.Member) -> str:
    replacements = {
        "{user}": member.mention,
        "{username}": member.name,
        "{server}": member.guild.name,
        "{member_count}": str(member.guild.member_count or 0),
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    return template


def valid_image_url(value: str) -> bool:
    if not value:
        return True

    try:
        parsed = urlparse(value)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )
    except ValueError:
        return False


def build_embed(settings, member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=render_template(
            settings["embed_title"] or DEFAULT_EMBED_TITLE,
            member,
        )[:256],
        description=render_template(
            settings["embed_description"] or DEFAULT_EMBED_DESCRIPTION,
            member,
        )[:4096],
        color=int(
            settings["embed_color"] or DEFAULT_EMBED_COLOR
        ),
    )

    footer = settings["embed_footer"] or ""
    if footer:
        embed.set_footer(
            text=render_template(footer, member)[:2048]
        )
    else:
        embed.set_footer(
            text=f"Member #{member.guild.member_count or 0}"
        )

    thumbnail_url = settings["thumbnail_url"] or ""
    image_url = settings["image_url"] or ""

    if valid_image_url(thumbnail_url) and thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    if valid_image_url(image_url) and image_url:
        embed.set_image(url=image_url)

    return embed


def can_manage(interaction: discord.Interaction) -> bool:
    return (
        interaction.guild is not None
        and isinstance(interaction.user, discord.Member)
        and interaction.user.guild_permissions.manage_guild
    )


class EmbedFieldsModal(discord.ui.Modal):
    def __init__(self, guild_id: int):
        super().__init__(title="Edit Welcome Embed")
        self.guild_id = guild_id

        settings = get_settings(guild_id)

        self.title_input = discord.ui.TextInput(
            label="Embed title",
            default=settings["embed_title"] or DEFAULT_EMBED_TITLE,
            max_length=256,
            required=True,
        )

        self.description_input = discord.ui.TextInput(
            label="Description",
            default=(
                settings["embed_description"]
                or DEFAULT_EMBED_DESCRIPTION
            ),
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=True,
        )

        self.footer_input = discord.ui.TextInput(
            label="Footer (optional)",
            default=settings["embed_footer"] or "",
            max_length=2048,
            required=False,
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.footer_input)

    async def on_submit(self, interaction: discord.Interaction):
        if not can_manage(interaction):
            await interaction.response.send_message(
                "You need the Manage Server permission to edit this.",
                ephemeral=True,
            )
            return

        if interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This editor belongs to another server.",
                ephemeral=True,
            )
            return

        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET embed_title = ?,
                embed_description = ?,
                embed_footer = ?,
                mode = 'embed'
            WHERE guild_id = ?
            """,
            (
                str(self.title_input),
                str(self.description_input),
                str(self.footer_input),
                self.guild_id,
            ),
        )
        database.db.commit()

        await interaction.response.send_message(
            "Embed fields saved. The embed format is now enabled.",
            ephemeral=True,
        )


class EmbedColorModal(discord.ui.Modal):
    def __init__(self, guild_id: int):
        super().__init__(title="Change Embed Color")
        self.guild_id = guild_id

        settings = get_settings(guild_id)
        current_color = int(
            settings["embed_color"] or DEFAULT_EMBED_COLOR
        )

        self.color_input = discord.ui.TextInput(
            label="Hex color, for example #5865F2",
            default=f"#{current_color:06X}",
            max_length=7,
            required=True,
        )
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        if not can_manage(interaction):
            await interaction.response.send_message(
                "You need the Manage Server permission to edit this.",
                ephemeral=True,
            )
            return

        if interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This editor belongs to another server.",
                ephemeral=True,
            )
            return

        try:
            color = int(
                str(self.color_input).strip().lstrip("#"),
                16,
            )
            if not 0 <= color <= 0xFFFFFF:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Invalid color. Use a value such as #A8E6CF.",
                ephemeral=True,
            )
            return

        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET embed_color = ?,
                mode = 'embed'
            WHERE guild_id = ?
            """,
            (color, self.guild_id),
        )
        database.db.commit()

        await interaction.response.send_message(
            f"Embed color saved: `#{color:06X}`.",
            ephemeral=True,
        )


class EmbedImagesModal(discord.ui.Modal):
    def __init__(self, guild_id: int):
        super().__init__(title="Edit Embed Images")
        self.guild_id = guild_id

        settings = get_settings(guild_id)

        self.thumbnail_input = discord.ui.TextInput(
            label="Thumbnail URL (optional)",
            default=settings["thumbnail_url"] or "",
            max_length=500,
            required=False,
        )

        self.image_input = discord.ui.TextInput(
            label="Large image URL (optional)",
            default=settings["image_url"] or "",
            max_length=500,
            required=False,
        )

        self.add_item(self.thumbnail_input)
        self.add_item(self.image_input)

    async def on_submit(self, interaction: discord.Interaction):
        if not can_manage(interaction):
            await interaction.response.send_message(
                "You need the Manage Server permission to edit this.",
                ephemeral=True,
            )
            return

        if interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This editor belongs to another server.",
                ephemeral=True,
            )
            return

        thumbnail = str(self.thumbnail_input).strip()
        image = str(self.image_input).strip()

        if not valid_image_url(thumbnail) or not valid_image_url(image):
            await interaction.response.send_message(
                "Use valid HTTP or HTTPS image URLs, "
                "or leave the fields empty to remove images.",
                ephemeral=True,
            )
            return

        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET thumbnail_url = ?,
                image_url = ?,
                mode = 'embed'
            WHERE guild_id = ?
            """,
            (thumbnail, image, self.guild_id),
        )
        database.db.commit()

        await interaction.response.send_message(
            "Embed images saved. The embed format is now enabled.",
            ephemeral=True,
        )


class WelcomeEditorView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=600)
        self.guild_id = guild_id

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if not can_manage(interaction):
            await interaction.response.send_message(
                "You need the Manage Server permission to use this editor.",
                ephemeral=True,
            )
            return False

        if interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This editor belongs to another server.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Edit Fields",
        style=discord.ButtonStyle.primary,
        emoji="✏️",
        row=0,
    )
    async def edit_fields(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if get_settings(self.guild_id) is None:
            await interaction.response.send_message(
                "Run `welcome setup` first.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            EmbedFieldsModal(self.guild_id)
        )

    @discord.ui.button(
        label="Color",
        style=discord.ButtonStyle.secondary,
        emoji="🎨",
        row=0,
    )
    async def edit_color(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if get_settings(self.guild_id) is None:
            await interaction.response.send_message(
                "Run `welcome setup` first.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            EmbedColorModal(self.guild_id)
        )

    @discord.ui.button(
        label="Images",
        style=discord.ButtonStyle.secondary,
        emoji="🖼️",
        row=0,
    )
    async def edit_images(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if get_settings(self.guild_id) is None:
            await interaction.response.send_message(
                "Run `welcome setup` first.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            EmbedImagesModal(self.guild_id)
        )

    @discord.ui.button(
        label="Preview",
        style=discord.ButtonStyle.success,
        emoji="👁️",
        row=1,
    )
    async def preview(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        settings = get_settings(self.guild_id)

        if settings is None:
            await interaction.response.send_message(
                "Run `welcome setup` first.",
                ephemeral=True,
            )
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Could not load your server member information.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=build_embed(settings, member),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @discord.ui.button(
        label="Use Embed",
        style=discord.ButtonStyle.primary,
        emoji="✅",
        row=1,
    )
    async def use_embed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET mode = 'embed'
            WHERE guild_id = ?
            """,
            (self.guild_id,),
        )
        database.db.commit()

        await interaction.response.send_message(
            "Embed format enabled for future welcome messages.",
            ephemeral=True,
        )


class WelcomeMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="welcome",
        description="Configure server welcome messages.",
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def welcome(self, ctx: commands.Context):
        await ctx.send(
            "Welcome Messages commands:\n"
            "`welcome setup <channel>`\n"
            "`welcome mode <text|embed>`\n"
            "`welcome text <message>`\n"
            "`welcome embed <title> <description>`\n"
            "`welcome color <hex>`\n"
            "`welcome editor` — Open the visual embed editor.\n"
            "`welcome preview`\n"
            "`welcome disable`"
        )

    @welcome.command(
        name="setup",
        description="Set the welcome channel and enable welcome messages.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_welcome(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
    ):
        database.db.execute(
            """
            INSERT INTO welcome_message_settings (
                guild_id,
                channel_id,
                enabled,
                mode,
                message_text,
                embed_title,
                embed_description,
                embed_color,
                embed_footer,
                thumbnail_url,
                image_url
            )
            VALUES (?, ?, 1, 'text', ?, ?, ?, ?, '', '', '')
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                enabled = 1
            """,
            (
                ctx.guild.id,
                channel.id,
                DEFAULT_TEXT,
                DEFAULT_EMBED_TITLE,
                DEFAULT_EMBED_DESCRIPTION,
                DEFAULT_EMBED_COLOR,
            ),
        )
        database.db.commit()

        await ctx.send(
            f"Welcome messages are enabled in {channel.mention}."
        )

    @welcome.command(
        name="mode",
        description="Choose the welcome message format.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def set_mode(
        self,
        ctx: commands.Context,
        mode: str,
    ):
        mode = mode.lower().strip()

        if mode not in {"text", "embed"}:
            await ctx.send("Choose `text` or `embed`.")
            return

        settings = get_settings(ctx.guild.id)

        if settings is None or settings["channel_id"] is None:
            await ctx.send("Run `welcome setup` first.")
            return

        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET mode = ?
            WHERE guild_id = ?
            """,
            (mode, ctx.guild.id),
        )
        database.db.commit()

        await ctx.send(f"Welcome format set to **{mode}**.")

    @welcome.command(
        name="text",
        description="Customize the normal text welcome message.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def set_text(
        self,
        ctx: commands.Context,
        *,
        message: str,
    ):
        if get_settings(ctx.guild.id) is None:
            await ctx.send("Run `welcome setup` first.")
            return

        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET message_text = ?
            WHERE guild_id = ?
            """,
            (message[:2000], ctx.guild.id),
        )
        database.db.commit()

        await ctx.send("Text welcome message updated.")

    @welcome.command(
        name="embed",
        description="Customize the welcome embed title and description.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def set_embed(
        self,
        ctx: commands.Context,
        title: str,
        *,
        description: str,
    ):
        if get_settings(ctx.guild.id) is None:
            await ctx.send("Run `welcome setup` first.")
            return

        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET embed_title = ?,
                embed_description = ?,
                mode = 'embed'
            WHERE guild_id = ?
            """,
            (title[:256], description[:4096], ctx.guild.id),
        )
        database.db.commit()

        await ctx.send("Welcome embed updated.")

    @welcome.command(
        name="color",
        description="Change the welcome embed color.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def set_color(
        self,
        ctx: commands.Context,
        color: str,
    ):
        if get_settings(ctx.guild.id) is None:
            await ctx.send("Run `welcome setup` first.")
            return

        try:
            color_value = int(color.strip().lstrip("#"), 16)
            if not 0 <= color_value <= 0xFFFFFF:
                raise ValueError
        except ValueError:
            await ctx.send("Use a hex color such as `#5865F2`.")
            return

        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET embed_color = ?,
                mode = 'embed'
            WHERE guild_id = ?
            """,
            (color_value, ctx.guild.id),
        )
        database.db.commit()

        await ctx.send(f"Embed color set to `#{color_value:06X}`.")

    @welcome.command(
        name="editor",
        description="Open the interactive welcome embed editor.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def editor(self, ctx: commands.Context):
        settings = get_settings(ctx.guild.id)

        if settings is None or settings["channel_id"] is None:
            await ctx.send("Run `welcome setup <channel>` first.")
            return

        member = ctx.author
        if not isinstance(member, discord.Member):
            await ctx.send("Could not load your server member information.")
            return

        await ctx.send(
            "## Welcome Embed Editor\n"
            "Use the buttons below to edit and preview your embed. "
            "Changes are saved automatically.",
            embed=build_embed(settings, member),
            view=WelcomeEditorView(ctx.guild.id),
        )

    @welcome.command(
        name="preview",
        description="Preview the current welcome message.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def preview(self, ctx: commands.Context):
        settings = get_settings(ctx.guild.id)

        if settings is None:
            await ctx.send("Run `welcome setup` first.")
            return

        member = ctx.author

        if settings["mode"] == "embed":
            await ctx.send(
                embed=build_embed(settings, member),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            message = render_template(
                settings["message_text"] or DEFAULT_TEXT,
                member,
            )
            await ctx.send(
                message[:2000],
                allowed_mentions=discord.AllowedMentions(
                    users=[member],
                    roles=False,
                    everyone=False,
                ),
            )

    @welcome.command(
        name="disable",
        description="Disable welcome messages for this server.",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def disable(self, ctx: commands.Context):
        database.db.execute(
            """
            UPDATE welcome_message_settings
            SET enabled = 0
            WHERE guild_id = ?
            """,
            (ctx.guild.id,),
        )
        database.db.commit()

        await ctx.send("Welcome messages have been disabled.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = get_settings(member.guild.id)

        if (
            settings is None
            or not settings["enabled"]
            or settings["channel_id"] is None
        ):
            return

        channel = member.guild.get_channel(settings["channel_id"])

        if not isinstance(channel, discord.TextChannel):
            return

        try:
            if settings["mode"] == "embed":
                await channel.send(
                    embed=build_embed(settings, member),
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            else:
                message = render_template(
                    settings["message_text"] or DEFAULT_TEXT,
                    member,
                )
                await channel.send(
                    message[:2000],
                    allowed_mentions=discord.AllowedMentions(
                        users=[member],
                        roles=False,
                        everyone=False,
                    ),
                )
        except discord.HTTPException:
            return


async def setup(bot):
    initialize_tables()
    await bot.add_cog(WelcomeMessages(bot))

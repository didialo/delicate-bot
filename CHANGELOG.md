# Changelog

## 2026-08-12

### Added

- 🎟️ Added a private support-ticket system.
- Added `/setticket` and `d!setticket` for configuring and posting ticket panels.
- Added `/ticket` and `d!ticket` for reposting configured ticket panels.
- Added `/closeticket` and `d!closeticket` for closing tickets.
- Added persistent ticket buttons for opening and closing tickets.
- Added private ticket-channel permissions for ticket creators and staff.
- Added prevention of multiple simultaneous tickets per user.
- Added automatic ticket transcripts.
- Added transcript delivery to the configured moderation log channel.
- Added invite welcome DMs when Delicate joins a server.
- Added audit-log based inviter detection.
- Added `/testinvitedm` and `d!testinvitedm` for safely testing invite DMs.
- Added `/invite` and `d!invite`.
- Added `/help` and `d!help`.
- Added `/ping` and `d!ping`.
- Added automatic loading of the ticket module during startup.

### Changed

- Disabled discord.py's default `help` command.
- Improved slash-command synchronization.
- Added cleanup for stale guild-scoped command registrations.
- Organized ticket functionality into `modules/tickets.py`.
- Added ticket configuration to server settings.
- Improved startup loading and cog initialization.

### Fixed

- Fixed duplicate slash commands.
- Fixed duplicate `Tickets` cog loading.
- Fixed `Unknown interaction` errors from the invite-DM test command.
- Fixed invalid ticket button emojis.
- Fixed the custom help command conflicting with discord.py's built-in help command.
- Fixed redundant command synchronization during startup.

### Existing Features

- Moderation commands
- Warning escalation
- Temporary bans and timeouts
- Moderation history and case lookup
- Moderation logging
- Server settings
- Configurable prefixes
- Boost notifications
- SQLite persistence

**Delicate — soft colors, hard moderation.** 📦🎀

# Changelog

All notable changes to Delicate are documented here.

## [Unreleased]

### Added

* 🎟️ Added a private support-ticket system.
* Added `/setticket` and `d!setticket` for configuring and posting ticket panels.
* Added `/ticket` and `d!ticket` for reposting configured ticket panels.
* Added `/closeticket` and `d!closeticket` for closing tickets.
* Added persistent ticket buttons for opening and closing tickets.
* Added private ticket-channel permissions for ticket creators and staff.
* Added prevention of multiple simultaneous tickets per user.
* Added automatic ticket transcripts.
* Added transcript delivery to the configured moderation log channel.
* Added invite welcome DMs when Delicate joins a server.
* Added audit-log based inviter detection.
* Added a temporary `/testinvitedm` / `d!testinvitedm` command for testing invite DMs without inviting Delicate into additional servers.
* Added `/invite` and `d!invite` for generating Delicate's bot invite link.
* Added a custom `/help` and `d!help` command.
* Added `/ping` and `d!ping` for checking response and WebSocket latency.
* Added automatic loading of the ticket module during startup.

### Changed

* Disabled discord.py's default `help` command so Delicate can provide its own hybrid help command.
* Improved slash-command synchronization.
* Added cleanup for stale guild-scoped command registrations in the configured development guild.
* Prevented duplicate command synchronization during startup.
* Organized ticket functionality into `modules/tickets.py`.
* Extended server settings to include ticket configuration.
* Updated boost functionality to continue using Delicate's module system.
* Improved startup loading so ticket functionality is initialized before command synchronization.

### Fixed

* Fixed duplicate slash commands caused by stale guild-scoped registrations.
* Fixed duplicate `Tickets` cog loading during startup.
* Fixed the invite-DM test command returning `Unknown interaction` when the response took too long.
* Fixed ticket button emoji validation errors by using supported Discord emojis.
* Fixed the custom `help` command colliding with discord.py's built-in help command.
* Fixed command startup performance by eliminating redundant global command synchronization.

## Previous Features

### Moderation

* Added temporary and permanent bans.
* Added member kicking.
* Added Discord timeouts / mutes.
* Added unmute support.
* Added user unban support.
* Added warning commands.
* Added automatic warning escalation.
* Added moderation cases.
* Added moderation history.
* Added case lookup.

### Logging

* Added configurable moderation log channels.
* Added moderation embeds.
* Added case numbers and timestamps.
* Added automatic escalation information to logs.

### Database

* Added SQLite persistence.
* Added per-server settings.
* Added warning storage.
* Added moderation case storage.
* Added automatic expiration tracking.
* Added database health checks.

### Boosts

* Added boost announcement support.
* Added boost-channel configuration.
* Added `/testboost` and `d!testboost`.
* Added automatic detection of new server boosts.
* Added Cardboard Box themed boost embeds.

### Prefixes

* Added the `d!` prefix.
* Added configurable server-specific prefixes.
* Kept `d!` available as the fallback prefix.

### Slash Commands

* Added global slash-command synchronization.
* Added support for public multi-server slash commands.
* Added development-guild cleanup for stale command registrations.

## Notes

Delicate is actively evolving for **Clouddyie's Cardboard Box**.

Before releasing a new version, test:

* moderation commands
* prefix commands
* slash commands
* ticket creation and closing
* ticket transcripts
* boost notifications
* invite welcome DMs
* command synchronization
* database persistence

**Delicate — soft colors, hard moderation.** 📦🎀

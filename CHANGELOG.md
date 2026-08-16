# Changelog

All notable changes to Delicate are documented here.

---

## 15/08/2026

### ✦ Added

* Added full moderation case tracking with persistent SQLite storage.
* Added temporary and permanent ban support.
* Added member kick moderation.
* Added member timeout moderation.
* Added unban and timeout removal commands.
* Added persistent warning system.
* Added automatic warning escalation:

  * 3 warnings → 1 hour timeout
  * 5 warnings → 1 day timeout
  * 7 warnings → permanent ban
* Added moderation history command.
* Added individual moderation case lookup.
* Added moderation log embeds.
* Added channel lock and unlock commands.
* Added channel hide and unhide commands.
* Added channel slowmode controls.
* Added message purge command.
* Added persistent per-server settings.
* Added configurable moderation log channel.
* Added configurable boost notification channel.
* Added configurable staff role.
* Added configurable suggestion channel.
* Added configurable Server Tag reward role.
* Added full suggestion system with pending, approved, and denied states.
* Added persistent private ticket system.
* Added ticket panel configuration.
* Added persistent ticket buttons.
* Added one-open-ticket-per-user protection.
* Added automatic ticket transcript generation.
* Added ticket transcript logging.
* Added Server Tag reward panel with role claiming.
* Added announcement command with optional attachments.
* Added member count command.
* Added custom Delicate invite command.
* Added invite welcome DMs using Discord audit logs.
* Added developer guild blacklist system.
* Added developer guild unblacklist system.
* Added developer shutdown command.
* Added test invite DM command.
* Added `/about` information card.
* Added `/help` command list.
* Added enhanced `/ping` system information.
* Added CPU detection.
* Added process memory reporting.
* Added uptime reporting.
* Added WebSocket latency reporting.
* Added automatic temporary moderation expiration worker.
* Added hybrid command support for the main bot command set.
* Added persistent ticket views that survive bot restarts.
* Added cozy pastel Delicate visual styling throughout embeds and responses.

### ✦ Improved

* Improved moderation permission checks.
* Improved moderator role hierarchy checks.
* Improved bot role hierarchy checks.
* Improved Discord interaction response handling for hybrid commands.
* Improved error handling for slash and prefix commands.
* Improved suggestion message updates after approval or denial.
* Improved ticket privacy through role and member-specific channel permissions.
* Improved server configuration visibility through `/settings`.
* Improved command synchronization for global commands and the development guild.
* Improved status and runtime information shown by `/ping`.
* Improved overall consistency of Delicate's cozy visual identity.

### ✦ Fixed

* Fixed missing `setlog`, `setboost`, and `setstaff` commands.
* Fixed global command synchronization stopping at 34 commands.
* Restored the full 37-command command tree.
* Fixed `/about` command counting so it reads the registered slash command tree.
* Fixed ticket commands being loaded after the ticket cog setup.
* Fixed temporary moderation cases not being automatically closed after expiration.
* Fixed role hierarchy edge cases for moderation actions.
* Fixed ticket channels allowing unintended regular-member visibility.
* Fixed suggestion embeds not reflecting their updated status.
* Fixed moderation and ticket configuration data being lost between restarts.

---

## [1.0.0]

### ✦ Initial Release

* Initial Delicate moderation bot implementation.
* SQLite-backed moderation storage.
* Basic moderation commands.
* Initial server configuration system.
* Initial Delicate visual identity.
* Initial ticket and utility functionality.

---

## Current Status

```text
// PROJECT: DELICATE
// VERSION: 2.0.0
// COMMANDS: 37
// DATABASE: SQLITE
// TICKETS: ACTIVE
// MODERATION: ACTIVE
// STATUS: STABLE
```

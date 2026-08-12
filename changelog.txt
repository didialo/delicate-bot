DELICATE CHANGELOG
==================

[2026-08-12] — v2.0

NEW
---
- Added separate database module for persistent moderation data.
- Added per-server guild settings.
- Added configurable moderation log channels.
- Added configurable boost notification channels.
- Added configurable staff roles.
- Added persistent moderation cases.
- Added persistent warnings.
- Added automatic warning escalation.
- Added automatic expiration for temporary bans.
- Added automatic expiration for temporary timeouts.
- Added moderation history.
- Added individual case lookup.
- Added slash commands.
- Added prefix commands using d!.
- Added configurable server prefixes.
- Kept d! available as a fallback prefix.
- Added server settings command.
- Added moderation command error handling.
- Added Discord presence/status.

MODERATION
----------
- Ban members temporarily or permanently.
- Kick members.
- Timeout members.
- Remove member timeouts.
- Unban users by Discord ID.
- Warn members.
- View member moderation history.
- View individual moderation cases.

WARNING ESCALATION
------------------
- 3 active warnings = 1 hour timeout.
- 5 active warnings = 1 day timeout.
- 7 active warnings = permanent ban.

DATABASE
--------
- Added SQLite persistence.
- Added cases table.
- Added warnings table.
- Added guild_settings table.
- Added database indexes.
- Added automatic database initialization.
- Existing moderation.db files are preserved.

PREFIX SYSTEM
--------------
- Default prefix: d!
- Added server-specific prefixes.
- Added prefix reset support.
- d! remains available after changing a server prefix.
- Prefix changes require Manage Server permission.

COMMANDS
--------
Slash commands:
- /ban
- /kick
- /mute
- /unmute
- /warn
- /unban
- /history
- /case
- /setlog
- /setboost
- /setstaff
- /settings

Prefix commands:
- d!ban
- d!kick
- d!mute
- d!unmute
- d!warn
- d!unban
- d!history
- d!case
- d!setlog
- d!setboost
- d!setstaff
- d!settings
- d!prefix

FIXES
-----
- Fixed the database import structure.
- Fixed the database package being loaded as a namespace package.
- Fixed missing database functions such as create_case().
- Fixed prefix commands not responding without Message Content Intent.
- Fixed moderation commands using the wrong database connection.
- Fixed moderation settings being tied to hard-coded channel IDs.
- Fixed moderation data not being separated cleanly from bot logic.
- Fixed temporary moderation expiration handling.
- Fixed hybrid command responses for prefix and slash commands.
- Restored the Delicate Discord presence.
- Improved command synchronization.

IMPORTANT
---------
- Message Content Intent must be enabled for prefix commands.
- The bot's role must be above members it needs to moderate.
- The database package must contain:

  database/
  ├── __init__.py
  └── database.py

- Do not delete moderation.db unless you intentionally want to remove
  existing moderation data.

UPCOMING
--------
- Global slash-command synchronization for public servers.
- Additional moderation features.
- More configurable server settings.
- More Delicate modules and public-bot improvements.

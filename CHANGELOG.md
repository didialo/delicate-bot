# Changelog

All notable changes to **Delicate** are documented here.

## August 14, 2026

### Added

* 💡 Added the suggestion system
* `/suggest` and `d!suggest`
* `/setsuggest` and `d!setsuggest`
* Persistent suggestion storage
* Suggestion IDs and statuses
* Suggestion message tracking
* 🐌 Added `/slowmode` and `d!slowmode`
* 🛡️ Added the developer guild blacklist system
* ⚙️ Added additional persistent guild settings
* 🖥️ Added system information and runtime reporting
* 📡 Added WebSocket latency reporting
* 🔌 Added the developer-only shutdown command
* 🗃️ Added database migrations for new settings
* 🧩 Added additional database indexes for moderation data

### Changed

* Reworked the main bot architecture around the current moderation and utility systems
* Expanded the SQLite database to support suggestions and additional server configuration
* Improved hybrid slash/prefix command handling
* Improved response handling for slash and prefix commands
* Improved persistent configuration across restarts
* Improved moderation logging
* Improved temporary moderation handling
* Improved startup and module loading
* Updated the ticket system to work with the current database and configuration structure
* Updated project dependencies

### Fixed

* Fixed interaction response handling after deferred commands
* Fixed database migration handling for existing installations
* Fixed persistent configuration edge cases
* Fixed command synchronization issues
* Fixed startup and module loading issues
* Fixed ticket module compatibility with the updated database
* Fixed several command and interaction errors

---

## Previous Features

### 🛡️ Moderation

* Ban members
* Kick members
* Timeout members
* Remove timeouts
* Unban users
* Warn members
* Moderation case numbers
* Persistent moderation history
* Case lookup
* Staff moderation logs
* Automatic expiration of temporary moderation actions

### ⚠️ Warning Escalation

* 3 active warnings → 1 hour timeout
* 5 active warnings → 1 day timeout
* 7 active warnings → permanent ban

### ⏱️ Temporary Moderation

* Seconds
* Minutes
* Hours
* Days
* Weeks
* Compound durations
* Permanent bans
* Automatic expiration of temporary bans and timeouts

### ⚙️ Server Configuration

* Moderation log channel
* Boost announcement channel
* Staff role
* Suggestion channel
* Ticket panel configuration
* Persistent per-server settings
* Configurable server prefixes

### 🎟️ Support Tickets

* Configurable ticket panel
* Private ticket channels
* Staff-role access
* One-ticket-per-user protection
* Ticket open button
* Ticket close button
* Persistent ticket buttons
* Automatic transcripts
* Transcript logging

### 📦 Boost System

* Automatic boost detection
* Boost announcement embeds
* Boost count display
* Boost level display
* `/testboost`
* `d!testboost`

### ✉️ Invite Handling

* Automatic inviter detection
* Audit-log based invite detection
* Private welcome DMs
* Safe handling for unavailable DMs
* `/testinvitedm`
* `d!testinvitedm`

### ✦ Utility Commands

* `/help`
* `d!help`
* `/invite`
* `d!invite`
* `/ping`
* `d!ping`

### 🪽 Prefix System

* Default `d!` prefix
* Custom server prefixes
* Prefix reset functionality
* `d!` remains available even when a custom prefix is configured

---

## Current Status

Delicate is actively maintained and continues to receive improvements across moderation, utility commands, tickets, suggestions, configuration, and server management.

See [`README.md`](README.md) for setup instructions and the current feature list.

---

**Delicate — soft colors, hard moderation.** 🎀📦

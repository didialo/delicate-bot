
# CHANGELOG.md

```md
# Changelog

All notable changes to **Delicate Bot** are documented here.

## [Unreleased]

### Added

* 🎟️ Private support ticket system
* `/setticket` / `d!setticket`
* `/ticket` / `d!ticket`
* `/closeticket` / `d!closeticket`
* Ticket open button
* Ticket close button
* Private ticket channels
* One-open-ticket-per-user protection
* Staff-role access to tickets
* Automatic ticket transcripts
* Transcript logging
* ✦ Invite welcome DMs when Delicate joins a server
* `/testinvitedm` / `d!testinvitedm`
* `/help` / `d!help`
* `/invite` / `d!invite`
* `/ping` / `d!ping`
* Ticket panel configuration
* Ticket panel settings
* WebSocket latency reporting
* Command response-time reporting

### Changed

* Improved global slash-command synchronization
* Removed stale guild-scoped command registrations
* Prevented duplicate global command synchronization
* Disabled discord.py's default `help` command
* Added Delicate's custom help command
* Added the Tickets cog
* Added persistent ticket buttons
* Improved invite detection using the Discord audit log
* Improved invite-DM failure handling
* Improved prefix and slash compatibility for utility commands
* Improved server settings to include ticket configuration
* Improved startup command registration

### Fixed

* Fixed duplicated slash commands
* Fixed duplicate Tickets cog loading
* Fixed the custom `/help` command registration conflict
* Fixed `Unknown interaction` errors from the invite-DM test command
* Fixed invalid ticket-button emoji errors
* Fixed ticket buttons after bot restarts
* Fixed invite-DM testing with both slash and prefix commands
* Fixed duplicate global command synchronization
* Fixed startup errors caused by loading the Tickets cog twice

## Previous Features

### Moderation

* Ban members
* Kick members
* Timeout members
* Remove timeouts
* Unban users
* Warn members
* Moderation case numbers
* Moderation history
* Case lookup
* Moderation logging

### Warning Escalation

* 3 active warnings → 1 hour timeout
* 5 active warnings → 1 day timeout
* 7 active warnings → permanent ban

### Temporary Moderation

* Seconds
* Minutes
* Hours
* Days
* Weeks
* Compound durations
* Permanent bans
* Automatic expiration of temporary bans and timeouts

### Server Configuration

* Moderation log channel
* Boost notification channel
* Staff role
* Ticket panel channel
* Per-server persistent settings

### Boost System

* Automatic boost detection
* Boost announcement embeds
* Boost count display
* Boost level display
* `/testboost`
* `d!testboost`

### Utility Commands

* `/help`
* `d!help`
* `/invite`
* `d!invite`
* `/ping`
* `d!ping`

## Development Notes

Delicate is currently in active development and is being prepared for public verification.

Testing commands currently include:

```text
/testboost
d!testboost

/testinvitedm
d!testinvitedm

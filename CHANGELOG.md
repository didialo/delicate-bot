# Changelog

All notable changes to **Delicate Bot** are documented here.

## Added

* 🎟️ Private support ticket system
* `/setticket` and `d!setticket`
* `/ticket` and `d!ticket`
* `/closeticket` and `d!closeticket`
* Ticket open button
* Ticket close button
* Private ticket channels
* One-open-ticket-per-user protection
* Staff-role access to tickets
* Automatic ticket transcripts
* Transcript logging
* ✦ Invite welcome DMs when Delicate joins a server
* `/testinvitedm` and `d!testinvitedm`
* `/help` and `d!help`
* `/invite` and `d!invite`
* `/ping` and `d!ping`
* Ticket panel configuration
* Ticket panel settings
* WebSocket latency reporting
* Command response-time reporting

## Changed

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
* Added ticket configuration to server settings
* Improved startup command registration
* Improved startup stability when loading modules and commands

## Fixed

* Fixed duplicated slash commands
* Fixed duplicate Tickets cog loading
* Fixed the custom `/help` command registration conflict
* Fixed `Unknown interaction` errors from the invite-DM test command
* Fixed invalid ticket-button emoji errors
* Fixed ticket buttons after bot restarts
* Fixed invite-DM testing with both slash and prefix commands
* Fixed duplicate global command synchronization
* Fixed startup errors caused by loading the Tickets cog twice

---

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

### Invite Handling

* Automatic inviter detection when Delicate joins a server
* Private welcome DM for the inviter
* Audit-log based invite detection
* Safe handling for unavailable DMs
* `/testinvitedm`
* `d!testinvitedm`

### Support Tickets

* Configurable ticket panel
* Private ticket channels
* Staff access
* One-ticket-per-user protection
* Ticket close button
* Ticket transcripts
* Transcript logging

---

## Current Status

Delicate is publicly available and continues to receive improvements and new features.

Development commands currently include:

```text
/testboost
d!testboost

/testinvitedm
d!testinvitedm
```

These commands are intended for development and testing and may be restricted or removed in future releases.

---

## Current Startup

A normal startup should look similar to:

```text
🎟️ Tickets cog loaded.
Synced 19 global command(s).
Logged in as ...
```

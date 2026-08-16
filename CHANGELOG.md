# Changelog

All notable changes to Delicate are documented here.

---

## [2.1.0] — 16/08/2026

### ✦ Added

- Added `/snapshot` for saving lightweight snapshots of the current server state.
- Added `/handoff` for generating staff shift handoff reports.
- Added `/heartbeat` for checking Delicate's internal systems.
- Added `/foster` for assigning temporary staff guardians to members.
- Added `/echo` for connecting a member's recent moderation history into a single timeline.
- Added persistent storage for Delicate snapshots.
- Added persistent storage for temporary foster assignments.
- Added a new collection of Delicate-specific server management tools.
- Increased the command count from 37 to 42.

### ✦ Improved

- Expanded Delicate beyond traditional moderation commands.
- Added more staff-focused utilities for server management.
- Improved Delicate's cozy identity through dedicated server-management systems.

---

## [2.0.0] — 15/08/2026

### ✦ Added

- Added full moderation case tracking with persistent SQLite storage.
- Added temporary and permanent ban support.
- Added member kick moderation.
- Added member timeout moderation.
- Added unban and timeout removal commands.
- Added persistent warning system.
- Added automatic warning escalation.
- Added moderation history and case lookup.
- Added moderation logging.
- Added channel locking, unlocking, hiding, and unhiding.
- Added slowmode controls.
- Added message purge command.
- Added persistent server configuration.
- Added configurable log, boost, staff, suggestion, reward, and ticket settings.
- Added suggestion system.
- Added private support ticket system.
- Added ticket transcripts.
- Added Server Tag rewards.
- Added announcement command with attachments.
- Added member count and enhanced ping commands.
- Added invite welcome DMs.
- Added developer guild blacklist system.
- Added developer shutdown and testing commands.
- Added `/about` and `/help`.
- Added temporary moderation expiration worker.
- Added hybrid command support.

### ✦ Fixed

- Fixed the command tree being stuck at 34 global commands.
- Restored the missing `setlog`, `setboost`, and `setstaff` commands.
- Fixed `/about` command counting.
- Restored the full 37-command command tree.

---

## Current Status

```text
// PROJECT: DELICATE
// VERSION: 2.1.0
// COMMANDS: 42
// DATABASE: SQLITE
// SPECIAL SYSTEMS: 5
// TICKETS: ACTIVE
// MODERATION: ACTIVE
// STATUS: STABLE

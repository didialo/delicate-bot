# Clouddyie's Cardboard Box — Discord Moderation Bot v2

A Discord-only moderation bot with a soft cardboard/pastel visual style, staff logs, persistent cases, warnings, automatic escalation, and member history.

## Commands

### Moderation
- `/ban member duration reason`
- `/kick member reason`
- `/mute member duration reason`
- `/warn member reason`

### Reversals
- `/unban user_id reason`
- `/unmute member reason`

### Records
- `/history member limit`
- `/case case_id`

## Warning system

Warnings are stored separately from cases and remain active until you later choose to add a warning-clear command.

Default automatic escalation:

| Active warnings | Action |
|---:|---|
| 3 | 1 hour timeout |
| 5 | 1 day timeout |
| 7 | Permanent ban |

The escalation thresholds are at the top of `bot.py` in `WARN_ESCALATION`, so you can change them easily.

For example:

    WARN_ESCALATION = [
        (3, "MUTE", "1h"),
        (5, "MUTE", "1d"),
        (7, "BAN", "perm"),
    ]

The highest threshold reached is applied. A 5th warning therefore triggers the 5-warning escalation, not both the 3-warning and 5-warning actions.

## Design

The logs use Discord embeds with a warm pastel palette inspired by Clouddyie's Cardboard Box aesthetic.

Each moderation log contains:
- Action
- Member
- Reason
- Moderator
- Duration when relevant
- Case number
- Timestamp

The `/history` command shows the member's recent warnings and moderation cases in one private staff-only embed.

## Duration formats

Examples:

- `30m`
- `2h`
- `7d`
- `1d12h`
- `perm`

Discord native timeouts cannot exceed 28 days.

## Setup

1. Install Python 3.10+.
2. Create your bot in the Discord Developer Portal.
3. Invite it with the `bot` and `applications.commands` scopes.
4. Give it:
   - Ban Members
   - Kick Members
   - Moderate Members
   - View Channels
   - Send Messages
   - Embed Links
5. Put the bot role ABOVE the members it needs to moderate.
6. Copy `.env.example` to `.env`.
7. Fill in:
   - `BOT_TOKEN`
   - `GUILD_ID`
   - `LOG_CHANNEL_ID`
   - optionally `STAFF_ROLE_ID`
8. Install dependencies:

    python -m pip install -r requirements.txt

9. Run:

    python bot.py

The bot creates `moderation.db` automatically.

## Staff workflow

A warning is as simple as:

    /warn @Steve Spamming

The bot records the warning, calculates the active warning count, posts a log, and checks the escalation rules.

History:

    /history @Steve

Case lookup:

    /case 42

## Security notes

- Never put your bot token in source code.
- Never commit `.env`.
- Never send your bot token to another person.
- The bot checks Discord permissions and role hierarchy before taking moderation actions.
- The staff log channel should be visible only to trusted staff.

## Changing the look

The colors can be changed in `.env` using decimal RGB integers. The defaults are already configured for the pastel cardboard-box theme.

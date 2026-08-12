# Delicate Bot 📦

A Discord moderation and server-management bot made for **Clouddyie’s Cardboard Box**.

Delicate provides moderation through both **Discord slash commands** and the **`d!` prefix**, alongside server settings, moderation logs, warning escalation, boost notifications, tickets, invite handling, and utility commands.

## ✦ Features

* 🔨 Ban members temporarily or permanently
* 👢 Kick members
* 🔇 Timeout / mute members
* ↩️ Remove timeouts
* ↩️ Unban users
* ⚠️ Warn members
* ⚡ Automatic warning escalation
* 📦 Persistent moderation history
* 🔎 Case lookup
* 📝 Moderation logs
* ⚙️ Per-server settings
* ⏱️ Automatic expiration of temporary bans and mutes
* 🎟️ Private support tickets
* 📄 Ticket transcripts
* 🪽 Server invite welcome DMs
* 🔗 Bot invite command
* ✦ Automatic help command
* 🏓 Ping / latency command
* 🪽 Boost notifications
* `/` slash commands
* `d!` prefix commands

## ✦ Commands

All main commands are available through both slash commands and the `d!` prefix.

| Slash          | Prefix          | Description                                     |
| -------------- | --------------- | ----------------------------------------------- |
| `/ban`         | `d!ban`         | Ban a member temporarily or permanently         |
| `/kick`        | `d!kick`        | Kick a member                                   |
| `/mute`        | `d!mute`        | Timeout a member                                |
| `/unmute`      | `d!unmute`      | Remove a member's timeout                       |
| `/warn`        | `d!warn`        | Give a member a warning                         |
| `/unban`       | `d!unban`       | Unban a user by Discord ID                      |
| `/history`     | `d!history`     | View moderation history                         |
| `/case`        | `d!case`        | Look up a moderation case                       |
| `/setlog`      | `d!setlog`      | Set the moderation log channel                  |
| `/setboost`    | `d!setboost`    | Set the boost notification channel              |
| `/setstaff`    | `d!setstaff`    | Set the staff role                              |
| `/settings`    | `d!settings`    | View server settings                            |
| `/setticket`   | `d!setticket`   | Configure and post the ticket panel             |
| `/ticket`      | `d!ticket`      | Post the configured ticket panel                |
| `/closeticket` | `d!closeticket` | Close the current ticket                        |
| `/help`        | `d!help`        | Show Delicate's command list                    |
| `/invite`      | `d!invite`      | Get Delicate's invite link                      |
| `/ping`        | `d!ping`        | Check Delicate's response and WebSocket latency |

## ✦ Prefix

The default prefix is:

`d!`

Examples:

```text
d!warn @user spamming
d!kick @user breaking the rules
d!mute @user 2h being disruptive
d!history @user
d!case 12
d!ping
```

The `d!` prefix remains available even when a server uses another configured prefix.

## ✦ Prefix Configuration

The prefix system supports server-specific prefixes.

Show the current prefix:

```text
d!prefix
```

Change the prefix:

```text
d!prefix set c!
```

Reset the prefix:

```text
d!prefix reset
```

Changing the prefix requires **Manage Server** permission.

## ✦ Warning Escalation

Warnings automatically escalate when a member reaches certain numbers of active warnings.

| Active warnings | Automatic action |
| --------------: | ---------------- |
|               3 | 1 hour timeout   |
|               5 | 1 day timeout    |
|               7 | Permanent ban    |

Escalations are stored as moderation cases and can appear in moderation logs.

## ✦ Temporary Moderation

Supported duration formats include:

```text
30m
2h
7d
1d12h
```

Permanent bans can use:

```text
perm
```

Supported units:

* `s` — seconds
* `m` — minutes
* `h` — hours
* `d` — days
* `w` — weeks

Discord timeouts cannot exceed 28 days.

Delicate automatically checks for expired temporary bans and timeouts and removes them when their expiration time is reached.

## ✦ Moderation History

Every moderation case receives a case number.

View recent history:

```text
/history @user
d!history @user
```

Look up a case:

```text
/case 42
d!case 42
```

Moderation history is stored persistently in SQLite.

## ✦ Moderation Logs

Administrators can configure the moderation log channel with:

```text
/setlog #channel
d!setlog #channel
```

Logs can contain:

* Action
* Target
* Moderator
* Reason
* Duration
* Case number
* Timestamp
* Automatic escalation details

## ✦ Server Settings

Delicate stores server configuration separately for each server.

Available settings include:

* Moderation log channel
* Boost notification channel
* Staff role
* Ticket panel channel

Configure them with:

```text
/setlog
/setboost
/setstaff
/setticket
```

View them with:

```text
/settings
d!settings
```

## ✦ Boost Notifications

Delicate can announce new server boosts in a configured channel.

Configure the channel with:

```text
/setboost #channel
d!setboost #channel
```

Boost announcements include the booster, current boost count, and server boost level.

A test command is also available:

```text
/testboost
d!testboost
```

## ✦ Tickets

Delicate includes a private support-ticket system.

Configure and post the ticket panel with:

```text
/setticket #channel
d!setticket #channel
```

The panel provides an **Open a Ticket** button.

When a user opens a ticket:

* A private text channel is created
* Only the ticket creator and staff can access it
* Delicate posts a welcome message
* A **Close Ticket** button is provided
* Users cannot open multiple tickets at the same time

Tickets can be closed through the button or:

```text
/closeticket
d!closeticket
```

When a ticket closes, Delicate can send a transcript to the configured moderation log channel.

## ✦ Invite Welcome DMs

When Delicate is invited to a server, it attempts to identify the user who added it through the server audit log.

The inviter receives a private welcome DM containing:

* The server Delicate joined
* A short introduction
* Basic setup commands
* Information about Delicate's features

This requires Delicate to have permission to view the server audit log.

If the inviter cannot be identified or their DMs are unavailable, Delicate safely skips the DM.

## ✦ Invite Command

Users can get Delicate's installation link with:

```text
/invite
d!invite
```

The generated link includes the required bot and application-command scopes.

## ✦ Help Command

Delicate includes a custom help command:

```text
/help
d!help
```

The help system is intended to show Delicate's available commands and descriptions.

## ✦ Ping

Delicate provides a simple latency check:

```text
/ping
d!ping
```

The response displays:

* Response time
* Discord WebSocket latency

Example:

```text
✦ delicate is awake ୨୧

♡ response · `276ms`
♡ websocket · `200ms`
```

## ✦ Database

Delicate uses SQLite.

The default database file is:

```text
moderation.db
```

The project uses a database package:

```text
database/
├── __init__.py
└── database.py
```

The database module handles:

* Moderation cases
* Warnings
* Warning counts
* Case expiration
* Moderation history
* Server settings
* Database initialization
* Database health checks

The bot imports the database implementation with:

```python
from database import database
```

Keep the `database/` package intact.

## ✦ Modules

Delicate can organize optional systems into modules.

Current module structure includes:

```text
modules/
├── __init__.py
├── boosts.py
└── tickets.py
```

The ticket system is loaded during bot startup.

## ✦ Requirements

* Python 3.10+
* discord.py 2.7+
* python-dotenv
* SQLite

Install dependencies:

```powershell
py -m pip install -U discord.py python-dotenv
```

The project also includes:

```text
requirements.txt
```

## ✦ Environment

Create a `.env` file in the project root.

Example:

```env
BOT_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here

DATABASE_PATH=moderation.db

COLOR_BAN=14423100
COLOR_KICK=16763187
COLOR_MUTE=11513775
COLOR_WARN=16772724
COLOR_UNBAN=11976299
COLOR_HISTORY=13224393
```

`GUILD_ID` is used for development/testing configuration and stale guild-command cleanup.

Never share your bot token.

Never commit `.env` to GitHub.

## ✦ Discord Developer Portal

For prefix commands to work, **Message Content Intent** must be enabled.

Go to:

**Discord Developer Portal → Your Application → Bot → Privileged Gateway Intents**

Enable the intents required by your enabled features.

For public slash-command use, make sure the bot is authorized with:

* `bot`
* `applications.commands`

## ✦ Bot Permissions

Recommended permissions include:

* View Channels
* Send Messages
* Embed Links
* Read Message History
* Manage Channels
* View Audit Log
* Kick Members
* Ban Members
* Moderate Members
* Manage Messages

Ticket creation requires permissions to create and manage ticket channels.

The bot cannot moderate members whose highest role is above or equal to the bot's highest role.

## ✦ Slash Command Sync

Delicate synchronizes its slash commands **globally** for public use.

Commands are synchronized automatically when the bot starts.

A normal startup should look similar to:

```text
🎟️ Tickets cog loaded.
Synced 19 global command(s).
Logged in as ...
```

The development guild cleanup runs separately to remove stale guild-scoped command registrations.

Global command updates can take some time to propagate through Discord.

## ✦ Running the Bot

From the project directory:

```powershell
py bot.py
```

## ✦ Testing

### Moderation

```text
/warn
/kick
/ban
/mute
/unmute
/unban
/history
/case
```

### Tickets

```text
/setticket
/ticket
/closeticket
```

### Utilities

```text
/help
/invite
/ping
```

### Boosts

```text
/testboost
```

### Invite DM testing

The temporary owner-only testing command is:

```text
/testinvitedm
d!testinvitedm
```

This simulates the invite welcome DM without requiring Delicate to be invited into another server.

## ✦ Common Problems

### Prefix commands do nothing

Check:

1. Message Content Intent is enabled.
2. The bot can read messages in the channel.
3. The bot was restarted after changing intents.
4. You are using `d!` or the server's configured prefix.

### Slash commands are missing

Check:

1. The bot was installed with `applications.commands`.
2. The bot is present in the server.
3. Global synchronization completed successfully.
4. Discord has had enough time to propagate global commands.
5. The Discord client is up to date.

If commands appear on one Discord client but not another, restart or update the affected client.

### Commands appear twice

This usually indicates stale guild-scoped registrations.

Delicate clears the configured development guild's old command registrations during startup before syncing the current global commands.

### Ticket creation fails

Check:

* Manage Channels
* View Channels
* Send Messages
* Read Message History
* Embed Links
* The bot's ability to create channels in the chosen category

Also make sure a ticket panel has been configured with:

```text
/setticket #channel
```

### Ticket transcripts are missing

Make sure a moderation log channel is configured:

```text
/setlog #channel
```

### The bot cannot moderate someone

Check:

* Bot permissions
* Moderator permissions
* Staff role
* Bot role hierarchy
* Target member's role hierarchy

### Invite welcome DM does not arrive

Check:

* Delicate can view the server audit log
* The inviter allows direct messages from the server
* The audit-log entry is available after Delicate joins

### Database errors

Make sure the project contains:

```text
database/
├── __init__.py
└── database.py
```

Keep `moderation.db` intact.

Delicate uses SQLite and initializes its tables automatically.

## ✦ Project Structure

A typical project looks like:

```text
delicate-bot/
│
├── bot.py
├── moderation.db
├── .env
├── .env.example
├── README.md
├── CHANGELOG.md
├── requirements.txt
│
├── database/
│   ├── __init__.py
│   └── database.py
│
└── modules/
    ├── __init__.py
    ├── boosts.py
    └── tickets.py
```

## ✦ Security

Never commit:

```text
.env
```

Never publish:

```text
BOT_TOKEN
```

If your bot token is accidentally exposed, regenerate it immediately in the Discord Developer Portal.

The SQLite database may contain moderation records and ticket information, so treat it as private data.

## ✦ Current Status

Delicate currently provides:

* ✅ Prefix moderation commands
* ✅ Global slash moderation commands
* ✅ SQLite persistence
* ✅ Moderation cases
* ✅ Persistent warnings
* ✅ Automatic warning escalation
* ✅ Temporary bans
* ✅ Temporary timeouts
* ✅ Automatic expiration
* ✅ Moderation history
* ✅ Case lookup
* ✅ Server settings
* ✅ Moderation logging
* ✅ Staff permission checks
* ✅ Configurable server prefixes
* ✅ Public multi-server slash-command support
* ✅ Boost notifications
* ✅ Invite welcome DMs
* ✅ Bot invite command
* ✅ Custom help command
* ✅ Ping command
* ✅ Private support tickets
* ✅ Ticket close buttons
* ✅ Ticket transcripts

## ✦ Credits

Made for **Clouddyie’s Cardboard Box**.

Built with:

* Python
* discord.py
* SQLite
* python-dotenv

**Delicate — soft colors, hard moderation.** 📦🎀

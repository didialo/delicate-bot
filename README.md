# Delicate Bot 📦

A cozy Discord moderation and server-management bot built to help communities stay **safe, organized, and comfortable**.

Delicate provides moderation through both **Discord slash commands** and the **`d!` prefix**, along with server configuration, boost notifications, private support tickets, invite welcome messages, and useful server utilities.

## ✦ Features

* 🔨 Ban members
* 👢 Kick members
* 🔇 Timeout / mute members
* ↩️ Remove timeouts
* ↩️ Unban users
* ⚠️ Warn members
* 📦 Moderation history
* 🔎 Case lookup
* ⚡ Automatic warning escalation
* 📝 Moderation logs
* ⚙️ Per-server settings
* ⏱️ Automatic expiration of temporary bans and mutes
* 🪽 Server boost notifications
* 🎟️ Private support tickets
* 📄 Ticket transcripts
* ✦ Invite welcome DMs
* 📋 Help command
* 🔗 Bot invite command
* 🏓 Ping / latency command
* `/` slash commands
* `d!` prefix commands

## ✦ Commands

All moderation and utility commands work with both slash commands and prefix commands.

| Slash           | Prefix           | Description                             |
| --------------- | ---------------- | --------------------------------------- |
| `/ban`          | `d!ban`          | Ban a member temporarily or permanently |
| `/kick`         | `d!kick`         | Kick a member                           |
| `/mute`         | `d!mute`         | Timeout a member                        |
| `/unmute`       | `d!unmute`       | Remove a member's timeout               |
| `/warn`         | `d!warn`         | Give a member a warning                 |
| `/unban`        | `d!unban`        | Unban a user by Discord ID              |
| `/history`      | `d!history`      | View moderation history                 |
| `/case`         | `d!case`         | Look up a moderation case               |
| `/setlog`       | `d!setlog`       | Set the moderation log channel          |
| `/setboost`     | `d!setboost`     | Set the boost notification channel      |
| `/setstaff`     | `d!setstaff`     | Set the staff role                      |
| `/settings`     | `d!settings`     | View server settings                    |
| `/setticket`    | `d!setticket`    | Set the ticket panel channel            |
| `/ticket`       | `d!ticket`       | Post the ticket panel                   |
| `/closeticket`  | `d!closeticket`  | Close the current ticket                |
| `/help`         | `d!help`         | Show Delicate's commands                |
| `/invite`       | `d!invite`       | Get Delicate's invite link              |
| `/ping`         | `d!ping`         | Check Delicate's latency                |
| `/testboost`    | `d!testboost`    | Test the server boost announcement      |
| `/testinvitedm` | `d!testinvitedm` | Test Delicate's invite welcome DM       |

Testing commands are intended for development and testing.

## ✦ Prefix

The default prefix is:

`d!`

Examples:

`d!warn @user spamming`

`d!kick @user breaking the rules`

`d!mute @user 2h being disruptive`

`d!history @user`

`d!case 12`

The `d!` prefix remains available even when a server uses another configured prefix.

## ✦ Prefix Configuration

The prefix system supports server-specific prefixes.

Show the current prefix:

`d!prefix`

Change the prefix:

`d!prefix set c!`

Reset the prefix:

`d!prefix reset`

For example, a server using `c!` can use:

`c!warn @user spamming`

and `d!warn @user spamming` will still work.

Changing the prefix requires **Manage Server** permission.

## ✦ Warning Escalation

Warnings automatically escalate when a member reaches certain numbers of active warnings.

| Active warnings | Automatic action |
| --------------: | ---------------- |
|               3 | 1 hour timeout   |
|               5 | 1 day timeout    |
|               7 | Permanent ban    |

The escalation is stored as a moderation case and can appear in the moderation logs.

## ✦ Temporary Moderation

Supported duration formats include:

`30m`

`2h`

`7d`

`1d12h`

Permanent bans can use:

`perm`

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

`/history @user`

or:

`d!history @user`

Look up a case:

`/case 42`

or:

`d!case 42`

Moderation history is stored persistently in SQLite.

## ✦ Moderation Logs

Administrators can configure the moderation log channel with:

`/setlog #channel`

or:

`d!setlog #channel`

Logs contain information such as:

* Action
* Target
* Moderator
* Reason
* Duration
* Case number
* Timestamp
* Automatic escalation details when applicable

Ticket transcripts are also sent to the configured moderation log channel when tickets are closed.

## ✦ Boost Notifications

Delicate can announce when a member starts boosting the server.

Configure the boost notification channel with:

`/setboost #channel`

or:

`d!setboost #channel`

Test the boost announcement with:

`/testboost`

or:

`d!testboost`

Boost notifications include the member, current boost count, and current server boost level.

## ✦ Support Tickets

Delicate includes a private support ticket system.

Configure the ticket panel channel with:

`/setticket #channel`

or:

`d!setticket #channel`

Post the ticket panel with:

`/ticket`

or:

`d!ticket`

Members can then use the **🎟️ open a ticket** button.

Each ticket:

* Creates a private text channel
* Is visible to the ticket author
* Is visible to the configured staff role
* Prevents multiple open tickets from the same user
* Includes a **🔒 close ticket** button

Tickets can also be closed with:

`/closeticket`

or:

`d!closeticket`

When a ticket is closed, Delicate generates a text transcript and sends it to the configured moderation log channel.

## ✦ Invite Welcome DM

When Delicate joins a new server, it attempts to identify the person who invited it through the server audit log.

The inviter receives a private welcome message containing:

* The server name
* A Delicate welcome message
* Basic setup instructions
* Server configuration commands

Delicate requires **View Audit Log** permission to reliably identify the inviter.

If the inviter cannot be determined or their DMs are unavailable, Delicate safely continues without crashing.

The invite DM can be tested without adding Delicate to another server:

`/testinvitedm`

or:

`d!testinvitedm`

## ✦ Help Command

Use:

`/help`

or:

`d!help`

to display Delicate's available commands.

## ✦ Invite Command

Use:

`/invite`

or:

`d!invite`

to get Delicate's invite link.

The generated invite includes both:

* `bot`
* `applications.commands`

## ✦ Ping Command

Use:

`/ping`

or:

`d!ping`

to check Delicate's latency.

The command reports:

* Command response time
* Discord WebSocket latency

Example:

```text
✦ delicate is awake ୨୧

♡ response · `276ms`
♡ websocket · `200ms`
```

## ✦ Server Settings

Delicate stores configuration separately for each server.

Available settings:

* Moderation log channel
* Boost notification channel
* Staff role
* Ticket panel channel

Configure them with:

`/setlog`

`/setboost`

`/setstaff`

`/setticket`

View them with:

`/settings`

## ✦ Database

Delicate uses SQLite.

The default database file is:

`moderation.db`

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
* Ticket configuration
* Database initialization
* Database health checks

The database is initialized automatically when the module is imported.

### Important

The bot imports the database implementation with:

```python
from database import database
```

The actual database implementation is located at:

```text
database/database.py
```

Make sure `database/__init__.py` exists.

Do not replace the database package with an unrelated `database.py` file in the project root.

## ✦ Requirements

* Python 3.10+
* discord.py
* python-dotenv

Install dependencies:

```powershell
py -m pip install -U discord.py python-dotenv
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

`GUILD_ID` is optional and can be kept for development/testing configuration. Slash commands are synchronized globally for public server use.

Never share your bot token.

Never commit `.env` to GitHub.

## ✦ Discord Developer Portal

For prefix commands to work, **Message Content Intent must be enabled**.

Go to:

**Discord Developer Portal → Your Application → Bot → Privileged Gateway Intents**

Enable:

* **Message Content Intent**
* **Server Members Intent** when required by the bot's features

For slash commands, make sure the application is authorized with both:

* `bot`
* `applications.commands`

For invite detection, Delicate also needs:

* **View Audit Log**

## ✦ Bot Permissions

Recommended permissions:

* View Channels
* Send Messages
* Embed Links
* Read Message History
* Manage Channels
* Manage Messages
* Kick Members
* Ban Members
* Moderate Members
* View Audit Log

The bot cannot moderate members whose highest role is above or equal to the bot's highest role.

Ticket creation also requires permission to create channels and manage their permission overwrites.

## ✦ Slash Command Sync

Delicate synchronizes its slash commands globally when the bot starts.

A successful startup should look similar to:

```text
🎟️ Tickets cog loaded.
Synced 19 global command(s).
Logged in as ...
```

Delicate also clears stale development-server command registrations when `GUILD_ID` is configured.

Global command updates can take some time to propagate through Discord.

## ✦ Running the Bot

From the project directory:

```powershell
py bot.py
```

## ✦ Testing

### Slash commands

```text
/warn
/kick
/ban
/mute
/unmute
/unban
/history
/case
/settings
/setticket
/ticket
/closeticket
/help
/invite
/ping
```

### Prefix commands

```text
d!warn
d!kick
d!ban
d!mute
d!unmute
d!unban
d!history
d!case
d!settings
d!setticket
d!ticket
d!closeticket
d!help
d!invite
d!ping
```

### Testing commands

```text
/testboost
d!testboost

/testinvitedm
d!testinvitedm
```

## ✦ Common Problems

### Prefix commands do nothing

Check:

1. Message Content Intent is enabled in the Discord Developer Portal.
2. The bot has permission to view and read messages in the channel.
3. The bot was restarted after changing its intents.
4. You are using `d!` or the server's configured prefix.

### Slash commands are missing

Check:

1. The bot was installed with `applications.commands`.
2. The bot is present in the server.
3. Global command synchronization completed successfully.
4. Discord has had enough time to propagate the global commands.
5. The Discord client is up to date.

If commands appear on one Discord client but not another, restart or update the affected client.

### Tickets cannot be created

Check:

* The ticket panel was configured with `/setticket` or `d!setticket`
* The bot can create channels
* The bot can manage channel permissions
* The configured staff role exists
* The configured ticket panel channel still exists

### Invite welcome DMs do not arrive

Check:

* Delicate has permission to view the audit log
* The inviter allows DMs
* Discord created a usable audit-log entry for the bot addition

### The bot cannot moderate someone

Check:

* Bot permissions
* Moderator permissions
* Staff role
* Bot role hierarchy
* Target member's role hierarchy

### Database errors

If you receive an error involving a database function, make sure the `database/` package contains:

```text
database/
├── __init__.py
└── database.py
```

and that `database/database.py` contains the required functions.

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

The SQLite database may contain moderation records and ticket transcripts, so treat it as private data.

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
* ✅ Private support tickets
* ✅ Ticket transcripts
* ✅ Invite welcome DMs
* ✅ Help command
* ✅ Invite command
* ✅ Ping command

## ✦ Credits

Built for Discord communities that want moderation without losing a little personality. 📦🎀

Built with:

* Python
* discord.py
* SQLite
* python-dotenv

**Delicate — soft colors, hard moderation.** 📦🎀

# Delicate Bot 📦

A Discord moderation bot made for **Clouddyie's Cardboard Box**.

Delicate provides moderation through both **Discord slash commands** and the **`d!` prefix**.

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
* `/` slash commands
* `d!` prefix commands

## ✦ Commands

All moderation commands work with both slash commands and prefix commands.

| Slash       | Prefix       | Description                             |
| ----------- | ------------ | --------------------------------------- |
| `/ban`      | `d!ban`      | Ban a member temporarily or permanently |
| `/kick`     | `d!kick`     | Kick a member                           |
| `/mute`     | `d!mute`     | Timeout a member                        |
| `/unmute`   | `d!unmute`   | Remove a member's timeout               |
| `/warn`     | `d!warn`     | Give a member a warning                 |
| `/unban`    | `d!unban`    | Unban a user by Discord ID              |
| `/history`  | `d!history`  | View moderation history                 |
| `/case`     | `d!case`     | Look up a moderation case               |
| `/setlog`   | `d!setlog`   | Set the moderation log channel          |
| `/setboost` | `d!setboost` | Set the boost notification channel      |
| `/setstaff` | `d!setstaff` | Set the staff role                      |
| `/settings` | `d!settings` | View server settings                    |

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

## ✦ Server Settings

Delicate stores server configuration separately for each server.

Available settings:

* Moderation log channel
* Boost notification channel
* Staff role

Configure them with:

`/setlog`

`/setboost`

`/setstaff`

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
* Database initialization
* Database health checks

The database is initialized automatically when the module is imported.

### Important

The bot imports the database package with:

```python
import database
```

The actual database implementation is located in:

```text
database/database.py
```

Make sure `database/__init__.py` exists.

Do not replace the database package with an unrelated `database.py` file in the project root.

## ✦ Database Troubleshooting

If you see:

```text
AttributeError: module 'database' has no attribute 'create_case'
```

Python is probably importing the wrong `database` package/module.

Check what Python is importing:

```powershell
py -c "import database; print(database.__file__); print(hasattr(database, 'create_case')); print(hasattr(database, 'get_expired_cases')); print(hasattr(database, 'get_guild_setting'))"
```

The functions should report:

```text
True
True
True
```

If `database.__file__` is `None` and Python reports a namespace package, check that:

```text
database/__init__.py
```

exists.

Keep `moderation.db` intact. Delicate uses `CREATE TABLE IF NOT EXISTS`, so an existing database is preserved.

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

Never share your bot token.

Never commit `.env` to GitHub.

## ✦ Discord Developer Portal

For prefix commands to work, **Message Content Intent must be enabled**.

Go to:

**Discord Developer Portal → Your Application → Bot → Privileged Gateway Intents**

Enable:

* **Message Content Intent**
* **Server Members Intent** when required by the bot's features

If slash commands work but commands such as:

`d!warn`

`d!ban`

`d!kick`

do nothing, check **Message Content Intent first**.

The bot also needs the appropriate Discord permissions for the moderation actions it performs.

Make sure the bot's role is above the members it needs to moderate.

## ✦ Bot Permissions

Recommended permissions:

* View Channels
* Send Messages
* Embed Links
* Read Message History
* Kick Members
* Ban Members
* Moderate Members

The bot cannot moderate members whose highest role is above or equal to the bot's highest role.

## ✦ Running the Bot

From the project directory:

```powershell
py bot.py
```

A successful startup should look similar to:

```text
Synced commands to guild ...
Logged in as ...
```

The exact number of commands may change as features are added.

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
```

### Prefix configuration

```text
d!prefix
d!prefix set c!
d!prefix reset
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

* `GUILD_ID` is correct.
* The bot has the `applications.commands` scope.
* The bot can access the guild.
* Command synchronization succeeds during startup.

### The bot cannot moderate someone

Check:

* Bot permissions
* Moderator permissions
* Staff role
* Bot role hierarchy
* Target member's role hierarchy

### Database errors

If you receive an error involving `database.create_case`, `database.get_expired_cases`, or another database function, make sure the `database/` package contains:

```text
database/
├── __init__.py
└── database.py
```

and that `database/database.py` contains the required functions.

## ✦ Project Structure

A typical project looks like:

```text
delicate-bot/
│
├── bot.py
├── moderation.db
├── .env
├── .env.example
│
├── database/
│   ├── __init__.py
│   └── database.py
│
└── modules/
    └── prefixes.py
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

The SQLite database may contain moderation records, so treat it as private data.

## ✦ Current Status

Delicate currently provides:

* ✅ Prefix moderation commands
* ✅ Slash moderation commands
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

## ✦ Credits

Made for **Clouddyiie's Cardboard Box**.

Built with:

* Python
* discord.py
* SQLite
* python-dotenv

**Delicate — soft colors, hard moderation.** 📦🎀

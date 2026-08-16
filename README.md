# 📦 Delicate

> A cozy, pastel-styled Discord moderation bot built to keep servers safe, calm, and organized without losing a little personality.

Delicate is a Python-based Discord moderation bot focused on practical server management with a soft, welcoming personality. It combines moderation, persistent warnings, support tickets, suggestions, server configuration, Server Tag rewards, invite welcome DMs, SQLite storage, and Delicate-specific server tools in one little cardboard box. ☁️📦

> **Delicate — keeping things safe, calm, and cozy.** ୨୧

---

## ✦ Features

### 🛡️ Moderation

Delicate includes a complete moderation workflow with persistent cases and configurable server staff roles.

* 🔨 Temporary and permanent bans
* 👢 Member kicks
* 🔇 Member timeouts
* ⚠️ Persistent warnings
* ⚡ Automatic warning escalation
* ↩️ Unbans and timeout removal
* 📋 Moderation history
* 🔎 Individual case lookup
* 📝 Moderation log embeds
* 🧹 Message purging
* 🔒 Channel locking and unlocking
* 👁️ Channel hiding and unhiding
* 🐌 Channel slowmode

### ⚠️ Warning Escalation

Warnings are stored in SQLite and can automatically escalate into stronger moderation actions.

| Active warnings | Action         |
| --------------: | :------------- |
|               3 | 1 hour timeout |
|               5 | 1 day timeout  |
|               7 | Permanent ban  |

```py
WARN_ESCALATION = [
    (3, "MUTE", "1h"),
    (5, "MUTE", "1d"),
    (7, "BAN", "perm"),
]
```

### 🎟️ Support Tickets

Delicate includes a persistent private ticket system designed for simple staff support.

```text
/setticket <channel>
/ticket
/closeticket
```

Tickets support:

* Private ticket channels
* Member-only access
* Configured staff-role access
* One open ticket per member
* Persistent ticket buttons
* Automatic transcript generation
* Transcript delivery to the configured log channel
* Ticket panels that continue working after bot restarts

### 💡 Suggestions

Servers can configure a dedicated suggestion channel and let members submit suggestions directly through Delicate.

```text
/setsuggest <channel>
/suggest <message>
/suggestapprove <suggestion_id>
/suggestdeny <suggestion_id>
```

Suggestions are stored persistently with their author, message, status, timestamps, and Discord message information.

### 🏷️ Server Tag Rewards

Delicate can give members a configurable reward role through a persistent Server Tag reward panel.

```text
/setreward <role>
/tag
```

The reward button lets members toggle the configured role while Delicate checks that it can safely manage the role.

### 📢 Announcements

Staff can send polished announcement embeds to any text channel, with optional attachments.

```text
/announce <channel> <message> [attachment]
```

The command supports images, videos, and other files uploaded with the command.

### 🚀 Server Boost Configuration

Delicate stores a dedicated boost notification channel as part of its persistent server configuration.

```text
/setboost <channel>
```

### ✉️ Invite Welcome DMs

When Delicate joins a server, it checks the Discord audit log to determine who invited it and attempts to send that person a private welcome message.

For development and testing:

```text
/testinvitedm
d!testinvitedm
```

### 🚫 Guild Blacklist

Developer-only controls allow Delicate to permanently blacklist a guild from using the bot.

```text
/blacklist <server_id>
/unblacklist <server_id>
```

---

## ✦ Delicate Systems

These are specialized tools built specifically around Delicate's identity rather than standard moderation functionality.

### 📦 `/snapshot`

Save a lightweight snapshot of the current server state.

Snapshots can store:

* Server member count
* Channel count
* Role count
* Boost count and level
* Delicate configuration
* Snapshot name and creator
* Creation timestamp

Example:

```text
d!snapshot before-event
```

### 🛡️ `/handoff`

Generate a staff handoff report for moderators taking over a shift.

The report includes:

* Active moderation cases
* Active warnings
* Pending suggestions
* Recent moderation activity
* Handoff timestamp

### ♡ `/heartbeat`

Check Delicate's internal systems.

The heartbeat checks systems such as:

* Database
* Moderation logging
* Staff configuration
* Suggestions
* Boost configuration
* Server Tag rewards
* Background expiration worker
* Gateway latency

Example output:

```text
♡ DELICATE HEARTBEAT

database .......... 💗 healthy
logging ........... 💗 healthy
staff ............. 💗 healthy
suggestions ....... 💗 healthy
boosts ............ 💗 healthy
rewards ........... 💗 healthy
worker ............ 💗 healthy
```

### 🪽 `/foster`

Assign a temporary staff guardian to a member.

```text
d!foster @member @staff 1h
```

Foster assignments are persistent and include:

* Member
* Guardian
* Duration
* Expiration time
* Assignment timestamp

### ☁️ `/echo`

Connect a member's recent moderation events into one timeline.

```text
d!echo @member
```

Delicate combines recorded moderation cases and warnings into a single chronological view.

---

## ✦ Commands

Delicate currently provides **42 registered commands**, available primarily as hybrid slash + prefix commands.

The default prefix is:

```text
d!
```

### General

| Command        | Description                        |
| -------------- | ---------------------------------- |
| `/about`       | View Delicate's information card   |
| `/help`        | Show Delicate's commands           |
| `/invite`      | Get Delicate's invite link         |
| `/membercount` | Show server member statistics      |
| `/ping`        | Check connection and system status |

### Moderation

| Command     | Description                             |
| ----------- | --------------------------------------- |
| `/ban`      | Ban a member temporarily or permanently |
| `/kick`     | Kick a member                           |
| `/mute`     | Timeout a member                        |
| `/warn`     | Give a member a warning                 |
| `/unban`    | Unban a user by Discord ID              |
| `/unmute`   | Remove a member's timeout               |
| `/history`  | Show moderation history                 |
| `/case`     | Look up a moderation case               |
| `/purge`    | Delete recent messages                  |
| `/slowmode` | Set or disable channel slowmode         |
| `/hide`     | Hide the current channel                |
| `/unhide`   | Unhide the current channel              |
| `/lock`     | Lock the current channel                |
| `/unlock`   | Unlock the current channel              |

### Server Configuration

| Command       | Description                        |
| ------------- | ---------------------------------- |
| `/settings`   | View current server settings       |
| `/setlog`     | Set the moderation log channel     |
| `/setboost`   | Set the boost notification channel |
| `/setstaff`   | Set the staff role                 |
| `/setsuggest` | Set the suggestion channel         |
| `/setreward`  | Set the Server Tag reward role     |
| `/setticket`  | Set the ticket panel channel       |

### Suggestions

| Command           | Description          |
| ----------------- | -------------------- |
| `/suggest`        | Submit a suggestion  |
| `/suggestapprove` | Approve a suggestion |
| `/suggestdeny`    | Deny a suggestion    |

### Tickets

| Command        | Description                      |
| -------------- | -------------------------------- |
| `/ticket`      | Post the configured ticket panel |
| `/closeticket` | Close the current ticket         |

### Delicate Systems

| Command      | Description                                                   |
| ------------ | ------------------------------------------------------------- |
| `/snapshot`  | Save a lightweight snapshot of the current server state       |
| `/handoff`   | Create a staff shift handoff summary                          |
| `/heartbeat` | Check Delicate's internal systems                             |
| `/foster`    | Assign a temporary staff guardian to a member                 |
| `/echo`      | Connect a member's recent moderation events into one timeline |
| `/tag`       | Show the Server Tag reward and claim button                   |

### Developer

| Command         | Description                       |
| --------------- | --------------------------------- |
| `/blacklist`    | Permanently blacklist a guild     |
| `/unblacklist`  | Remove a guild from the blacklist |
| `/shutdown`     | Shut down Delicate                |
| `/testinvitedm` | Test the invite welcome DM        |

> Prefix equivalents use `d!` instead of `/` where supported. Some commands are restricted to staff, administrators, or developers.

---

## ✦ Server Configuration

Delicate stores per-server configuration persistently through SQLite.

```text
/setlog <channel>
/setboost <channel>
/setstaff <role>
/setsuggest <channel>
/setreward <role>
/setticket <channel>
/settings
```

Current configuration can include:

* Moderation log channel
* Boost notification channel
* Staff role
* Suggestion channel
* Server Tag reward role
* Ticket panel channel

---

## ✦ Duration Formats

Temporary moderation accepts compact duration formats such as:

```text
30s
30m
2h
7d
1d12h
2w
perm
```

Supported units:

```text
s = seconds
m = minutes
h = hours
d = days
w = weeks
```

Multiple units may be combined, such as `1d12h`.

Discord's native timeout limit still applies: member timeouts cannot exceed 28 days.

---

## ✦ Persistent Data

Delicate uses SQLite for persistent storage.

The database keeps information such as:

* Moderation cases
* Warning records
* Server settings
* Blacklisted guilds
* Suggestions
* Ticket configuration
* Delicate snapshots
* Foster assignments

By default, Delicate uses:

```text
moderation.db
```

The database path can be customized through `.env`:

```env
DATABASE_PATH=moderation.db
```

---

## ✦ Runtime & Status

Delicate's `/ping` command reports:

* Gateway latency
* Discord round-trip response time
* Bot uptime
* Process memory usage
* Python version
* discord.py version
* Operating system
* CPU information

Delicate also runs a background expiration worker every 30 seconds to process expired temporary bans and timeouts.

---

## ✦ Design

Delicate follows a soft, pastel visual identity inspired by **Clouddyie's Cardboard Box**.

The design language focuses on:

* ☁️ Soft clouds
* 📦 Handmade cardboard details
* 🪽 Gentle pastel colors
* ♡ Cozy, welcoming wording
* ୨୧ Small decorative accents

Moderation actions use distinct colors so important actions remain easy to recognize, while tickets, suggestions, settings, and Delicate's special systems share the same cozy visual language.

> **soft colors, hard moderation.** 🎀📦

---

## ✦ Tech Stack

* **Python**
* **discord.py 2.7+**
* **SQLite**
* **python-dotenv**
* **psutil**
* **Discord API**

---

## ✦ Requirements

* Python 3.10+
* A Discord application and bot account
* A Discord bot token
* A server for testing

Recommended bot permissions include:

* Ban Members
* Kick Members
* Moderate Members
* Manage Channels
* Manage Messages
* Manage Roles
* View Channels
* Send Messages
* Embed Links
* Attach Files
* Read Message History

Delicate's role must be above members it needs to moderate and above roles it needs to assign.

---

## ✦ Installation

Clone the repository:

```bash
git clone https://github.com/didialo/delicate-bot.git
cd delicate-bot
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a `.env` file and configure at least:

```env
BOT_TOKEN=your_bot_token
GUILD_ID=your_test_server_id
DEV_USER_ID=your_discord_user_id
```

Optional database and color configuration can also be provided:

```env
DATABASE_PATH=moderation.db
COLOR_BAN=14423100
COLOR_KICK=16763187
COLOR_MUTE=11513775
COLOR_WARN=16772724
COLOR_UNBAN=11976299
COLOR_HISTORY=13224393
```

Start the bot:

```bash
python bot.py
```

On startup, Delicate initializes its database, loads the ticket and special systems, synchronizes its slash commands, and starts its expiration worker.

> Never share your bot token or commit `.env` to a public repository.

---

## ✦ Project Structure

```text
delicate-bot/
├── bot.py
├── database/
│   └── database.py
├── modules/
│   ├── tickets.py
│   └── special.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CHANGELOG.md
├── PRIVACY.md
├── TERMS.md
└── LICENSE.txt
```

---

## ✦ Security & Permissions

* Never place your bot token in source code.
* Never commit `.env`.
* Keep moderation logs and ticket transcripts private.
* Only give staff roles to trusted members.
* Keep the SQLite database private when it contains moderation records.
* Developer-only commands are protected by the configured developer ID or owner checks.
* Moderation commands respect Discord permission and role hierarchy checks.
* Blacklisted guilds are blocked from using Delicate.

---

## ✦ Credits

**Delicate** is an original fan-made Discord bot project built around the cozy **Clouddyiie's Cardboard Box** aesthetic.

---

## ✦ License

Delicate is licensed under the MIT License.

See [`LICENSE.txt`](LICENSE.txt) for the full license text.

---

## ✦ Current Status

```text
// PROJECT: DELICATE
// VERSION: 2.1.0
// COMMANDS: 42
// SPECIAL SYSTEMS: 5
// DATABASE: SQLITE
// TICKETS: ACTIVE
// MODERATION: ACTIVE
// STATUS: STABLE
```

# 📦 "keeping things cozy ୨୧"

# 📦 Delicate

A cozy, pastel-styled Discord moderation bot built for servers that want powerful moderation tools without losing a little personality.

Delicate combines moderation, server utilities, private support tickets, suggestions, boost announcements, invite handling, persistent configuration, and SQLite storage into one bot.

> **Delicate — soft colors, hard moderation.** 🎀📦

## ✨ Features

* 🔨 Temporary and permanent bans
* 👢 Member kicks
* 🔇 Member timeouts
* ⚠️ Persistent warnings
* ⚡ Automatic warning escalation
* ↩️ Unbans and timeout removal
* 📋 Persistent moderation history
* 🔎 Individual case lookup
* 📝 Staff moderation logs
* 🎟️ Private support tickets
* 📄 Automatic ticket transcripts
* 💡 Suggestion system
* 🐌 Channel slowmode
* 📦 Server boost announcements
* ✉️ Invite welcome DMs
* 🛡️ Developer guild blacklist system
* ⚙️ Persistent per-server configuration
* 🎨 Customizable embed colors
* 💾 SQLite database storage
* 🪽 Configurable command prefixes
* 📡 WebSocket latency reporting

## 🛡️ Moderation

Delicate supports both slash commands and prefix commands for its main moderation tools.

```text
/ban <member> <duration> <reason>
/kick <member> <reason>
/mute <member> <duration> <reason>
/warn <member> <reason>

/unban <user_id> <reason>
/unmute <member> <reason>

/history <member> <limit>
/case <case_id>
```

Moderation actions are protected by Discord permissions, staff-role configuration, and role hierarchy checks.

## ⚠️ Warning Escalation

Warnings are stored persistently and can automatically escalate into stronger moderation actions.

The default thresholds are:

| Active warnings | Action         |
| --------------: | -------------- |
|               3 | 1 hour timeout |
|               5 | 1 day timeout  |
|               7 | Permanent ban  |

The thresholds are configured in `bot.py`:

```py
WARN_ESCALATION = [
    (3, "MUTE", "1h"),
    (5, "MUTE", "1d"),
    (7, "BAN", "perm"),
]
```

Only the highest threshold reached is applied.

For example, reaching 5 warnings triggers the 5-warning action rather than both the 3-warning and 5-warning actions.

## 🎟️ Support Tickets

Delicate includes a persistent private ticket system.

```text
/setticket <channel>
/ticket
/closeticket
```

Tickets support:

* Private ticket channels
* Staff-role access
* One open ticket per user
* Persistent buttons
* Automatic transcript generation
* Transcript logging
* Ticket panels that continue working after restarts

Ticket transcripts can be sent to the configured moderation log channel when a ticket is closed.

## 💡 Suggestions

Servers can configure a dedicated suggestion channel and allow members to submit suggestions.

```text
/setsuggest <channel>
/suggest <message>
```

Suggestions are stored in SQLite with a unique ID, author, message content, status, timestamps, and Discord message information.

## 🐌 Slowmode

Delicate can configure slowmode directly from Discord:

```text
/slowmode <seconds>
```

Use `0` to disable slowmode.

```text
/slowmode 10
```

enables a 10-second delay.

```text
/slowmode 0
```

disables it.

The maximum supported value is `21600` seconds.

## 📦 Server Boosts

Delicate can automatically announce server boosts in a configured channel.

Boost announcements can display:

* The member who boosted
* Current boost count
* Current boost level
* Member avatar
* Cardboard Box-inspired styling

Configure the boost channel with:

```text
/setboost <channel>
```

The announcement system can also be tested with:

```text
/testboost
d!testboost
```

## ✉️ Invite Welcome DMs

When Delicate joins a server, it can detect the inviter through the Discord audit log and send them a private welcome message.

For development and testing:

```text
/testinvitedm
d!testinvitedm
```

The system safely handles cases where the inviter cannot receive direct messages.

## 🪽 Prefix System

The default prefix is:

```text
d!
```

Delicate always keeps `d!` available, even when a server configures a different custom prefix.

```text
d!prefix
d!prefix set c!
d!prefix reset
```

Custom prefixes can be up to 5 characters long.

Changing the prefix requires the **Manage Server** permission.

## ✦ Utility Commands

Delicate also provides general utility commands:

```text
/help
/invite
/ping
```

Prefix equivalents are also available:

```text
d!help
d!invite
d!ping
```

The ping command reports the bot's response time and WebSocket latency.

## ⚙️ Server Configuration

Delicate stores server configuration persistently.

Available configuration commands include:

```text
/setlog <channel>
/setboost <channel>
/setstaff <role>
/setsuggest <channel>
/setsuggestion <channel>

/settings
/resetsettings
```

Configuration can include:

* Moderation log channel
* Boost announcement channel
* Staff role
* Suggestion channel
* Ticket panel configuration
* Additional persistent server settings

## 💾 Database

Delicate uses SQLite for persistent data storage.

The database stores information such as:

* Moderation cases
* Warnings
* Server settings
* Blacklisted guilds
* Suggestions
* Ticket configuration

By default:

```text
moderation.db
```

The database path can be changed through `.env`:

```env
DATABASE_PATH=moderation.db
```

## 🎨 Design

Delicate uses a soft pastel visual style inspired by **Clouddyiе's Cardboard Box** aesthetic.

Different moderation actions use dedicated colors while utility, ticket, suggestion, and boost systems follow the same overall visual language.

Embed colors can be customized through environment variables.

## ⏱️ Duration Formats

Temporary moderation supports formats such as:

```text
30m
2h
7d
1d12h
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

Multiple units can be combined.

Discord's native timeout limit of 28 days still applies to member timeouts.

## 🛠️ Setup

### Requirements

* Python 3.10+
* A Discord application
* A Discord bot token
* A Discord server for testing

### 1. Create the bot

Create an application through the Discord Developer Portal and create a bot user.

Invite Delicate using:

```text
bot
applications.commands
```

Recommended permissions include:

* Ban Members
* Kick Members
* Moderate Members
* Manage Channels
* View Channels
* Send Messages
* Embed Links
* Attach Files
* Read Message History

Make sure Delicate's role is above the members it needs to moderate.

### 2. Configure `.env`

Copy:

```text
.env.example
```

to:

```text
.env
```

Then configure:

```env
BOT_TOKEN=your_bot_token
GUILD_ID=your_server_id
LOG_CHANNEL_ID=your_staff_log_channel_id
```

Optional settings include:

```env
STAFF_ROLE_ID=0
DATABASE_PATH=moderation.db
BOOST_CHANNEL_ID=0
DEV_USER_ID=0
```

Color variables can also be customized.

> Never share your bot token or commit `.env` to a public repository.

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run Delicate

```bash
python bot.py
```

Delicate initializes its SQLite database automatically when it starts.

## 🧑‍⚖️ Staff Workflow

Warn a member:

```text
/warn @Steve Spamming
```

View their moderation history:

```text
/history @Steve
```

Look up a specific case:

```text
/case 42
```

Configure the moderation log:

```text
/setlog #staff-logs
```

Configure the staff role:

```text
/setstaff @Moderators
```

Create a ticket panel:

```text
/setticket #support
```

Configure suggestions:

```text
/setsuggest #suggestions
```

## 🔐 Security

* Never place your bot token in source code.
* Never commit `.env`.
* Never share your bot token.
* Keep moderation logs and ticket transcripts private.
* Only give staff roles to trusted members.
* Keep the SQLite database private when it contains sensitive moderation records.
* Developer-only commands are protected by the configured developer ID.
* Blacklisted guilds are prevented from using Delicate.

## 📁 Project Structure

```text
delicate-bot/
├── bot.py
├── database/
│   └── database.py
├── modules/
│   └── tickets.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CHANGELOG.md
├── PRIVACY.md
├── TERMS.md
└── LICENSE.txt
```

## 📜 License

Delicate is licensed under the MIT License.

See [`LICENSE.txt`](LICENSE.txt) for the full license text.

---

**Delicate — soft colors, hard moderation.** 🎀📦

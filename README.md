# 📦 Clouddyiе's Cardboard Box — Discord Moderation Bot v2

A Discord-only moderation bot with a soft cardboard/pastel visual style, staff logs, persistent moderation cases, warnings, automatic escalation, and member history.

## ✨ Features

* 🔨 Ban members temporarily or permanently
* 👢 Kick members
* 🔇 Timeout members
* ⚠️ Persistent warnings
* ⚡ Automatic warning escalation
* ↩️ Remove bans and timeouts
* 📋 Persistent moderation history
* 📦 Individual case lookup
* 📝 Staff-only moderation logs
* 🎨 Customizable pastel embed colors
* 💾 SQLite database storage

## Commands

### Moderation

* `/ban member duration reason`
* `/kick member reason`
* `/mute member duration reason`
* `/warn member reason`

### Reversals

* `/unban user_id reason`
* `/unmute member reason`

### Records

* `/history member limit`
* `/case case_id`

All moderation commands are restricted to staff members through Discord permissions or the configured staff role.

## ⚠️ Warning System

Warnings are stored separately from moderation cases and remain active until a warning-clear system is added.

Default automatic escalation:

| Active warnings | Action         |
| --------------: | -------------- |
|               3 | 1 hour timeout |
|               5 | 1 day timeout  |
|               7 | Permanent ban  |

The escalation thresholds are configurable near the top of `bot.py`:

```py
WARN_ESCALATION = [
    (3, "MUTE", "1h"),
    (5, "MUTE", "1d"),
    (7, "BAN", "perm"),
]
```

Only the highest threshold reached is applied. For example, a member reaching 5 active warnings receives the 5-warning escalation rather than both the 3-warning and 5-warning actions.

## 🎨 Design

Moderation logs use Discord embeds with a warm pastel palette inspired by **Clouddyiе's Cardboard Box** aesthetic.

Each moderation log contains:

* Action
* Member
* Reason
* Moderator
* Duration when relevant
* Case number
* Timestamp

The `/history` command combines recent warnings and moderation cases into a private staff-only embed.

## ⏱️ Duration Formats

Supported examples:

```text
30m
2h
7d
1d12h
perm
```

Supported units:

* `s` — seconds
* `m` — minutes
* `h` — hours
* `d` — days
* `w` — weeks

Discord native timeouts cannot exceed 28 days.

## 🛠️ Setup

### Requirements

* Python 3.10+
* A Discord application
* A Discord bot token
* A Discord server for testing

### 1. Create the bot

Create a bot through the Discord Developer Portal.

Invite it using the:

* `bot` scope
* `applications.commands` scope

Give the bot these permissions:

* Ban Members
* Kick Members
* Moderate Members
* View Channels
* Send Messages
* Embed Links

Make sure the bot's role is **above the members it needs to moderate**.

### 2. Configure environment variables

Copy `.env.example` to `.env`.

Fill in:

```env
BOT_TOKEN=your_bot_token
GUILD_ID=your_server_id
LOG_CHANNEL_ID=your_staff_log_channel_id
```

Optionally configure:

```env
STAFF_ROLE_ID=0
DATABASE_PATH=moderation.db
```

The remaining color variables can be left at their defaults.

> Never share your bot token or commit `.env` to a public repository.

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run Delicate

```bash
python bot.py
```

The bot automatically creates `moderation.db` when it starts.

## 🧑‍⚖️ Staff Workflow

Give a member a warning:

```text
/warn @Steve Spamming
```

The bot records the warning, calculates the active warning count, sends a staff log, and checks the escalation rules.

View recent history:

```text
/history @Steve
```

Look up a specific case:

```text
/case 42
```

## 🔐 Security

* Never put your bot token in source code.
* Never commit `.env`.
* Never share your bot token with anyone.
* The bot checks Discord permissions and role hierarchy before taking moderation actions.
* Keep the staff log channel visible only to trusted staff.
* Keep the SQLite database private if it contains sensitive moderation records.

## 🎨 Changing the Look

Embed colors can be customized through `.env` using decimal RGB integers.

The default values are configured for the pastel cardboard-box aesthetic.

## 📁 Project Files

```text
delicate-bot/
├── bot.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── PRIVACY.md
├── TERMS.md
└── LICENSE
```

## 📜 License

This project is licensed under the MIT License. See `LICENSE` for details.

---

**Delicate — soft colors, hard moderation.** 🎀📦

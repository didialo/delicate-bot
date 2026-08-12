# 📦 Clouddyiе's Cardboard Box — Discord Moderation Bot v2

A Discord moderation bot with a soft cardboard/pastel visual style, staff logs, persistent moderation cases, warnings, automatic escalation, member history, configurable server prefixes, and Cardboard Box boost announcements.

## ✨ Features

- 🔨 Ban members temporarily or permanently
- 👢 Kick members
- 🔇 Timeout members
- ⚠️ Persistent warnings
- ⚡ Automatic warning escalation
- ↩️ Remove bans and timeouts
- 📋 Persistent moderation history
- 📦 Individual case lookup
- 📝 Staff-only moderation logs
- 🎨 Customizable pastel embed colors
- 💾 SQLite database storage
- 🪽 Configurable server command prefixes
- 📦 Server boost announcements
- 🧪 Boost announcement testing with slash and prefix commands

## Commands

### Moderation — Slash Commands

- `/ban member duration reason`
- `/kick member reason`
- `/mute member duration reason`
- `/warn member reason`

### Reversals — Slash Commands

- `/unban user_id reason`
- `/unmute member reason`

### Records — Slash Commands

- `/history member limit`
- `/case case_id`

All moderation commands are restricted to staff members through Discord permissions or the configured staff role.

## 🪽 Prefix Commands

The default prefix is **`d!`**.

`d!` always remains available, even if a server changes its custom prefix, so the prefix can always be changed or reset.

### Prefix management

- `d!prefix` — show the current server prefix
- `d!prefix set c!` — change the server prefix
- `d!prefix reset` — restore the default `d!` prefix

Changing the prefix requires the **Manage Server** permission.

A custom prefix may be up to 5 characters long.

### Boost testing

The boost module provides the same test command through both command systems:

- `/testboost`
- `d!testboost` — or the server's configured prefix

The test command posts a Cardboard Box boost announcement in the configured boost channel.

## 📦 Server Boosts

Delicate automatically detects when a member starts boosting the server and sends a Cardboard Box-themed announcement to the configured boost channel.

Boost announcements include:

- The boosting member
- Current server boost count
- Current server boost level
- The member's avatar
- Cardboard Box-themed embed styling

Configure the announcement channel with:

```env
BOOST_CHANNEL_ID=your_boost_channel_id
```

If `BOOST_CHANNEL_ID` is `0` or not configured, boost announcements are disabled.

## ⚠️ Warning System

Warnings are stored separately from moderation cases and remain active until a warning-clear system is added.

Default automatic escalation:

| Active warnings | Action |
|---:|---|
| 3 | 1 hour timeout |
| 5 | 1 day timeout |
| 7 | Permanent ban |

The escalation thresholds are configurable near the top of `bot.py`:

```py
WARN_ESCALATION = [
    (3, "MUTE", "1h"),
    (5, "MUTE", "1d"),
    (7, "BAN", "perm"),
]
```

Only the highest threshold reached is applied.

For example, a member reaching 5 active warnings receives the 5-warning escalation rather than both the 3-warning and 5-warning actions.

## 🎨 Design

Moderation logs use Discord embeds with a warm pastel palette inspired by **Clouddyiе's Cardboard Box** aesthetic.

Each moderation log contains:

- Action
- Member
- Reason
- Moderator
- Duration when relevant
- Case number
- Timestamp

The `/history` command combines recent warnings and moderation cases into a private staff-only embed.

Boost announcements use the same Cardboard Box visual language, with a dedicated boost message for members who support the server.

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

- `s` — seconds
- `m` — minutes
- `h` — hours
- `d` — days
- `w` — weeks

Discord native timeouts cannot exceed 28 days.

## 🛠️ Setup

### Requirements

- Python 3.10+
- A Discord application
- A Discord bot token
- A Discord server for testing

### 1. Create the bot

Create a bot through the Discord Developer Portal.

Invite it using the:

- `bot` scope
- `applications.commands` scope

Give the bot these permissions:

- Ban Members
- Kick Members
- Moderate Members
- View Channels
- Send Messages
- Embed Links

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
BOOST_CHANNEL_ID=0
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

Manage the server prefix:

```text
d!prefix
```

Run a boost announcement test:

```text
d!testboost
```

## 🔐 Security

- Never put your bot token in source code.
- Never commit `.env`.
- Never share your bot token with anyone.
- The bot checks Discord permissions and role hierarchy before taking moderation actions.
- Keep the staff log channel visible only to trusted staff.
- Keep the SQLite database private if it contains sensitive moderation records.
- Only trusted staff should be given permission to change the server prefix.

## 🎨 Changing the Look

Embed colors can be customized through `.env` using decimal RGB integers.

The default values are configured for the pastel cardboard-box aesthetic.

## 📁 Project Files

```text
delicate-bot/
├── bot.py
├── modules/
│   ├── boosts.py
│   └── prefixes.py
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

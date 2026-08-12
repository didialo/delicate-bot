import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

# ============================================================
# CONFIG
# ============================================================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "moderation.db",
)

# ============================================================
# DATABASE CONNECTION
# ============================================================

db = sqlite3.connect(
    DATABASE_PATH,
    check_same_thread=False,
)

db.row_factory = sqlite3.Row

# ============================================================
# HELPERS
# ============================================================

def now_ts() -> int:
    return int(
        datetime.now(timezone.utc).timestamp()
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database() -> None:
    """
    Creates all Delicate database tables and indexes.
    Existing data is preserved.
    """

    # --------------------------------------------------------
    # MODERATION CASES
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            guild_id INTEGER NOT NULL,

            action TEXT NOT NULL,

            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,

            moderator_id INTEGER NOT NULL,
            moderator_name TEXT NOT NULL,

            reason TEXT NOT NULL,

            duration TEXT,
            expires_at INTEGER,

            created_at INTEGER NOT NULL,

            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            guild_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,

            moderator_id INTEGER NOT NULL,
            moderator_name TEXT NOT NULL,

            reason TEXT NOT NULL,

            created_at INTEGER NOT NULL,

            active INTEGER NOT NULL DEFAULT 1,

            escalation_case_id INTEGER
        )
        """
    )

    # --------------------------------------------------------
    # PER-SERVER SETTINGS
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,

            log_channel_id INTEGER,

            boost_channel_id INTEGER,

            staff_role_id INTEGER
        )
        """
    )

    # --------------------------------------------------------
    # INDEXES
    # --------------------------------------------------------

    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cases_guild_user
        ON cases (guild_id, user_id)
        """
    )

    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cases_expiration
        ON cases (active, expires_at)
        """
    )

    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_warnings_guild_user
        ON warnings (guild_id, user_id, active)
        """
    )

    db.commit()


# ============================================================
# GUILD SETTINGS
# ============================================================

VALID_SETTINGS = {
    "log_channel_id",
    "boost_channel_id",
    "staff_role_id",
}


def get_guild_setting(
    guild_id: int,
    setting: str,
) -> Optional[int]:

    if setting not in VALID_SETTINGS:
        raise ValueError(
            "Invalid guild setting."
        )

    row = db.execute(
        f"""
        SELECT {setting}
        FROM guild_settings
        WHERE guild_id = ?
        """,
        (guild_id,),
    ).fetchone()

    if row is None:
        return None

    value = row[setting]

    if value is None:
        return None

    return int(value)


def set_guild_setting(
    guild_id: int,
    setting: str,
    value: Optional[int],
) -> None:

    if setting not in VALID_SETTINGS:
        raise ValueError(
            "Invalid guild setting."
        )

    db.execute(
        """
        INSERT OR IGNORE INTO guild_settings (
            guild_id
        )
        VALUES (?)
        """,
        (guild_id,),
    )

    db.execute(
        f"""
        UPDATE guild_settings
        SET {setting} = ?
        WHERE guild_id = ?
        """,
        (
            value,
            guild_id,
        ),
    )

    db.commit()


def reset_guild_settings(
    guild_id: int,
) -> None:

    db.execute(
        """
        DELETE FROM guild_settings
        WHERE guild_id = ?
        """,
        (guild_id,),
    )

    db.commit()


# ============================================================
# MODERATION CASES
# ============================================================

def create_case(
    guild_id: int,
    action: str,
    user,
    moderator,
    reason: str,
    duration: Optional[str] = None,
    expires_at: Optional[int] = None,
) -> int:

    cur = db.execute(
        """
        INSERT INTO cases (
            guild_id,
            action,
            user_id,
            user_name,
            moderator_id,
            moderator_name,
            reason,
            duration,
            expires_at,
            created_at,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            guild_id,
            action,
            user.id,
            str(user),
            moderator.id,
            str(moderator),
            reason,
            duration,
            expires_at,
            now_ts(),
        ),
    )

    db.commit()

    return int(cur.lastrowid or 0)


def close_case(
    case_id: int,
) -> None:

    db.execute(
        """
        UPDATE cases
        SET active = 0
        WHERE id = ?
        """,
        (case_id,),
    )

    db.commit()


def get_case(
    guild_id: int,
    case_id: int,
):
    return db.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        AND guild_id = ?
        """,
        (
            case_id,
            guild_id,
        ),
    ).fetchone()


def get_expired_cases():
    """
    Returns active temporary moderation cases
    whose expiration time has passed.
    """

    return db.execute(
        """
        SELECT *
        FROM cases
        WHERE active = 1
        AND expires_at IS NOT NULL
        AND expires_at <= ?
        ORDER BY id ASC
        """,
        (now_ts(),),
    ).fetchall()


# ============================================================
# WARNINGS
# ============================================================

def add_warning(
    guild_id: int,
    user,
    moderator,
    reason: str,
) -> int:

    cur = db.execute(
        """
        INSERT INTO warnings (
            guild_id,
            user_id,
            user_name,
            moderator_id,
            moderator_name,
            reason,
            created_at,
            active,
            escalation_case_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, NULL)
        """,
        (
            guild_id,
            user.id,
            str(user),
            moderator.id,
            str(moderator),
            reason,
            now_ts(),
        ),
    )

    db.commit()

    return int(cur.lastrowid or 0)


def active_warning_count(
    guild_id: int,
    user_id: int,
) -> int:

    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM warnings
        WHERE guild_id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            guild_id,
            user_id,
        ),
    ).fetchone()

    if row is None:
        return 0

    return int(row["count"])


def get_warning(
    guild_id: int,
    warning_id: int,
):
    return db.execute(
        """
        SELECT *
        FROM warnings
        WHERE id = ?
        AND guild_id = ?
        """,
        (
            warning_id,
            guild_id,
        ),
    ).fetchone()


def close_warning(
    warning_id: int,
) -> None:

    db.execute(
        """
        UPDATE warnings
        SET active = 0
        WHERE id = ?
        """,
        (warning_id,),
    )

    db.commit()


def set_warning_escalation_case(
    warning_id: int,
    case_id: int,
) -> None:

    db.execute(
        """
        UPDATE warnings
        SET escalation_case_id = ?
        WHERE id = ?
        """,
        (
            case_id,
            warning_id,
        ),
    )

    db.commit()


# ============================================================
# USER HISTORY
# ============================================================

def get_user_history(
    guild_id: int,
    user_id: int,
    limit: int = 10,
):

    return db.execute(
        """
        SELECT *
        FROM (
            SELECT
                id,
                action,
                user_id,
                user_name,
                moderator_id,
                moderator_name,
                reason,
                duration,
                expires_at,
                created_at,
                active,
                'case' AS source
            FROM cases
            WHERE guild_id = ?
            AND user_id = ?

            UNION ALL

            SELECT
                id,
                'WARN' AS action,
                user_id,
                user_name,
                moderator_id,
                moderator_name,
                reason,
                NULL AS duration,
                NULL AS expires_at,
                created_at,
                active,
                'warning' AS source
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
        )
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (
            guild_id,
            user_id,
            guild_id,
            user_id,
            limit,
        ),
    ).fetchall()


# ============================================================
# DATABASE HEALTH
# ============================================================

def database_ready() -> bool:

    try:
        db.execute(
            "SELECT 1"
        ).fetchone()

        return True

    except sqlite3.Error:
        return False


# ============================================================
# STARTUP
# ============================================================

init_database()
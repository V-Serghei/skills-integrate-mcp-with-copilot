"""Persistence layer for the school activities application."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "school.db"


DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Initialize schema and seed baseline data on first run."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                role TEXT NOT NULL CHECK (role IN ('student', 'admin'))
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL CHECK (max_participants > 0)
            );

            CREATE TABLE IF NOT EXISTS activity_participants (
                activity_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (activity_id, user_email),
                FOREIGN KEY (activity_id) REFERENCES activities (id) ON DELETE CASCADE,
                FOREIGN KEY (user_email) REFERENCES users (email) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS membership_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'declined')) DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (activity_id) REFERENCES activities (id) ON DELETE CASCADE,
                FOREIGN KEY (user_email) REFERENCES users (email) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS event_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                user_email TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'declined')) DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users (email) ON DELETE CASCADE
            );
            """
        )

        existing_activities = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
        if existing_activities > 0:
            return

        all_emails = {
            email
            for activity in DEFAULT_ACTIVITIES.values()
            for email in activity["participants"]
        }
        all_emails.add("admin@mergington.edu")

        conn.executemany(
            "INSERT INTO users(email, role) VALUES(?, ?)",
            [
                (email, "admin" if email == "admin@mergington.edu" else "student")
                for email in sorted(all_emails)
            ],
        )

        for name, data in DEFAULT_ACTIVITIES.items():
            cursor = conn.execute(
                """
                INSERT INTO activities(name, description, schedule, max_participants)
                VALUES(?, ?, ?, ?)
                """,
                (name, data["description"], data["schedule"], data["max_participants"]),
            )
            activity_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO activity_participants(activity_id, user_email) VALUES(?, ?)",
                [(activity_id, email) for email in data["participants"]],
            )


def get_activities() -> dict[str, dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                a.name,
                a.description,
                a.schedule,
                a.max_participants,
                ap.user_email
            FROM activities a
            LEFT JOIN activity_participants ap ON ap.activity_id = a.id
            ORDER BY a.name, ap.created_at
            """
        ).fetchall()

    activities: dict[str, dict] = {}
    for row in rows:
        name = row["name"]
        if name not in activities:
            activities[name] = {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": [],
            }
        if row["user_email"]:
            activities[name]["participants"].append(row["user_email"])

    return activities


def signup_for_activity(activity_name: str, email: str) -> None:
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        activity = conn.execute(
            "SELECT id, max_participants FROM activities WHERE name = ?", (activity_name,)
        ).fetchone()
        if not activity:
            raise KeyError("activity_not_found")

        conn.execute(
            "INSERT OR IGNORE INTO users(email, role) VALUES(?, 'student')", (email,)
        )

        current_count = conn.execute(
            "SELECT COUNT(*) FROM activity_participants WHERE activity_id = ?",
            (activity["id"],),
        ).fetchone()[0]
        if current_count >= activity["max_participants"]:
            raise ValueError("activity_full")

        try:
            conn.execute(
                "INSERT INTO activity_participants(activity_id, user_email) VALUES(?, ?)",
                (activity["id"], email),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("already_signed_up") from exc


def unregister_from_activity(activity_name: str, email: str) -> None:
    with _connect() as conn:
        activity = conn.execute(
            "SELECT id FROM activities WHERE name = ?", (activity_name,)
        ).fetchone()
        if not activity:
            raise KeyError("activity_not_found")

        deleted = conn.execute(
            "DELETE FROM activity_participants WHERE activity_id = ? AND user_email = ?",
            (activity["id"], email),
        ).rowcount
        if deleted == 0:
            raise ValueError("not_signed_up")

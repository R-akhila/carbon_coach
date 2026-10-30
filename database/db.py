
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Database file location
DB_PATH = Path(__file__).resolve().parent / "carbon_coach.db"


# 1. Connect to the database
def get_connection():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# 2. Create the activities table
def init_db():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT NOT NULL,

            activity TEXT NOT NULL,

            subtype TEXT NOT NULL,

            quantity REAL NOT NULL,

            emission_factor REAL NOT NULL,

            emissions_kg REAL NOT NULL,

            unit TEXT,

            factor_status TEXT,

            source TEXT,

            created_at TEXT NOT NULL

        )
    """)

    connection.commit()

    connection.close()


# 3. Save an activity
def save_activity(result, user_id="demo-user"):

    connection = get_connection()

    cursor = connection.cursor()

    created_at = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    cursor.execute("""
        INSERT INTO activities (
            user_id,
            activity,
            subtype,
            quantity,
            emission_factor,
            emissions_kg,
            unit,
            factor_status,
            source,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        result["activity"],
        result["type"],
        result["quantity"],
        result["emission_factor"],
        result["emissions_kg"],
        result["unit"],
        result["status"],
        result["source"],
        created_at
    ))

    connection.commit()

    activity_id = cursor.lastrowid

    connection.close()

    return activity_id


# 4. Retrieve all saved activities
def get_activities(user_id="demo-user"):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM activities
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()

    activities = [dict(row) for row in rows]

    connection.close()

    return activities


# 5. Calculate carbon summary
def get_summary(period="all", user_id="demo-user"):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.now(timezone.utc)

    if period == "today":

        start_time = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        cutoff = start_time.isoformat()

    elif period == "week":

        cutoff = (
            now - timedelta(days=7)
        ).isoformat()

    elif period == "month":

        cutoff = (
            now - timedelta(days=30)
        ).isoformat()

    elif period == "all":

        cutoff = None

    else:

        connection.close()

        raise ValueError(
            "Period must be today, week, month or all"
        )

    if cutoff:

        cursor.execute("""
            SELECT
                COUNT(*) AS total_activities,
                COALESCE(SUM(emissions_kg), 0) AS total_emissions
            FROM activities
            WHERE user_id = ?
            AND created_at >= ?
        """, (user_id, cutoff))

    else:

        cursor.execute("""
            SELECT
                COUNT(*) AS total_activities,
                COALESCE(SUM(emissions_kg), 0) AS total_emissions
            FROM activities
            WHERE user_id = ?
        """, (user_id,))

    summary = dict(cursor.fetchone())

    # Emissions grouped by activity category
    if cutoff:

        cursor.execute("""
            SELECT
                activity,
                SUM(emissions_kg) AS emissions
            FROM activities
            WHERE user_id = ?
            AND created_at >= ?
            GROUP BY activity
        """, (user_id, cutoff))

    else:

        cursor.execute("""
            SELECT
                activity,
                SUM(emissions_kg) AS emissions
            FROM activities
            WHERE user_id = ?
            GROUP BY activity
        """, (user_id,))

    summary["by_activity"] = {
        row["activity"]: round(row["emissions"], 3)
        for row in cursor.fetchall()
    }

    summary["total_emissions"] = round(
        summary["total_emissions"], 3
    )

    connection.close()

    return summary

from datetime import datetime

from database.db import get_db
from database._transactions import _get_recent_transactions
from database._stats import _get_summary_stats
from database._categories import _get_category_breakdown


def get_user_by_id(user_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": datetime.strptime(
            row["created_at"], "%Y-%m-%d %H:%M:%S"
        ).strftime("%B %Y"),
    }


def get_summary_stats(user_id: int):
    return _get_summary_stats(user_id)


def get_recent_transactions(user_id: int, limit: int = 10):
    return _get_recent_transactions(user_id, limit)


def get_category_breakdown(user_id: int):
    return _get_category_breakdown(user_id)

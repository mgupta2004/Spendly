from database.db import get_db


def _get_recent_transactions(user_id: int, limit: int = 10):
    conn = get_db()
    rows = conn.execute(
        "SELECT date, description, category, amount "
        "FROM expenses WHERE user_id = ? "
        "ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [
        {
            "date": r["date"],
            "description": r["description"],
            "category": r["category"],
            "amount": float(r["amount"]),
        }
        for r in rows
    ]

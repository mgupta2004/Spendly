from typing import Optional

from database.db import get_db
from database._filters import build_date_filter


def _get_recent_transactions(user_id: int, limit: Optional[int] = 10,
                              from_date: Optional[str] = None,
                              to_date: Optional[str] = None):
    where, params = build_date_filter(user_id, from_date, to_date)

    sql = (
        "SELECT date, description, category, amount "
        "FROM expenses WHERE " + where +
        " ORDER BY date DESC, id DESC"
    )
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
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

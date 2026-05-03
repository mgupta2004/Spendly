from typing import Optional

from database.db import get_db
from database._filters import build_date_filter


def _get_category_breakdown(user_id: int,
                              from_date: Optional[str] = None,
                              to_date: Optional[str] = None):
    where, params = build_date_filter(user_id, from_date, to_date)

    conn = get_db()
    rows = conn.execute(
        "SELECT category AS name, SUM(amount) AS amount "
        "FROM expenses WHERE " + where +
        " GROUP BY category ORDER BY SUM(amount) DESC",
        params
    ).fetchall()
    conn.close()
    if not rows:
        return []
    amounts = [float(r["amount"]) for r in rows]
    total = sum(amounts)
    floors = [int(a / total * 100) for a in amounts]
    floors[floors.index(max(floors))] += 100 - sum(floors)
    return [
        {"name": rows[i]["name"], "amount": amounts[i], "pct": floors[i]}
        for i in range(len(rows))
    ]

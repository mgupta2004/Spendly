from typing import Optional

from database.db import get_db
from database._filters import build_date_filter


def _get_summary_stats(user_id: int,
                        from_date: Optional[str] = None,
                        to_date: Optional[str] = None):
    where, params = build_date_filter(user_id, from_date, to_date)

    conn = get_db()
    agg = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total_spent, "
        "COUNT(*) AS transaction_count "
        "FROM expenses WHERE " + where,
        params
    ).fetchone()
    top = conn.execute(
        "SELECT category FROM expenses WHERE " + where +
        " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        params
    ).fetchone()
    conn.close()
    return {
        "total_spent": float(agg["total_spent"]),
        "transaction_count": int(agg["transaction_count"]),
        "top_category": top["category"] if top else None,
    }

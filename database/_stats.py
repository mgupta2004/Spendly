from database.db import get_db


def _get_summary_stats(user_id: int):
    conn = get_db()
    agg = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total_spent, "
        "COUNT(*) AS transaction_count "
        "FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    top = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return {
        "total_spent": float(agg["total_spent"]),
        "transaction_count": int(agg["transaction_count"]),
        "top_category": top["category"] if top else None,
    }

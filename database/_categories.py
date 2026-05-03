from database.db import get_db


def _get_category_breakdown(user_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT category AS name, SUM(amount) AS amount "
        "FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC",
        (user_id,)
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

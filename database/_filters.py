from typing import List, Optional, Tuple


def build_date_filter(
    user_id: int,
    from_date: Optional[str],
    to_date: Optional[str],
) -> Tuple[str, List]:
    where = "user_id = ?"
    params: List = [user_id]
    if from_date:
        where += " AND date >= ?"
        params.append(from_date)
    if to_date:
        where += " AND date <= ?"
        params.append(to_date)
    return where, params

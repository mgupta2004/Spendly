from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


class TestGetUserById:
    def test_returns_dict_with_required_keys(self, seeded_user_id):
        result = get_user_by_id(seeded_user_id)
        assert result is not None
        assert set(result.keys()) == {"name", "email", "member_since"}

    def test_correct_name_and_email(self, seeded_user_id):
        result = get_user_by_id(seeded_user_id)
        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"

    def test_member_since_format_is_month_year(self, seeded_user_id):
        result = get_user_by_id(seeded_user_id)
        # Should be "Month YYYY", e.g. "May 2026" — not "May 01, 2026"
        parts = result["member_since"].split()
        assert len(parts) == 2
        assert parts[1].isdigit() and len(parts[1]) == 4

    def test_returns_none_for_unknown_id(self, app):
        assert get_user_by_id(99999) is None


class TestGetSummaryStats:
    def test_returns_correct_total_spent(self, seeded_user_id):
        result = get_summary_stats(seeded_user_id)
        assert result["total_spent"] == 200.0

    def test_returns_correct_transaction_count(self, seeded_user_id):
        result = get_summary_stats(seeded_user_id)
        assert result["transaction_count"] == 3

    def test_top_category_is_highest_spend(self, seeded_user_id):
        result = get_summary_stats(seeded_user_id)
        assert result["top_category"] == "Food"

    def test_zero_expense_user_returns_zeros(self, zero_user_id):
        result = get_summary_stats(zero_user_id)
        assert result["total_spent"] == 0.0
        assert result["transaction_count"] == 0

    def test_zero_expense_user_top_category_is_none(self, zero_user_id):
        result = get_summary_stats(zero_user_id)
        assert result["top_category"] is None


class TestGetRecentTransactions:
    def test_returns_list_of_dicts(self, seeded_user_id):
        result = get_recent_transactions(seeded_user_id)
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_dict_keys_are_correct(self, seeded_user_id):
        result = get_recent_transactions(seeded_user_id)
        assert set(result[0].keys()) == {"date", "description", "category", "amount"}

    def test_ordered_by_date_descending(self, seeded_user_id):
        result = get_recent_transactions(seeded_user_id)
        dates = [r["date"] for r in result]
        assert dates == sorted(dates, reverse=True)

    def test_default_limit_returns_at_most_10(self, seeded_user_id):
        result = get_recent_transactions(seeded_user_id)
        assert len(result) <= 10

    def test_custom_limit_respected(self, seeded_user_id):
        result = get_recent_transactions(seeded_user_id, limit=1)
        assert len(result) == 1

    def test_zero_expense_user_returns_empty_list(self, zero_user_id):
        assert get_recent_transactions(zero_user_id) == []


class TestGetCategoryBreakdown:
    def test_returns_list_of_dicts(self, seeded_user_id):
        result = get_category_breakdown(seeded_user_id)
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_dict_keys_are_correct(self, seeded_user_id):
        result = get_category_breakdown(seeded_user_id)
        assert set(result[0].keys()) == {"name", "amount", "pct"}

    def test_pct_values_sum_to_100(self, seeded_user_id):
        result = get_category_breakdown(seeded_user_id)
        assert sum(r["pct"] for r in result) == 100

    def test_pct_values_are_integers(self, seeded_user_id):
        result = get_category_breakdown(seeded_user_id)
        assert all(isinstance(r["pct"], int) for r in result)

    def test_ordered_by_amount_descending(self, seeded_user_id):
        result = get_category_breakdown(seeded_user_id)
        amounts = [r["amount"] for r in result]
        assert amounts == sorted(amounts, reverse=True)

    def test_single_category_pct_is_100(self, app):
        from database.db import create_user, get_db
        uid = create_user("Single", "single@example.com", "pw")
        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?,?,?,?)",
            (uid, 99.0, "Food", "2026-01-01")
        )
        conn.commit()
        conn.close()
        result = get_category_breakdown(uid)
        assert len(result) == 1
        assert result[0]["pct"] == 100

    def test_zero_expense_user_returns_empty_list(self, zero_user_id):
        assert get_category_breakdown(zero_user_id) == []


class TestProfileRoute:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_authenticated_returns_200(self, client, seeded_user_id):
        with client.session_transaction() as sess:
            sess["user_id"] = seeded_user_id
            sess["user_name"] = "Test User"
        response = client.get("/profile")
        assert response.status_code == 200

    def test_profile_shows_user_name(self, client, seeded_user_id):
        with client.session_transaction() as sess:
            sess["user_id"] = seeded_user_id
            sess["user_name"] = "Test User"
        response = client.get("/profile")
        assert b"Test User" in response.data

    def test_profile_shows_rupee_symbol(self, client, seeded_user_id):
        with client.session_transaction() as sess:
            sess["user_id"] = seeded_user_id
            sess["user_name"] = "Test User"
        response = client.get("/profile")
        assert "₹".encode() in response.data

    def test_zero_expense_user_shows_empty_state(self, client, zero_user_id):
        with client.session_transaction() as sess:
            sess["user_id"] = zero_user_id
            sess["user_name"] = "Empty User"
        response = client.get("/profile")
        assert b"No transactions yet." in response.data

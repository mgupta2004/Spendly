"""
Tests for Step 6: Date Filter on the Profile Page.

Covers:
  - Auth guard on GET /profile
  - No-filter baseline (all-time view with seed data)
  - Period presets: this_month, last_month, last_3_months
  - Custom date range: full April, single day, empty range
  - Malformed date parameters (silently ignored)
  - Form pre-fill of from_date / to_date inputs
  - Filter bar HTML: preset links, active-pill class
  - "Showing results for" label presence/absence
  - Unit tests: get_summary_stats with from_date / to_date
  - Unit tests: get_recent_transactions with from_date / to_date
  - Unit tests: get_category_breakdown with from_date / to_date

Seed data (demo@spendly.com / demo123) — 8 expenses all in April 2026:
  2026-04-01  Food           52.30  Weekly groceries
  2026-04-03  Transport      12.00  Bus pass top-up
  2026-04-05  Entertainment  15.99  Netflix subscription
  2026-04-07  Shopping       89.00  New shoes
  2026-04-10  Food           34.50  Restaurant dinner
  2026-04-12  Bills          45.00  Electricity bill
  2026-04-14  Health         20.00  Pharmacy
  2026-04-16  Other           5.00  Miscellaneous
  Total: 273.79
"""

import pytest
import database.db as db_module
from app import app as flask_app
from database.db import init_db, seed_db, get_db
from database.queries import (
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"

APRIL_FROM = "2026-04-01"
APRIL_TO = "2026-04-30"
APRIL_TOTAL = 273.79
APRIL_COUNT = 8
# Shopping (89.00) is the highest-spend single category in April
APRIL_TOP_CATEGORY = "Shopping"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """Isolated Flask app using a fresh temp DB seeded with demo data."""
    db_file = tmp_path / "test_06.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))
    with flask_app.app_context():
        init_db()
        seed_db()
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-06"
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    """Test client already logged in as the seeded demo user."""
    resp = client.post(
        "/login",
        data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code == 302, (
        "Login should redirect after success; check demo credentials match seed_db"
    )
    return client


@pytest.fixture()
def demo_user_id(app):
    """Return the integer user_id for demo@spendly.com (seeded by seed_db)."""
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)
    ).fetchone()
    conn.close()
    assert row is not None, "seed_db must have created demo@spendly.com"
    return row["id"]


# ---------------------------------------------------------------------------
# 1. Auth guard
# ---------------------------------------------------------------------------


class TestAuthGuard:
    def test_unauthenticated_get_profile_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302, "Unauthenticated /profile must redirect"
        assert "/login" in response.headers["Location"], (
            "Redirect target must be /login"
        )

    def test_unauthenticated_profile_with_date_params_still_redirects(self, client):
        response = client.get(f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}")
        assert response.status_code == 302, (
            "Auth guard must fire even when query params are present"
        )
        assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# 2. No-filter baseline (All Time)
# ---------------------------------------------------------------------------


class TestNoFilterBaseline:
    def test_profile_loads_200_with_no_params(self, auth_client):
        response = auth_client.get("/profile")
        assert response.status_code == 200, "Authenticated /profile must return 200"

    def test_all_seed_expenses_counted_unfiltered(self, auth_client):
        response = auth_client.get("/profile")
        # All 8 seed expenses, total 273.79
        assert b"273.79" in response.data, (
            "Unfiltered profile must show total of all 8 seed expenses (273.79)"
        )

    def test_all_time_transaction_count_shown(self, auth_client):
        response = auth_client.get("/profile")
        assert b"8" in response.data, (
            "Unfiltered profile must show transaction count of 8"
        )

    def test_showing_results_label_absent_when_no_filter(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Showing results for" not in response.data, (
            "'Showing results for' label must NOT appear when no filter is active"
        )

    def test_no_filter_limits_recent_transactions_to_10(self, auth_client):
        """Without a date filter, the template must not receive more than 10 rows."""
        response = auth_client.get("/profile")
        # Seed has only 8 rows — we confirm all 8 are shown (≤10) and no crash
        assert response.status_code == 200
        # Each seed row has a unique description we can count
        page = response.data.decode()
        assert page.count("2026-04") <= 10, (
            "Unfiltered view must respect limit=10 (seed has 8, all should appear)"
        )


# ---------------------------------------------------------------------------
# 3. Period preset parameters
# ---------------------------------------------------------------------------


class TestPeriodPresets:
    @pytest.mark.parametrize("period", ["this_month", "last_month", "last_3_months"])
    def test_period_preset_returns_200(self, auth_client, period):
        response = auth_client.get(f"/profile?period={period}")
        assert response.status_code == 200, (
            f"?period={period} must return 200, not {response.status_code}"
        )

    @pytest.mark.parametrize("period", ["this_month", "last_month", "last_3_months"])
    def test_period_preset_does_not_show_results_label(self, auth_client, period):
        """Period presets resolve to from/to internally but the template uses
        active_period, not bare from_date/to_date, so 'Showing results for'
        should NOT appear (that label is only for explicit custom date input)."""
        response = auth_client.get(f"/profile?period={period}")
        assert b"Showing results for" not in response.data, (
            "Period presets must not trigger the custom-range 'Showing results for' label"
        )

    def test_unknown_period_value_returns_200_no_filter(self, auth_client):
        """An unrecognised period value must be ignored, falling back to All Time."""
        response = auth_client.get("/profile?period=invalid_period")
        assert response.status_code == 200
        # Falls back to all-time total
        assert b"273.79" in response.data, (
            "Unknown period must fall back to unfiltered all-time view"
        )


# ---------------------------------------------------------------------------
# 4. Custom date range — full April 2026
# ---------------------------------------------------------------------------


class TestCustomDateRangeApril:
    def test_full_april_range_returns_200(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}"
        )
        assert response.status_code == 200

    def test_full_april_range_shows_correct_total(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}"
        )
        assert b"273.79" in response.data, (
            "Full April range must show total 273.79"
        )

    def test_full_april_range_shows_correct_count(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}"
        )
        assert b"8" in response.data, "Full April range must show 8 transactions"

    def test_full_april_range_shows_results_label(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}"
        )
        assert b"Showing results for" in response.data, (
            "'Showing results for' label must appear when from_date and to_date are set"
        )

    def test_full_april_range_removes_limit_on_transactions(self, auth_client):
        """When a date filter is active, limit=None — all matching rows are shown."""
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}"
        )
        page = response.data.decode()
        # All 8 unique descriptions must appear in the transactions table
        seed_descriptions = [
            "Weekly groceries",
            "Bus pass top-up",
            "Netflix subscription",
            "New shoes",
            "Restaurant dinner",
            "Electricity bill",
            "Pharmacy",
            "Miscellaneous",
        ]
        for desc in seed_descriptions:
            assert desc in page, (
                f"Description '{desc}' must appear in filtered transaction table"
            )


# ---------------------------------------------------------------------------
# 5. Narrow custom range — single day (2026-04-01)
# ---------------------------------------------------------------------------


class TestSingleDayRange:
    def test_single_day_returns_200(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_FROM}"
        )
        assert response.status_code == 200

    def test_single_day_shows_correct_amount(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_FROM}"
        )
        assert b"52.30" in response.data, (
            "Apr-01-only filter must show the single expense of 52.30"
        )

    def test_single_day_count_is_one(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_FROM}"
        )
        assert b"1" in response.data, "Single-day filter must show transaction count of 1"

    def test_single_day_shows_only_food_category(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_FROM}"
        )
        assert b"Food" in response.data, "Apr-01 has a Food expense"

    def test_single_day_does_not_show_other_descriptions(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_FROM}"
        )
        page = response.data.decode()
        # These descriptions are from later dates and must NOT appear
        for desc in ["Bus pass top-up", "Netflix subscription", "New shoes"]:
            assert desc not in page, (
                f"'{desc}' must NOT appear when filtered to 2026-04-01 only"
            )


# ---------------------------------------------------------------------------
# 6. Empty date range (no matching expenses)
# ---------------------------------------------------------------------------


class TestEmptyDateRange:
    def test_empty_range_returns_200(self, auth_client):
        response = auth_client.get(
            "/profile?from_date=2000-01-01&to_date=2000-01-31"
        )
        assert response.status_code == 200, (
            "Empty date range must return 200, not a 500 error"
        )

    def test_empty_range_shows_no_transactions_message(self, auth_client):
        response = auth_client.get(
            "/profile?from_date=2000-01-01&to_date=2000-01-31"
        )
        assert b"No transactions" in response.data, (
            "Empty range must display 'No transactions' message"
        )

    def test_empty_range_shows_zero_total(self, auth_client):
        response = auth_client.get(
            "/profile?from_date=2000-01-01&to_date=2000-01-31"
        )
        assert b"0.00" in response.data, "Empty range must show total of 0.00"

    def test_empty_range_shows_results_label(self, auth_client):
        response = auth_client.get(
            "/profile?from_date=2000-01-01&to_date=2000-01-31"
        )
        assert b"Showing results for" in response.data, (
            "'Showing results for' must appear even when the range yields no data"
        )


# ---------------------------------------------------------------------------
# 7. Malformed date inputs (silently ignored)
# ---------------------------------------------------------------------------


class TestMalformedDateInputs:
    def test_malformed_from_date_returns_200(self, auth_client):
        response = auth_client.get("/profile?from_date=not-a-date")
        assert response.status_code == 200, (
            "Malformed from_date must be silently ignored and page must load"
        )

    def test_malformed_from_date_falls_back_to_all_time(self, auth_client):
        response = auth_client.get("/profile?from_date=not-a-date")
        assert b"273.79" in response.data, (
            "Malformed from_date must be ignored, showing all-time total 273.79"
        )

    def test_malformed_to_date_returns_200(self, auth_client):
        response = auth_client.get("/profile?to_date=bad")
        assert response.status_code == 200, (
            "Malformed to_date must be silently ignored and page must load"
        )

    def test_malformed_to_date_falls_back_to_all_time(self, auth_client):
        response = auth_client.get("/profile?to_date=bad")
        assert b"273.79" in response.data, (
            "Malformed to_date must be ignored, showing all-time total 273.79"
        )

    def test_both_malformed_dates_returns_200(self, auth_client):
        response = auth_client.get("/profile?from_date=abc&to_date=xyz")
        assert response.status_code == 200

    def test_both_malformed_dates_do_not_show_results_label(self, auth_client):
        response = auth_client.get("/profile?from_date=abc&to_date=xyz")
        assert b"Showing results for" not in response.data, (
            "Malformed dates are treated as None — no active filter label"
        )

    @pytest.mark.parametrize("bad_value", ["2026-13-01", "2026-04-32", "04-01-2026", "2026/04/01", ""])
    def test_various_invalid_from_date_formats_return_200(self, auth_client, bad_value):
        response = auth_client.get(f"/profile?from_date={bad_value}")
        assert response.status_code == 200, (
            f"from_date='{bad_value}' must not crash the page"
        )


# ---------------------------------------------------------------------------
# 8. Form pre-fill
# ---------------------------------------------------------------------------


class TestFormPrefill:
    def test_from_date_input_prefilled_in_html(self, auth_client):
        response = auth_client.get(f"/profile?from_date={APRIL_FROM}")
        assert f'value="{APRIL_FROM}"'.encode() in response.data, (
            f"from_date input must be pre-filled with {APRIL_FROM}"
        )

    def test_to_date_input_prefilled_in_html(self, auth_client):
        response = auth_client.get(f"/profile?to_date={APRIL_TO}")
        assert f'value="{APRIL_TO}"'.encode() in response.data, (
            f"to_date input must be pre-filled with {APRIL_TO}"
        )

    def test_both_date_inputs_prefilled(self, auth_client):
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}"
        )
        assert f'value="{APRIL_FROM}"'.encode() in response.data
        assert f'value="{APRIL_TO}"'.encode() in response.data

    def test_inputs_empty_when_no_dates_given(self, auth_client):
        response = auth_client.get("/profile")
        page = response.data.decode()
        # Both date inputs must render with empty value attributes
        assert 'value=""' in page, (
            "Date inputs must render with empty value when no filter is active"
        )

    def test_malformed_date_not_prefilled(self, auth_client):
        """A malformed date is treated as None — the input must NOT be pre-filled."""
        response = auth_client.get("/profile?from_date=not-a-date")
        assert b'value="not-a-date"' not in response.data, (
            "Malformed from_date must not be reflected back into the form input"
        )


# ---------------------------------------------------------------------------
# 9. Filter bar HTML landmarks
# ---------------------------------------------------------------------------


class TestFilterBarHTML:
    def test_all_time_link_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b"All Time" in response.data, "Filter bar must contain 'All Time' link"

    def test_this_month_link_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b"This Month" in response.data, "Filter bar must contain 'This Month'"

    def test_last_month_link_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Last Month" in response.data, "Filter bar must contain 'Last Month'"

    def test_last_3_months_link_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Last 3 Months" in response.data, (
            "Filter bar must contain 'Last 3 Months'"
        )

    def test_filter_date_form_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b'name="from_date"' in response.data, (
            "Filter form must include from_date date input"
        )
        assert b'name="to_date"' in response.data, (
            "Filter form must include to_date date input"
        )

    def test_filter_submit_button_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Filter" in response.data, "Filter bar must include a Filter submit button"


# ---------------------------------------------------------------------------
# 10. Active-pill CSS class
# ---------------------------------------------------------------------------


class TestActivePillClass:
    def test_all_time_pill_active_when_no_filter(self, auth_client):
        response = auth_client.get("/profile")
        page = response.data.decode()
        # The active pill class must appear; its position relative to "All Time"
        # confirms the correct link is highlighted.
        assert "filter-pill--active" in page, (
            "filter-pill--active class must be present when no filter is active"
        )
        # Ensure the active class appears before the next preset link text
        active_pos = page.index("filter-pill--active")
        all_time_pos = page.index("All Time")
        this_month_pos = page.index("This Month")
        assert active_pos < this_month_pos, (
            "filter-pill--active must appear before 'This Month'"
        )
        assert all_time_pos < this_month_pos, (
            "'All Time' link must appear before 'This Month'"
        )

    def test_this_month_pill_active_when_period_this_month(self, auth_client):
        response = auth_client.get("/profile?period=this_month")
        page = response.data.decode()
        assert "filter-pill--active" in page, (
            "filter-pill--active must be present for period=this_month"
        )
        active_pos = page.index("filter-pill--active")
        this_month_pos = page.index("This Month")
        last_month_pos = page.index("Last Month")
        assert active_pos < last_month_pos, (
            "Active pill must appear before 'Last Month' when this_month is active"
        )
        # "This Month" text follows its active pill
        assert this_month_pos > active_pos

    def test_last_month_pill_active_when_period_last_month(self, auth_client):
        response = auth_client.get("/profile?period=last_month")
        page = response.data.decode()
        assert "filter-pill--active" in page
        # "Last Month" must appear after the first active-pill occurrence
        active_idx = page.index("filter-pill--active")
        last_month_idx = page.index("Last Month")
        assert last_month_idx > active_idx

    def test_no_active_pill_for_custom_date_range(self, auth_client):
        """Custom date ranges have no preset active — filter-pill--active should
        only appear on the All Time pill (which defaults active when active_period
        is None and from_date/to_date are set by the user, NOT a period)."""
        response = auth_client.get(
            f"/profile?from_date={APRIL_FROM}&to_date={APRIL_TO}"
        )
        page = response.data.decode()
        # When explicit from_date/to_date are set, active_period is None
        # and from_date/to_date are truthy — so NO pill should be active
        # (template condition: not active_period and not from_date and not to_date)
        assert "filter-pill--active" not in page, (
            "No preset pill should be active when a custom date range is in use"
        )


# ---------------------------------------------------------------------------
# 11. Unit tests — get_summary_stats with date filters
# ---------------------------------------------------------------------------


class TestGetSummaryStatsFiltered:
    def test_full_april_range_total(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert abs(result["total_spent"] - APRIL_TOTAL) < 0.01, (
            f"Expected total_spent ~{APRIL_TOTAL}, got {result['total_spent']}"
        )

    def test_full_april_range_count(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert result["transaction_count"] == APRIL_COUNT, (
            f"Expected {APRIL_COUNT} transactions in April, got {result['transaction_count']}"
        )

    def test_full_april_range_top_category(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert result["top_category"] == APRIL_TOP_CATEGORY, (
            f"Expected top category '{APRIL_TOP_CATEGORY}', got '{result['top_category']}'"
        )

    def test_single_day_apr01_total(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_FROM
            )
        assert abs(result["total_spent"] - 52.30) < 0.01, (
            f"Expected 52.30 for Apr-01 only, got {result['total_spent']}"
        )
        assert result["transaction_count"] == 1
        assert result["top_category"] == "Food"

    def test_empty_range_returns_zeros(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date="2000-01-01", to_date="2000-01-31"
            )
        assert result["total_spent"] == 0.0, "Empty range must return total_spent=0.0"
        assert result["transaction_count"] == 0, (
            "Empty range must return transaction_count=0"
        )
        assert result["top_category"] is None, (
            "Empty range must return top_category=None"
        )

    def test_only_from_date_set(self, app, demo_user_id):
        """from_date alone must filter as a lower bound with no upper bound."""
        with app.app_context():
            result = get_summary_stats(demo_user_id, from_date="2026-04-10")
        # Expenses from Apr-10 onwards: 34.50 + 45.00 + 20.00 + 5.00 = 104.50
        assert abs(result["total_spent"] - 104.50) < 0.01, (
            f"from_date=2026-04-10 only should total 104.50, got {result['total_spent']}"
        )

    def test_only_to_date_set(self, app, demo_user_id):
        """to_date alone must filter as an upper bound with no lower bound."""
        with app.app_context():
            result = get_summary_stats(demo_user_id, to_date="2026-04-03")
        # Expenses up to Apr-03: 52.30 + 12.00 = 64.30
        assert abs(result["total_spent"] - 64.30) < 0.01, (
            f"to_date=2026-04-03 only should total 64.30, got {result['total_spent']}"
        )

    def test_returns_dict_with_all_required_keys(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert set(result.keys()) == {"total_spent", "transaction_count", "top_category"}

    def test_total_spent_is_float(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert isinstance(result["total_spent"], float)

    def test_transaction_count_is_int(self, app, demo_user_id):
        with app.app_context():
            result = get_summary_stats(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert isinstance(result["transaction_count"], int)


# ---------------------------------------------------------------------------
# 12. Unit tests — get_recent_transactions with date filters
# ---------------------------------------------------------------------------


class TestGetRecentTransactionsFiltered:
    def test_full_april_returns_8_rows(self, app, demo_user_id):
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert len(result) == 8, (
            f"Full April range must return 8 transactions, got {len(result)}"
        )

    def test_all_rows_within_april(self, app, demo_user_id):
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        for row in result:
            assert APRIL_FROM <= row["date"] <= APRIL_TO, (
                f"Row date {row['date']} is outside the April 2026 range"
            )

    def test_single_day_apr01_returns_1_row(self, app, demo_user_id):
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date=APRIL_FROM, to_date=APRIL_FROM
            )
        assert len(result) == 1, (
            f"Single-day Apr-01 filter must return 1 transaction, got {len(result)}"
        )
        assert abs(result[0]["amount"] - 52.30) < 0.01
        assert result[0]["category"] == "Food"
        assert result[0]["date"] == "2026-04-01"

    def test_empty_range_returns_empty_list(self, app, demo_user_id):
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date="2000-01-01", to_date="2000-01-31"
            )
        assert result == [], "Empty range must return an empty list"

    def test_limit_none_returns_all_rows_in_range(self, app, demo_user_id):
        """limit=None must omit the LIMIT clause and return all matching rows."""
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert len(result) == 8, "limit=None must return all 8 matching rows"

    def test_limit_respected_with_filter(self, app, demo_user_id):
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=3, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert len(result) == 3, "limit=3 with April filter must return exactly 3 rows"

    def test_ordered_by_date_descending(self, app, demo_user_id):
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        dates = [r["date"] for r in result]
        assert dates == sorted(dates, reverse=True), (
            "Transactions must be ordered by date descending"
        )

    def test_each_row_has_required_keys(self, app, demo_user_id):
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        for row in result:
            assert set(row.keys()) == {"date", "description", "category", "amount"}, (
                f"Transaction row is missing keys: {row.keys()}"
            )

    def test_from_date_only_filters_lower_bound(self, app, demo_user_id):
        """Only from_date set — expenses from Apr-14 onwards."""
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, from_date="2026-04-14"
            )
        assert len(result) == 2, (
            "from_date=2026-04-14 should return 2 expenses (Apr-14, Apr-16)"
        )
        for row in result:
            assert row["date"] >= "2026-04-14"

    def test_to_date_only_filters_upper_bound(self, app, demo_user_id):
        """Only to_date set — expenses up through Apr-03."""
        with app.app_context():
            result = get_recent_transactions(
                demo_user_id, limit=None, to_date="2026-04-03"
            )
        assert len(result) == 2, (
            "to_date=2026-04-03 should return 2 expenses (Apr-01, Apr-03)"
        )
        for row in result:
            assert row["date"] <= "2026-04-03"


# ---------------------------------------------------------------------------
# 13. Unit tests — get_category_breakdown with date filters
# ---------------------------------------------------------------------------


class TestGetCategoryBreakdownFiltered:
    def test_full_april_returns_7_categories(self, app, demo_user_id):
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        # Seed has 7 distinct categories: Food, Transport, Entertainment, Shopping, Bills, Health, Other
        assert len(result) == 7, (
            f"Full April must return 7 distinct categories, got {len(result)}"
        )

    def test_full_april_pct_sums_to_100(self, app, demo_user_id):
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        total_pct = sum(r["pct"] for r in result)
        assert total_pct == 100, (
            f"Category percentages must sum to 100, got {total_pct}"
        )

    def test_each_row_has_required_keys(self, app, demo_user_id):
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        for row in result:
            assert set(row.keys()) == {"name", "amount", "pct"}, (
                f"Category row is missing keys: {row.keys()}"
            )

    def test_ordered_by_amount_descending(self, app, demo_user_id):
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        amounts = [r["amount"] for r in result]
        assert amounts == sorted(amounts, reverse=True), (
            "Category breakdown must be ordered by amount descending"
        )

    def test_single_day_apr01_one_category(self, app, demo_user_id):
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_FROM
            )
        assert len(result) == 1, (
            f"Apr-01 only has one expense (Food), got {len(result)} categories"
        )
        assert result[0]["name"] == "Food"
        assert result[0]["pct"] == 100, "Single category must have pct=100"

    def test_empty_range_returns_empty_list(self, app, demo_user_id):
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date="2000-01-01", to_date="2000-01-31"
            )
        assert result == [], "Empty range must return an empty list for category breakdown"

    def test_shopping_is_highest_category_in_april(self, app, demo_user_id):
        """Shopping (89.00) is the single largest expense category in April."""
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        assert result[0]["name"] == "Shopping", (
            f"Shopping (89.00) must be the top category; got '{result[0]['name']}'"
        )

    def test_pct_values_are_integers(self, app, demo_user_id):
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        for row in result:
            assert isinstance(row["pct"], int), (
                f"pct must be int, got {type(row['pct'])} for category '{row['name']}'"
            )

    def test_food_category_combines_two_expenses(self, app, demo_user_id):
        """Food has two expenses: 52.30 (Apr-01) + 34.50 (Apr-10) = 86.80."""
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date=APRIL_FROM, to_date=APRIL_TO
            )
        food_rows = [r for r in result if r["name"] == "Food"]
        assert len(food_rows) == 1, "Food must appear exactly once (grouped)"
        assert abs(food_rows[0]["amount"] - 86.80) < 0.01, (
            f"Food total must be 86.80, got {food_rows[0]['amount']}"
        )

    def test_from_date_filter_excludes_earlier_categories(self, app, demo_user_id):
        """From Apr-07 onwards: Shopping, Food(10), Bills, Health, Other — no Transport or Entertainment."""
        with app.app_context():
            result = get_category_breakdown(
                demo_user_id, from_date="2026-04-07"
            )
        category_names = [r["name"] for r in result]
        assert "Transport" not in category_names, (
            "Transport (Apr-03) must not appear when from_date=2026-04-07"
        )
        assert "Entertainment" not in category_names, (
            "Entertainment (Apr-05) must not appear when from_date=2026-04-07"
        )
        assert "Shopping" in category_names, (
            "Shopping (Apr-07) must appear when from_date=2026-04-07"
        )

# Spec: Date Filter for Profile Page

## Overview
Step 6 adds date-range filtering to the profile page so users can scope all
three data sections — summary stats, category breakdown, and recent transactions
— to a chosen time window. The `GET /profile` route gains optional query
parameters (`from_date`, `to_date`) and an optional period shortcut
(`period=this_month | last_month | last_3_months`). When no filter is active
the page behaves exactly as it does today. All filtering is done in SQL with
parameterised queries; no new tables are required.

## Depends on
- Step 1: Database setup (`get_db()`, `expenses` table with a `date` column)
- Step 2: Registration (users in the database)
- Step 3: Login / Logout (`session["user_id"]` set on login)
- Step 4: Profile page static UI (template structure already in place)
- Step 5: Backend routes for profile (`get_summary_stats`, `get_recent_transactions`,
  `get_category_breakdown` already wired to the `/profile` route)

## Routes
No new routes. The existing `GET /profile` route is modified to accept the
following optional query parameters:

| Parameter    | Format       | Notes |
|---|---|---|
| `from_date`  | `YYYY-MM-DD` | Inclusive lower bound on `expenses.date` |
| `to_date`    | `YYYY-MM-DD` | Inclusive upper bound on `expenses.date` |
| `period`     | string       | Shortcut: `this_month`, `last_month`, `last_3_months` |

Priority: explicit `from_date`/`to_date` take precedence over `period`. If
neither is present, no date filter is applied (All Time).

## Database changes
No new tables or columns. The `expenses.date` column (`TEXT`, stored as
`YYYY-MM-DD`) already supports lexicographic comparison with `>=` / `<=`
in SQLite.

## Templates
- **Modify:** `templates/profile.html`
  - Add a filter bar above the stats card with:
    - Four preset links: **All Time**, **This Month**, **Last Month**,
      **Last 3 Months** — each is an `<a>` that sets the appropriate query
      string; the active preset is highlighted with a CSS class.
    - A custom date range form (`method="GET"`) with two `<input type="date">`
      fields (`name="from_date"`, `name="to_date"`) and a **Filter** submit
      button.
    - A visible "Showing results for …" label when a filter is active.
  - The summary stats, category breakdown, and transactions table already
    render from template variables; **no structural changes** to those sections
    are needed — only the data passed to them changes.

## Files to change
- `app.py`
  - Read `from_date`, `to_date`, and `period` from `request.args`.
  - Compute concrete `from_date` / `to_date` strings from the `period` shortcut
    using Python's `datetime` module (all arithmetic stays in the route, not
    in query helpers).
  - Validate that `from_date` and `to_date`, if provided, match `YYYY-MM-DD`
    format; silently ignore malformed values (treat as None).
  - Pass `from_date` and `to_date` (may be `None`) to all three query helpers.
  - Pass `from_date`, `to_date`, and the active `period` string back to the
    template so it can highlight the correct preset and pre-fill the date
    inputs.
  - When a date filter is active, remove the `limit` on recent transactions
    (pass `limit=None`) so every expense in the range is shown.
- `database/_transactions.py`
  - Add `from_date: str | None = None` and `to_date: str | None = None`
    parameters to `_get_recent_transactions`.
  - Add `AND date >= ?` / `AND date <= ?` clauses when the parameters are not
    None.
  - When `limit` is `None`, omit the `LIMIT` clause entirely.
- `database/_stats.py`
  - Add `from_date: str | None = None` and `to_date: str | None = None`
    parameters to `_get_summary_stats`.
  - Apply the same date clauses to both the aggregate and the top-category
    queries.
- `database/_categories.py`
  - Add `from_date: str | None = None` and `to_date: str | None = None`
    parameters to `_get_category_breakdown`.
  - Apply date clauses to the group-by query.
- `database/queries.py`
  - Update the three public wrapper functions (`get_summary_stats`,
    `get_recent_transactions`, `get_category_breakdown`) to accept and forward
    `from_date` and `to_date`.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Date comparisons rely on SQLite's lexicographic ordering of `YYYY-MM-DD`
  strings — do not use `DATE()` casting unless required
- `from_date` / `to_date` validation must use `datetime.strptime` with
  `%Y-%m-%d`; catch `ValueError` and treat the input as `None`
- Use CSS variables — never hardcode hex values in templates or stylesheets
- All templates extend `base.html`
- The filter bar must be accessible without JavaScript — preset links are plain
  anchor tags, the custom form is a plain HTML GET form
- When no filter is active, behaviour must be identical to Step 5 (limit=10
  recent transactions, all-time stats)
- `period` arithmetic must use Python's `datetime.date` (stdlib only) —
  compute the first/last day of the target month explicitly, do not rely on
  `timedelta` alone for month boundaries
- Passwords must never be exposed to templates (already enforced; do not
  regress)

## Definition of done
- [ ] Visiting `/profile` with no query params shows the same data as Step 5
      (no regression)
- [ ] Clicking **This Month** shows only expenses in the current calendar month;
      summary stats, breakdown, and transaction table all reflect the filtered
      data
- [ ] Clicking **Last Month** shows only expenses from the previous calendar
      month
- [ ] Clicking **Last 3 Months** shows expenses from the first day of the month
      three months ago through today
- [ ] Clicking **All Time** clears all filters and returns to the unfiltered view
- [ ] Submitting a custom date range (e.g. 2026-04-01 to 2026-04-15) shows
      only expenses within that range across all three data sections
- [ ] The active preset link is visually highlighted
- [ ] When a filter is active a "Showing results for …" label is visible on
      the page
- [ ] A date range that matches no expenses shows ₹0.00 total, 0 transactions,
      and an empty breakdown — no 500 error
- [ ] Malformed date query params (e.g. `?from_date=abc`) are silently ignored
      and the page loads without error
- [ ] Custom date range inputs are pre-filled with the currently active
      `from_date` / `to_date` values after filtering

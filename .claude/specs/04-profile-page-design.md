---
# Spec: Profile Page Design

## Overview
Implement the `/profile` page so logged-in users can view their account details (name, email, and member-since date). This step is purely presentational — no editing or password change yet. It wires up the existing stub route, adds a `get_user_by_id` helper to `db.py`, and builds a styled profile template consistent with the Spendly design system.

## Depends on
- Step 01 — Database Setup (users table must exist)
- Step 02 — Registration (user rows must exist)
- Step 03 — Login and Logout (session must carry `user_id`)

## Routes
- `GET /profile` — render the profile page with the logged-in user's data — logged-in only (redirect to `/login` if not authenticated)

## Database changes
No database changes. The existing `users` table (id, name, email, password_hash, created_at) already holds all required data. A new `get_user_by_id` query function will be added to `database/db.py`.

## Templates
- **Create:** `templates/profile.html` — profile card showing name, email, member-since date, and a logout button
- **Modify:** none

## Files to change
- `app.py` — replace stub `/profile` route with real implementation; add `get_user_by_id` to imports; add login guard
- `database/db.py` — add `get_user_by_id(user_id)` function
- `static/css/style.css` — add profile-page component styles

## Files to create
- `templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw SQL with parameterised queries only
- Use `get_user_by_id` (not `get_user_by_email`) so the lookup is by session `user_id`
- Redirect unauthenticated users to `/login` at the top of the route
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Passwords hashed with werkzeug (already done; do not expose `password_hash` to the template)
- Display `created_at` formatted as a readable date (e.g. "April 1, 2026")
- Profile card must be responsive — usable on mobile widths

## Definition of done
- [ ] Visiting `/profile` while logged out redirects to `/login`
- [ ] Visiting `/profile` while logged in renders a page (no 500 error, no plain-text stub)
- [ ] The page displays the logged-in user's name and email
- [ ] The page displays the member-since date in a human-readable format
- [ ] A logout button/link is visible and works (clears session, redirects to `/login`)
- [ ] The profile card is styled using only CSS variables (no raw hex colours)
- [ ] The page is navigable from the navbar (navbar "Profile" link points to `/profile`)

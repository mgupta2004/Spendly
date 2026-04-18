# Spec: Login and Logout

## Overview
Implement session-based login and logout so registered users can authenticate with Spendly. This step wires up the existing `/login` route (currently GET-only stub) to a real POST handler that validates credentials, starts a Flask session, and redirects to a dashboard placeholder. It also implements `/logout` to clear the session. This is the first step that introduces `flask.session` and a `secret_key`, and it establishes the logged-in/logged-out navigation state used by all future steps.

## Depends on
- Step 1 — Database setup (`users` table, `get_db` working)
- Step 2 — Registration (users exist in the database with hashed passwords)

## Routes
- `GET  /login` — render login form — public
- `POST /login` — validate credentials, start session, redirect to `/dashboard` — public
- `GET  /logout` — clear session, redirect to `/login` — logged-in only

## Database changes
No database changes. The `users` table from Step 1 is sufficient.

## Templates
- **Modify:** `templates/login.html` — two changes required:
  1. Change form `action` to `action="{{ url_for('login') }}"`
  2. Confirm the `{{ error }}` display block is present (it should already be there from the base template convention)
- **Modify:** `templates/base.html` — update navbar links:
  - Show **Logout** link when the user is logged in (`session.get('user_id')`)
  - Show **Login** and **Register** links when the user is logged out

## Files to change
- `app.py` — four changes:
  1. Add `app.secret_key` (use a hardcoded dev string for now; a comment noting it must be an env var in production)
  2. Import `session` from `flask`
  3. Replace the GET-only `/login` stub with a GET/POST handler
  4. Replace the string-returning `/logout` stub with a real handler that clears the session
- `database/db.py` — add a `get_user_by_email(email)` helper that returns a `sqlite3.Row` (or `None`) for the given email
- `templates/login.html` — update form `action` to `url_for('login')`
- `templates/base.html` — conditionally render navbar auth links based on `session.get('user_id')`

## Files to create
None

## New dependencies
No new dependencies. `flask.session` and `werkzeug.security.check_password_hash` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL
- Verify passwords with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Store only `user_id` and `user_name` in the session — never store the password hash
- `secret_key` must be set on `app` before any session use; hardcode a dev string and add a comment that it must come from an env var in production
- `get_user_by_email` lives in `database/db.py`, not in `app.py` — keep DB logic out of route handlers
- On invalid credentials (email not found OR wrong password), re-render `login.html` with a generic `error="Invalid email or password."` — do not distinguish between the two failure modes
- On successful login, redirect to `/dashboard` (stub route is acceptable for now — Step 4 will implement it fully; add a minimal stub if it doesn't exist)
- `/logout` clears the entire session with `session.clear()` and redirects to `/login`
- Validate that `email` and `password` fields are non-empty on POST; re-render with error if blank

## Definition of done
- [ ] `GET /login` renders the login form without errors
- [ ] Submitting valid credentials starts a session and redirects away from `/login`
- [ ] Submitting an unknown email re-renders the form with a generic error message
- [ ] Submitting the correct email but wrong password re-renders the form with the same generic error message
- [ ] Submitting with a blank email or password re-renders the form with an error message
- [ ] After login, the navbar shows a **Logout** link and hides **Login** / **Register**
- [ ] Visiting `/logout` while logged in clears the session and redirects to `/login`
- [ ] After logout, the navbar shows **Login** and **Register** again
- [ ] The session never contains the password or password hash
- [ ] Visiting `/logout` while not logged in redirects to `/login` without error

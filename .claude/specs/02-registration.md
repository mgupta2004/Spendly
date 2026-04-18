# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. This step wires up the existing `/register` route and `register.html` template (already styled) to a real POST handler that validates input, hashes the password, inserts a new user row, and redirects on success. It is the first auth step and unblocks login (Step 3).

## Depends on
- Step 1 — Database setup (`get_db`, `init_db`, `seed_db` all working, `users` table exists)

## Routes
- `GET  /register` — render registration form — public
- `POST /register` — validate input, create user, redirect to `/login` — public

## Database changes
No database changes. The `users` table created in Step 1 is sufficient.

## Templates
- **Modify:** `templates/register.html` — three changes required:
  1. Change `action="/register"` to `action="{{ url_for('register') }}"`
  2. Add a `confirm_password` field (type password) between the password field and the submit button
  - Note: `{{ error }}` display block is already present; no change needed there

## Files to change
- `database/db.py` — add a `create_user(name, email, password)` helper that hashes the password and inserts a row into `users`; raises `sqlite3.IntegrityError` on duplicate email
- `app.py` — replace the GET-only `register` route with a GET/POST handler that validates input, calls `create_user`, and redirects
- `templates/register.html` — update form action to `url_for('register')` and add `confirm_password` field

## Files to create
None

## New dependencies
No new dependencies. `werkzeug.security` is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL
- Hash passwords with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- On duplicate email, catch the `sqlite3.IntegrityError` and re-render the form with `error="An account with that email already exists."`
- Validate that `password == confirm_password` before hitting the database; re-render with an appropriate error message if they differ
- Validate that `name`, `email`, and `password` are non-empty; re-render with error if any are blank
- On success, redirect to `/login` (do not auto-login the user — that is Step 3)
- `create_user` lives in `database/db.py`, not in `app.py` — keep DB logic out of route handlers
- `app.py` imports and calls `create_user`; catches `sqlite3.IntegrityError` for duplicate email
- Use `flask.request`, `flask.redirect`, `flask.url_for` — no new imports beyond what Flask already provides

## Definition of done
- [ ] `GET /register` renders the registration form without errors
- [ ] Submitting the form with valid data inserts a new row into `users` with a hashed password
- [ ] After successful registration, the user is redirected to `/login`
- [ ] Submitting with mismatched passwords re-renders the form with an error message
- [ ] Submitting with a blank name, email, or password re-renders the form with an error message
- [ ] Submitting with an already-registered email re-renders the form with an error message
- [ ] The password is never stored in plain text (verified by inspecting the DB)
- [ ] Registering the same email twice does not create a duplicate row

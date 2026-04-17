# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt

# Run
python app.py                  # Starts at http://127.0.0.1:5001

# Test
pytest
```

## Architecture

**Stack:** Flask + SQLite + Jinja2 templates. No ORM — raw SQL via a custom `db.py` helper.

**`app.py`** — single-file app containing all route definitions. Routes currently implemented: `/`, `/login`, `/register`, `/terms`, `/privacy`. Stub routes (to be implemented): `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`.

**`database/db.py`** — stub file. Must expose three functions: `get_db()`, `init_db()`, `seed_db()`. Database file will be `expense_tracker.db` (gitignored). This is Step 1 of the course implementation.

**`templates/`** — all templates extend `base.html` via Jinja2 block inheritance. Blocks: `title`, `head` (extra CSS), `content`, `scripts` (extra JS). The navbar and footer live in `base.html`. Auth templates (`login.html`, `register.html`) support an `{{ error }}` variable for displaying flash errors.

**`static/css/`** — two stylesheets: `style.css` (global, component-based with CSS custom properties for theming) and `landing.css` (landing page only). Color tokens and typography scale are defined as CSS variables at the top of `style.css`.

## This is a teaching project

The codebase is intentionally incomplete. The UI/styling is done; students progressively implement the backend across numbered steps (database → auth → CRUD). Don't add features beyond what a given step requires.

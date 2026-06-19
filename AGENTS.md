# AI Agent Instructions for job-scraper-bot

## Purpose
This repository contains a single Python scraper for extracting recruitment notices from district websites and writing them into an `umbrella_jobs` Postgres table.

## Key files
- `job_scraper_bot.py` - single entrypoint and full implementation.

## What to know first
- The script is not packaged and has no manifest files (`setup.py`, `pyproject.toml`, `requirements.txt` are absent).
- Dependencies are imported directly in `job_scraper_bot.py`:
  - `requests`
  - `beautifulsoup4`
  - `psycopg2` (optional; the code prints fallback output when unavailable)
- The main function is `process_districts(db_config, district_config=None)`.
- Default behavior is configured in the `if __name__ == "__main__"` block with a local Postgres `DB_CONFIG`.

## Development guidance for AI agents
- Focus changes in `job_scraper_bot.py`; there is currently no other application code.
- Preserve the existing scraping heuristics and fallback behavior unless explicitly improving robustness.
- Do not assume a package manager or dependency installer; if adding dependencies, update documentation or include installation notes in the repo.
- If adding tests or packaging, keep the repo structure simple and avoid introducing unrelated frameworks.

## Special notes
- The script uses `ON CONFLICT (url) DO NOTHING` and attempts to ensure a unique constraint on `umbrella_jobs.url`.
- The code contains inline comments explaining behavior and fallback modes.
- There is currently no separate test suite or CI config.

## When to ask for clarification
- If a change would require new project structure, dependency management, or a test harness.
- If a local Postgres environment is required to verify behavior.

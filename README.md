# job-scraper-bot

This repository implements a scraper for district recruitment notices and a URL validation pipeline for candidate source pages.

## URL Validation Pipeline

The validation pipeline is implemented in `validators/url_validator.py`.

Usage:

```bash
python3 -m validators.url_validator
```

This will:
- read `config/sources/up_districts.csv`
- build candidate recruitment URLs using `config/source_patterns.json`
- validate each candidate URL for HTTP status, redirected URL, and keyword presence
- write reports to `reports/validation`
- write a summary to `validation_summary.json`

## Main Scraper

The main scraper implementation is in `job_scraper_bot.py`.
It extracts recruitment notice links from configured district pages and inserts them into the `umbrella_jobs` table.

```bash
python3 job_scraper_bot.py
```

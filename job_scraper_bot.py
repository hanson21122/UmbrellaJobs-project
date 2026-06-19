import json
import logging
import csv
import os
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# Database pipeline jo naye 'umbrella_jobs' schema me insert karega
# Optional Postgres client; if not installed, DB functions will print an error and skip.
try:
    import psycopg2
    import psycopg2.extras as _psql_extras
except Exception:
    psycopg2 = None
    _psql_extras = None
def insert_to_umbrella_jobs(job_title, job_url, district_name, pdf_url=None):
    print(f"Schema 'umbrella_jobs' me entry check ho rahi hai: {job_title}")
    
    # Yahan aapki purani database connection problems solve ho jayengi
    # Hum 'ON CONFLICT DO NOTHING' ya duplicate check lagayenge taaki pipeline crash na ho
    
    db_payload = {
        "title": job_title,
        "url": job_url,
        "district": district_name,
        "pdf_attachment": pdf_url,
        "status": "active"
    }
    
    # Yeh aapka clean write-layer hai
    # JSON standard format me data verification ke liye:
    print(f"Data ready for pipeline: {json.dumps(db_payload, indent=2)}")
    return db_payload


def print_jobs_fallback(processed):
    print("Database unavailable or connection refused. Running in fallback mode and printing payloads instead of inserting.")
    for title, url, district, pdf_url, status in processed:
        payload = {
            "title": title,
            "url": url,
            "district": district,
            "pdf_attachment": pdf_url,
            "status": status,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def fetch_recruitment_notices(district_url: str, session: requests.Session = None) -> List[Dict[str, str]]:

    """
    `district_url` se saare recruitment notices ka text aur unke links extract karta hai.

    Returns: list of dicts: {"text": ..., "link": ...}
    - Generic heuristic use karta hai: anchor text ya href me common keywords ('recruit', 'notification', 'bharti', etc.) ya PDF links detect karega.
    - Agar anchor ke andar visible text nahin hai to parent element ka text use karega.
    """
    logger = logging.getLogger(__name__)
    s = session or requests.Session()
    try:
        resp = s.get(district_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Request failed for {district_url}: {e}")
        print(f"Request failed for {district_url}: {e}")
        return []

    import re

    soup = BeautifulSoup(resp.text, "html.parser")

    anchors = soup.find_all("a", href=True)
    keywords = [
        "recruit",
        "recruitment",
        "notification",
        "notice",
        "vacancy",
        "vacancies",
        "bharti",
        "advertisement",
        "admit",
        "result",
        "apply",
    ]
    exclude_keywords = [
        "facebook",
        "twitter",
        "x.com",
        "instagram",
        "youtube",
        "share",
        "rti",
        "tender",
        "contact",
        "home",
        "notice_category",
    ]

    def _clean_title(raw_text: str) -> str:
        if not raw_text:
            return ""
        cleaned = raw_text.strip()
        cleaned = re.sub(r'^(view|download)\b[\s:-]*', "", cleaned, flags=re.I)
        cleaned = re.sub(r'[\(\[]\s*\d+(?:\.\d+)?\s*(kb|mb|gb)\s*[\)\]]$', "", cleaned, flags=re.I)
        return cleaned.strip()

    def _is_unhelpful_text(raw_text: str) -> bool:
        if not raw_text:
            return True
        text_value = raw_text.strip()
        if not text_value:
            return True
        if re.match(r'^(view|download)\b', text_value, flags=re.I):
            return True
        if re.fullmatch(r'[\(\[]?\s*\d+(?:\.\d+)?\s*(kb|mb|gb)\s*[\)\]]?', text_value, flags=re.I):
            return True
        return False

    def _find_nearest_title(anchor_tag) -> str:
        for heading_tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            nearby = anchor_tag.find_previous(heading_tag)
            if nearby:
                nearby_text = nearby.get_text(separator=" ", strip=True)
                if nearby_text and not _is_unhelpful_text(nearby_text):
                    return nearby_text

        current = anchor_tag
        while current is not None:
            prev = current.previous_sibling
            while prev is not None:
                if hasattr(prev, "get_text"):
                    candidate = prev.get_text(separator=" ", strip=True)
                    if candidate and not _is_unhelpful_text(candidate):
                        return candidate
                prev = prev.previous_sibling
            current = getattr(current, "parent", None)

        parent_text = anchor_tag.parent.get_text(separator=" ", strip=True) if anchor_tag.parent is not None else ""
        if parent_text and not _is_unhelpful_text(parent_text):
            return parent_text
        return ""

    results: List[Dict[str, str]] = []
    seen = set()
    for a in anchors:
        text = (a.get_text(separator=" ", strip=True) or "").strip()
        href = a["href"].strip()
        full = urljoin(district_url, href)

        lower_text = text.lower()
        lower_href = href.lower()
        is_pdf = ".pdf" in lower_href or lower_href.endswith(".pdf")
        matches_kw = (
            any(k in lower_text for k in keywords)
            or any(k in lower_href for k in keywords)
        )
        excluded = (
            any(k in lower_text for k in exclude_keywords)
            or any(k in lower_href for k in exclude_keywords)
        ) or any(k in lower_href for k in keywords)

        title = _clean_title(text)
        if not title or _is_unhelpful_text(text) or is_pdf:
            candidate = _find_nearest_title(a)
            if candidate:
                title = _clean_title(candidate)
            elif not title:
                fallback = a.parent.get_text(separator=" ", strip=True)
                title = _clean_title(fallback) or text

        if (matches_kw or is_pdf) and not excluded:
            if full in seen:
                continue
            seen.add(full)
            if not title:
                title = a.parent.get_text(separator=" ", strip=True)
            results.append({"text": title, "link": full})

    return results


def insert_jobs_to_umbrella(jobs: List[Dict[str, str]], district_name: str, db_config, session: requests.Session = None) -> int:
    """
    Process `jobs` (as returned by `fetch_recruitment_notices`) and insert into `umbrella_jobs` Postgres table.

    - `db_config` can be a dict of connection params for `psycopg2.connect(**db_config)`
      e.g. {"dbname": "db", "user": "u", "password": "p", "host": "localhost", "port": 5432}
    - Returns number of rows inserted (approximate; counts only successful INSERTs).
    - Uses `ON CONFLICT (url) DO NOTHING` to avoid duplicates. Assumes `url` has a UNIQUE constraint.
    """
    logger = logging.getLogger(__name__)
    s = session or requests.Session()

    # Enrich jobs with PDF detection
    processed = []  # tuples of (title, url, district, pdf_url, status)
    for j in jobs:
        title = j.get("text") or None
        link = j.get("link")
        if not link:
            continue
        pdf_url = None
        try:
            l_lower = link.lower()
            if l_lower.endswith(".pdf"):
                pdf_url = link
            else:
                # Try HEAD first to check content-type
                try:
                    h = s.head(link, allow_redirects=True, timeout=10)
                    ctype = h.headers.get("content-type", "").lower()
                    if "application/pdf" in ctype or h.url.lower().endswith(".pdf"):
                        pdf_url = h.url
                    else:
                        # fetch page and look for first PDF link
                        p = s.get(link, timeout=10)
                        p.raise_for_status()
                        page_soup = BeautifulSoup(p.text, "html.parser")
                        a_pdf = page_soup.find("a", href=lambda href: href and href.lower().endswith('.pdf'))
                        if a_pdf:
                            pdf_url = urljoin(link, a_pdf["href"])
                except Exception:
                    # best-effort: skip PDF detection on failure
                    pdf_url = None

        except Exception as e:
            logger.error(f"Error while checking PDFs for {link}: {e}")
            print(f"Error while checking PDFs for {link}: {e}")

        processed.append((title, link, district_name, pdf_url, "active"))

    if not processed:
        logger.info("No jobs to insert after processing.")
        print("No jobs to insert after processing.")
        return 0

    if not psycopg2:
        logger.warning("psycopg2 not installed - skipping DB insert and switching to fallback mode.")
        print("psycopg2 not installed - skipping DB insert and switching to fallback mode.")
        print_jobs_fallback(processed)
        return len(processed)

    # Insert into Postgres with ON CONFLICT DO NOTHING
    inserted = 0
    conn = None
    try:
        # support passing DSN string or dict
        if isinstance(db_config, str):
            conn = psycopg2.connect(db_config)
        else:
            conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        insert_sql = (
            "INSERT INTO umbrella_jobs (title, url, district, pdf_attachment, status)"
            " VALUES (%s, %s, %s, %s, %s)"
            " ON CONFLICT (url) DO NOTHING"
            " RETURNING 1"
        )

        for row in processed:
            try:
                cur.execute(insert_sql, row)
                res = cur.fetchone()
                if res:
                    inserted += 1
            except Exception as e:
                # skip bad rows but continue
                logger.warning(f"Insert failed for {row[1]}: {e}")
                print(f"Insert failed for {row[1]}: {e}")
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"DB insert failed: {e}")
        print(f"DB insert failed: {e}")
        print_jobs_fallback(processed)
        return len(processed)
    finally:
        if conn:
            conn.close()

    logger.info(f"Inserted {inserted} new rows into umbrella_jobs (attempted {len(processed)})")
    print(f"Inserted {inserted} new rows into umbrella_jobs (attempted {len(processed)}).")
    return inserted


def ensure_umbrella_jobs_url_unique_constraint(db_config):
    """
    Ensure the `umbrella_jobs.url` column has a UNIQUE constraint.
    This is an idempotent migration/query helper that will not fail if the
    constraint already exists.

    This keeps PostgreSQL `ON CONFLICT (url) DO NOTHING` working correctly
    even when the table is loaded multiple times.
    """
    if not psycopg2:
        print("psycopg2 not installed - cannot enforce UNIQUE constraint on url.")
        return False

    conn = None
    try:
        if isinstance(db_config, str):
            conn = psycopg2.connect(db_config)
        else:
            conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        # Idempotent constraint creation: check pg_constraint before ALTER.
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint c
                    JOIN pg_class t ON c.conrelid = t.oid
                    WHERE c.conname = 'umbrella_jobs_url_key'
                      AND t.relname = 'umbrella_jobs'
                ) THEN
                    ALTER TABLE umbrella_jobs
                    ADD CONSTRAINT umbrella_jobs_url_key UNIQUE (url);
                END IF;
            END
            $$;
            """
        )
        conn.commit()
        cur.close()
        print("Ensured UNIQUE constraint on umbrella_jobs.url.")
        return True
    except Exception as e:
        print(f"Failed to ensure UNIQUE constraint on umbrella_jobs.url: {e}")
        return False
    finally:
        if conn:
            conn.close()


def setup_logging(log_dir: str = "logs"):
    """Setup logging to file and console."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "job_scraper.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_district_config(config_path: str = "config/districts.json") -> Dict[str, str]:
    """
    Load district configuration from JSON file.
    
    Returns dict mapping district name to URL.
    Raises FileNotFoundError if config file is missing.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"District configuration file not found: {config_path}\n"
            f"Please create {config_path} with the following format:\n"
            f'{{"districts": [{{"name": "District Name", "url": "https://..."}}]}}'
        )
    
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    district_config = {}
    if "districts" in config_data:
        for district in config_data["districts"]:
            name = district.get("name")
            url = district.get("url")
            if name and url:
                district_config[name] = url
    
    if not district_config:
        raise ValueError("No valid districts found in configuration file.")
    
    return district_config


def export_to_csv(jobs_data: List[Dict[str, str]], export_dir: str = "reports"):
    """
    Export collected jobs to CSV file.
    
    jobs_data: list of dicts with keys: text, link, district, pdf_attachment
    """
    os.makedirs(export_dir, exist_ok=True)
    export_file = os.path.join(export_dir, "jobs_export.csv")
    
    try:
        with open(export_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'url', 'district', 'pdf_attachment', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in jobs_data:
                writer.writerow({
                    'title': job.get('text', ''),
                    'url': job.get('link', ''),
                    'district': job.get('district', ''),
                    'pdf_attachment': job.get('pdf_attachment', ''),
                    'status': job.get('status', 'active')
                })
        
        logging.info(f"Exported {len(jobs_data)} jobs to {export_file}")
        return export_file
    except Exception as e:
        logging.error(f"Failed to export jobs to CSV: {e}")
        raise




def process_districts(db_config, district_config=None):
    """
    Process districts: fetch recruitment notices, insert to DB, and export to CSV.
    """
    logger = logging.getLogger(__name__)
    
    if district_config is None:
        try:
            district_config = load_district_config()
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to load district config: {e}")
            raise
    
    if not ensure_umbrella_jobs_url_unique_constraint(db_config):
        logger.warning("URL uniqueness enforcement failed. ON CONFLICT may not work as expected.")

    total_districts = len(district_config)
    total_jobs_found = 0
    total_inserted = 0
    total_errors = 0
    all_jobs = []  # Collect all jobs for CSV export

    for district_name, district_url in district_config.items():
        logger.info(f"Processing district: {district_name} - {district_url}")
        try:
            jobs = fetch_recruitment_notices(district_url)
            if not jobs:
                logger.info(f"No recruitment notices found for {district_name}")
                continue

            for job in jobs:
                job['district'] = district_name

            inserted = insert_jobs_to_umbrella(jobs, district_name, db_config)
            total_jobs_found += len(jobs)
            total_inserted += inserted
            all_jobs.extend(jobs)
            
            logger.info(f"{district_name}: found {len(jobs)} jobs, inserted {inserted} new rows")
        except Exception as e:
            total_errors += 1
            logger.error(f"Error processing {district_name}: {e}")
            continue

    # Export collected jobs to CSV
    try:
        if all_jobs:
            for job in all_jobs:
                job['status'] = 'active'
            export_to_csv(all_jobs)
    except Exception as e:
        logger.error(f"CSV export failed: {e}")

    print("\n=== Summary Report ===")
    print(f"Total districts configured: {total_districts}")
    print(f"Total jobs found: {total_jobs_found}")
    print(f"Total rows inserted/fallback printed: {total_inserted}")
    print(f"Total errors encountered: {total_errors}")
    print("======================")
    
    logger.info(f"Summary: {total_districts} districts, {total_jobs_found} jobs found, {total_inserted} inserted, {total_errors} errors")

    return {
        "total_districts": total_districts,
        "total_jobs_found": total_jobs_found,
        "total_inserted": total_inserted,
        "total_errors": total_errors,
    }


if __name__ == "__main__":
    # Setup logging
    logger = setup_logging()
    logger.info("Job Scraper Bot started")
    
    # PostgreSQL database connection settings for the migrated umbrella_jobs schema.
    DB_CONFIG = {
        "dbname": "umbrella_jobs",
        "user": "postgres",
        "password": "password",
        "host": "localhost",
        "port": 5432,
    }

    try:
        process_districts(DB_CONFIG)
        logger.info("Job Scraper Bot completed successfully")
    except Exception as e:
        logger.error(f"Job Scraper Bot failed: {e}")
        raise

"""
Application History and Version Archive for Resume Tailor.
Persists tailored resumes, match scores, keyword analytics, and compiled PDFs
for every job application.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "applications"
PDFS_DIR = DATA_DIR / "pdfs"
INDEX_FILE = DATA_DIR / "applications.json"


def ensure_dirs():
    """Ensure data directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def slugify(text: str) -> str:
    """Generate a clean URL/filename slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text)[:40]


def save_application(
    company: str,
    role_title: str,
    match_score: int,
    match_rating: str,
    job_description: str,
    matched_keywords: List[str],
    missing_keywords: List[str],
    tailored_summary: str,
    tailored_experience: List[Dict[str, Any]],
    pdf_bytes: Optional[bytes] = None,
    job_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Save a tailored resume application record and its generated PDF."""
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    company_slug = slugify(company or "company")
    role_slug = slugify(role_title or "role")
    app_id = f"{time_slug}_{company_slug}_{role_slug}"

    pdf_filename = f"{app_id}.pdf"
    pdf_path = PDFS_DIR / pdf_filename

    if pdf_bytes:
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

    record = {
        "id": app_id,
        "timestamp": timestamp,
        "company": company or "Unknown Company",
        "role_title": role_title or "Cybersecurity Specialist",
        "job_url": job_url or "",
        "match_score": match_score,
        "match_rating": match_rating,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "tailored_summary": tailored_summary,
        "tailored_experience": tailored_experience,
        "job_description_snippet": (job_description[:400] + "...") if len(job_description) > 400 else job_description,
        "pdf_filename": pdf_filename if pdf_bytes else None,
    }

    # Append to applications.json
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        try:
            applications = json.load(f)
        except Exception:
            applications = []

    applications.insert(0, record)  # Most recent first

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(applications, f, indent=2)

    return record


def list_applications() -> List[Dict[str, Any]]:
    """List all saved applications ordered by newest first."""
    ensure_dirs()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def get_application_pdf(pdf_filename: str) -> Optional[bytes]:
    """Retrieve saved PDF bytes for an application."""
    if not pdf_filename:
        return None
    pdf_path = PDFS_DIR / pdf_filename
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            return f.read()
    return None


def delete_application(app_id: str) -> bool:
    """Delete an application record and its PDF."""
    ensure_dirs()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        try:
            applications = json.load(f)
        except Exception:
            return False

    updated = []
    deleted = False
    for app in applications:
        if app.get("id") == app_id:
            deleted = True
            pdf_name = app.get("pdf_filename")
            if pdf_name:
                pdf_p = PDFS_DIR / pdf_name
                if pdf_p.exists():
                    try:
                        pdf_p.unlink()
                    except Exception:
                        pass
        else:
            updated.append(app)

    if deleted:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2)

    return deleted

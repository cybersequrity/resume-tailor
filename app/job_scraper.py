"""
Private Sector & Contractor Job Posting Scraper for Resume Tailor.
Extracts job title, company, location, and description from public job URLs
using Playwright headless browser.
"""

import re
from typing import Any, Dict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def clean_job_text(text: str) -> str:
    """Clean boilerplate noise, excess whitespace, and navigation fragments."""
    # Remove multiple blank lines
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    # Remove common tracking / cookie disclaimers if isolated
    lines = []
    for line in text.split('\n'):
        line_clean = line.strip()
        if not line_clean:
            lines.append("")
            continue
        # Skip generic cookie / header noise lines
        if any(noise in line_clean.lower() for noise in [
            "cookie policy", "accept all cookies", "manage cookies",
            "skip to main content", "all rights reserved"
        ]) and len(line_clean) < 80:
            continue
        lines.append(line_clean)
    return "\n".join(lines).strip()


def scrape_job_url(url: str, timeout_ms: int = 15000) -> Dict[str, Any]:
    """
    Scrape a job posting from a private sector or contractor career page.
    Supports LinkedIn, Greenhouse, Lever, Indeed, Workday, and company career sites.
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900}
            )
            page = context.new_page()

            # Navigate to the page
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(2000)  # Brief pause for dynamic hydration

            title = ""
            company = ""
            location = ""
            description = ""

            # 1. Site-specific extractors for top ATS platforms
            url_lower = url.lower()

            # Greenhouse
            if "greenhouse.io" in url_lower:
                title_elem = page.query_selector(".app-title, h1.app-title, h1")
                company_elem = page.query_selector(".company-name")
                desc_elem = page.query_selector("#content, #main, .content")
                if title_elem:
                    title = title_elem.inner_text().strip()
                if company_elem:
                    company = company_elem.inner_text().strip()
                if desc_elem:
                    description = desc_elem.inner_text().strip()

            # Lever
            elif "lever.co" in url_lower:
                title_elem = page.query_selector(".posting-headline h2, h2")
                company_elem = page.query_selector(".main-header-logo img, a.main-header-logo")
                desc_elem = page.query_selector(".content, .section.page-centered")
                if title_elem:
                    title = title_elem.inner_text().strip()
                if desc_elem:
                    description = desc_elem.inner_text().strip()

            # LinkedIn public job posts
            elif "linkedin.com/jobs" in url_lower:
                title_elem = page.query_selector("h1.topcard__title, h1.top-card-layout__title, h1")
                company_elem = page.query_selector("a.topcard__org-name-link, span.topcard__flavor, .topcard__flavor--black-link")
                loc_elem = page.query_selector("span.topcard__flavor--bullet, .top-card-layout__first-subline .topcard__flavor")
                desc_elem = page.query_selector(".description__text, .show-more-less-html__markup, .job-description")
                if title_elem:
                    title = title_elem.inner_text().strip()
                if company_elem:
                    company = company_elem.inner_text().strip()
                if loc_elem:
                    location = loc_elem.inner_text().strip()
                if desc_elem:
                    description = desc_elem.inner_text().strip()

            # Indeed
            elif "indeed.com" in url_lower:
                title_elem = page.query_selector("h1.jobsearch-JobInfoHeader-title, h1")
                company_elem = page.query_selector("[data-company-name='true'], .jobsearch-CompanyInfoContainer a")
                desc_elem = page.query_selector("#jobDescriptionText, .jobsearch-jobDescriptionText")
                if title_elem:
                    title = title_elem.inner_text().strip()
                if company_elem:
                    company = company_elem.inner_text().strip()
                if desc_elem:
                    description = desc_elem.inner_text().strip()

            # Generic fallback: heuristics based on standard semantic tags
            if not description:
                # Try finding standard job description containers
                for selector in [
                    "main", "[role='main']", "article", "#job-description",
                    ".job-description", ".description", ".posting-description",
                    "#content", ".job-details"
                ]:
                    elem = page.query_selector(selector)
                    if elem:
                        txt = elem.inner_text().strip()
                        if len(txt) > 300:
                            description = txt
                            break

            # If still not found, get full body text
            if not description:
                description = page.inner_text("body")

            if not title:
                h1 = page.query_selector("h1")
                title = h1.inner_text().strip() if h1 else page.title()

            browser.close()

            cleaned_desc = clean_job_text(description)

            # Extract company from title tag if missing (e.g. "Security Analyst at CyberCorp")
            if not company and " at " in title:
                parts = title.split(" at ")
                title = parts[0].strip()
                company = parts[1].split(" - ")[0].strip()

            return {
                "success": True,
                "url": url,
                "title": title or "Job Position",
                "company": company or "Target Organization",
                "location": location,
                "description": cleaned_desc
            }

    except PlaywrightTimeoutError:
        return {
            "success": False,
            "error": "Timeout while connecting to job URL. The site may have strict bot protection or took too long to respond."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to scrape job page: {str(e)}"
        }

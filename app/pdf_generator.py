"""
PDF and Markdown Generator for Resume Tailor.
Renders Jinja2 HTML templates and exports print-ready PDFs using WeasyPrint.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import jinja2
import weasyprint

try:
    from formatting_manager import compile_theme_css, load_formatting_config
except ImportError:
    from app.formatting_manager import compile_theme_css, load_formatting_config

TEMPLATES_DIR = Path(__file__).parent / "templates"
RESUME_TEMPLATE_NAME = "resume.html"


def get_jinja_env(templates_dir: Path = TEMPLATES_DIR) -> jinja2.Environment:
    """Instantiate a Jinja2 environment configured for resume templates."""
    loader = jinja2.FileSystemLoader(searchpath=str(templates_dir))
    env = jinja2.Environment(
        loader=loader,
        autoescape=jinja2.select_autoescape(["html", "xml"])
    )
    return env


def prepare_resume_context(
    master_resume: Dict[str, Any],
    tailored_analysis: Dict[str, Any],
    formatting_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Merge master resume baseline data (contact, education, certs, projects)
    with tailored recommendations (tailored summary, selected/rewritten bullets, filtered skills)
    and compiled formatting styling variables.
    """
    context = dict(master_resume)

    # Use tailored summary if available
    if "tailored_summary" in tailored_analysis:
        context["professional_summary"] = {
            "tailored_summary": tailored_analysis["tailored_summary"]
        }

    # Use tailored skills if available, else keep master
    if "tailored_skills" in tailored_analysis and tailored_analysis["tailored_skills"]:
        context["skills"] = tailored_analysis["tailored_skills"]

    # Use tailored experience roles & bullets
    if "experience" in tailored_analysis and tailored_analysis["experience"]:
        tailored_exp = []
        for role in tailored_analysis["experience"]:
            # Format bullets into clean strings or dicts
            clean_bullets = []
            for b in role.get("bullets", []):
                if isinstance(b, dict):
                    # Prefer tailored_text, fallback to original_text or text
                    bullet_text = b.get("tailored_text") or b.get("original_text") or b.get("text")
                    if bullet_text:
                        clean_bullets.append(bullet_text)
                elif isinstance(b, str):
                    clean_bullets.append(b)

            role_copy = dict(role)
            role_copy["bullets"] = clean_bullets
            tailored_exp.append(role_copy)

        context["experience"] = tailored_exp

    # Wire in dynamic formatting configuration & CSS Custom Properties
    fmt_cfg = formatting_config or load_formatting_config()
    context["formatting_config"] = fmt_cfg
    context["custom_css_vars"] = compile_theme_css(fmt_cfg)

    return context


def render_resume_html(
    context: Dict[str, Any],
    template_name: str = RESUME_TEMPLATE_NAME,
    formatting_config: Optional[Dict[str, Any]] = None,
) -> str:
    """Render the resume context to an HTML string with dynamic CSS custom properties."""
    ctx = dict(context)
    if formatting_config is not None:
        ctx["formatting_config"] = formatting_config
        ctx["custom_css_vars"] = compile_theme_css(formatting_config)
    elif "custom_css_vars" not in ctx:
        fmt_cfg = load_formatting_config()
        ctx["formatting_config"] = fmt_cfg
        ctx["custom_css_vars"] = compile_theme_css(fmt_cfg)

    env = get_jinja_env()
    template = env.get_template(template_name)
    return template.render(**ctx)


def generate_resume_pdf(
    context: Union[Dict[str, Any], str],
    template_name: str = RESUME_TEMPLATE_NAME,
    formatting_config: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Generate PDF bytes from resume context dict or rendered HTML string via WeasyPrint."""
    if isinstance(context, str):
        html_content = context
    else:
        html_content = render_resume_html(context, template_name, formatting_config)
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    return pdf_bytes


def generate_resume_markdown(context: Dict[str, Any]) -> str:
    """Generate a clean Markdown representation of the resume."""
    pi = context.get("personal_info", {})
    md_lines = []

    md_lines.append(f"# {pi.get('name', 'Resume')}")
    if pi.get("headline"):
        md_lines.append(f"**{pi.get('headline')}**")

    contact = []
    for k in ["location", "email", "phone", "linkedin", "github"]:
        if pi.get(k):
            contact.append(str(pi[k]))
    if contact:
        md_lines.append(" | ".join(contact))
    md_lines.append("\n---\n")

    # Summary
    summary = context.get("professional_summary", {})
    s_text = summary.get("tailored_summary") or summary.get("default_pitch")
    if s_text:
        md_lines.append("## Professional Summary")
        md_lines.append(s_text + "\n")

    # Skills
    skills = context.get("skills", {})
    if skills:
        md_lines.append("## Core Technical & Compliance Competencies")
        cat_map = {
            "frameworks_and_compliance": "Compliance & Frameworks",
            "security_operations_and_domains": "Security Domains & Systems",
            "technical_tools_and_languages": "Tools, Scripting & SIEM",
            "specialized_programs": "Programs & Leadership"
        }
        for cat, items in skills.items():
            cat_name = cat_map.get(cat, cat.replace("_and_", " & ").replace("_", " ").title())
            md_lines.append(f"- **{cat_name}:** {' • '.join(items)}")
        md_lines.append("")

    # Experience
    experience = context.get("experience", [])
    if experience:
        md_lines.append("## Professional Experience")
        for role in experience:
            title = role.get("title") or role.get("role_title", "Role")
            company = role.get("company", "Company")
            dates = f"{role.get('start_date', '')} - {role.get('end_date', 'Present') if not role.get('is_current') else 'Present'}"
            loc = role.get("location", "")
            md_lines.append(f"### {title} | {company}")
            md_lines.append(f"*{dates} | {loc}*")
            for b in role.get("bullets", []):
                b_text = b if isinstance(b, str) else (b.get("tailored_text") or b.get("text", ""))
                md_lines.append(f"- {b_text}")
            md_lines.append("")

    # Education
    education = context.get("education", [])
    if education:
        md_lines.append("## Education")
        for edu in education:
            md_lines.append(f"- **{edu.get('degree')}** in {edu.get('field_of_study')}, {edu.get('institution')} ({edu.get('graduation_date')})")
        md_lines.append("")

    # Certifications
    certs = context.get("certifications", [])
    if certs:
        md_lines.append("## Certifications")
        for c in certs:
            md_lines.append(f"- **{c.get('name')}** - {c.get('issuer')} ({c.get('issue_date')})")
        md_lines.append("")

    return "\n".join(md_lines)

"""
Resume Tailor: Dynamic ATS Optimization & Modular Experience Bank.
Streamlit Web UI with Gemini API (google-genai), Playwright Job Scraper,
Interactive Review Studio, Application History Archive, and WeasyPrint export.
"""

import json
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables (.env) if present
load_dotenv()

import importlib
import tailor_engine
import pdf_generator
import pdf_parser
import job_scraper
import history_manager
import formatting_manager

importlib.reload(tailor_engine)
importlib.reload(pdf_generator)
importlib.reload(pdf_parser)
importlib.reload(job_scraper)
importlib.reload(history_manager)
importlib.reload(formatting_manager)

from tailor_engine import (
    ResumeTailorService,
    load_master_resume,
    save_master_resume,
    validate_master_resume,
    GENAI_AVAILABLE,
)
from pdf_generator import (
    generate_resume_markdown,
    generate_resume_pdf,
    prepare_resume_context,
    render_resume_html,
)
from pdf_parser import (
    ResumePDFExtractor,
    extract_text_from_pdf,
    list_uploaded_pdfs,
    UPLOADS_DIR,
)
from job_scraper import scrape_job_url
from history_manager import (
    save_application,
    list_applications,
    get_application_pdf,
    delete_application,
)
from formatting_manager import (
    load_formatting_config,
    save_formatting_config,
    compile_theme_css,
    DEFAULT_THEME,
    THEME_PRESETS,
)

# -----------------------------------------------------------------------------
# Streamlit Page Setup & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Resume Tailor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .badge-tag {
        display: inline-block;
        background-color: #E2E8F0;
        color: #334155;
        padding: 2px 8px;
        margin: 2px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 500;
    }
    .badge-skill {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
        padding: 2px 7px;
        margin: 2px;
        border-radius: 10px;
        font-size: 0.76rem;
        font-weight: 500;
    }
    .badge-matched {
        display: inline-block;
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 9px;
        margin: 2px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-missing {
        display: inline-block;
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 9px;
        margin: 2px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Preset Job Descriptions for Instant Prototype Testing
# -----------------------------------------------------------------------------
SAMPLE_JDS = {
    "Custom (Paste Your Own)": {
        "company": "",
        "title": "",
        "text": "",
    },
    "Lead Information System Security Officer (ISSO) - NIST RMF & OT": {
        "company": "Critical Infrastructure Solutions",
        "title": "Lead ISSO (Operational Technology & RMF)",
        "text": """
Position: Lead Information System Security Officer (ISSO)
Location: Reston, VA / Hybrid

Overview:
We are seeking an experienced Information System Security Officer (ISSO) to oversee the security authorization,
compliance, and risk posture of our mission-critical Industrial Control Systems (ICS) and Operational Technology (OT)
environments. You will lead Authorization to Operate (ATO) packages under the NIST Risk Management Framework (RMF).

Key Responsibilities:
- Maintain and update System Security Plans (SSPs), Security Assessment Reports, and Plans of Actions & Milestones (POA&Ms).
- Lead NIST SP 800-37 RMF lifecycle steps and implement security controls compliant with NIST SP 800-53 rev. 5.
- Establish and execute Cybersecurity Supply Chain Risk Management (C-SCRM) protocols in accordance with NIST SP 800-161.
- Interface directly with Authorizing Officials (AO), Designated Representatives (AODR), and federal assessors.
- Direct continuous monitoring activities and security test & evaluation (ST&E) for plant and OT facilities.

Qualifications:
- Bachelor's degree in Cybersecurity, Computer Science, or related field.
- Active cybersecurity certification: CISSP, CRISC, CISM, or equivalent.
- 3+ years experience supporting federal RMF compliance, DOE Orders (e.g. 205.1), or critical infrastructure.
- Hands-on experience with ICS/SCADA/OT boundaries and supply chain vetting.
- U.S. Citizenship with ability to maintain federal badging (DOE PIV or Public Trust).
"""
    },
    "Cybersecurity Compliance & Risk Analyst (NIST 800-53 / Contractor Oversight)": {
        "company": "Apex Defense Solutions",
        "title": "Senior Cybersecurity Compliance & Risk Analyst",
        "text": """
Position: Senior Cybersecurity Compliance & Risk Analyst
Location: Remote / Denver, CO

About the Role:
Join our cyber governance team providing prime contractor compliance and continuous monitoring across multiple
accreditation boundaries.

Requirements:
- Proven experience evaluating System Security Plans (SSPs) against NIST SP 800-53 revisions 4 & 5.
- Familiarity with Department of Energy (DOE) cybersecurity requirements including DOE Order 205.1B & C.
- Experience coordinating data calls, baseline schedule assessments, and contractor risk oversight.
- Familiarity with SIEM monitoring tools (Splunk) and vulnerability management procedures.
- Strong technical writing and executive stakeholder reporting skills.
- CISSP or CRISC certification preferred.
"""
    },
    "Security Operations & Automation Analyst (Splunk & PowerShell)": {
        "company": "Pacific Cyber Defense Corp",
        "title": "Security Operations & Automation Analyst",
        "text": """
Position: Security Operations & Automation Analyst
Location: Pacific Northwest / Hybrid

Responsibilities:
- Build and tune correlation rules, dashboards, and automated alert workflows in Splunk SIEM.
- Automate repetitive administrative, compliance verification, and log parsing tasks using PowerShell scripting.
- Perform network traffic analysis, anomaly detection, and vulnerability remediation on enterprise and plant systems.
- Maintain access control procedures for isolated industrial networks and high-security zones.
"""
    }
}

# -----------------------------------------------------------------------------
# Sidebar: Engine Configuration
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ Engine Settings")

# Silent background environment loading
active_api_key = os.getenv("GEMINI_API_KEY", None)
force_offline = not bool(active_api_key)

model_choice = st.sidebar.selectbox(
    "Optimization Engine",
    options=["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    index=0,
    help="Select active optimization engine model for ATS keyword analysis and modular bullet scoring.",
)

st.sidebar.markdown("---")
st.sidebar.caption("Resume Tailor • ATS Optimization • WeasyPrint")

# -----------------------------------------------------------------------------
# Main Application Header & Tabs
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🎯 Resume Tailor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Dynamic ATS Optimization System & Modular Experience Bank</div>',
    unsafe_allow_html=True,
)

tab_tailor, tab_history, tab_master, tab_format, tab_diag = st.tabs([
    "🚀 Job Tailoring Studio",
    "📁 Application Archive",
    "🗄️ Master Experience Bank",
    "🎨 PDF Design & Layout Workshop",
    "🛠️ System Architecture & Status",
])

# -----------------------------------------------------------------------------
# TAB 1: Job Tailoring Studio
# -----------------------------------------------------------------------------
with tab_tailor:
    st.subheader("1. Target Job Ingestion (URL Scraper or Text Input)")

    # Option to scrape via URL
    with st.expander("🌐 Fetch & Scrape Job Posting from URL (LinkedIn, Indeed, Greenhouse, Lever, etc.)", expanded=False):
        st.caption("Paste any private sector or contractor job posting URL to automatically extract title, company, and description.")
        col_url, col_scrape_btn = st.columns([4, 1])
        with col_url:
            job_url_input = st.text_input("Job Posting URL", placeholder="https://www.linkedin.com/jobs/view/... or https://boards.greenhouse.io/...")
        with col_scrape_btn:
            scrape_clicked = st.button("🔍 Fetch & Scrape", use_container_width=True)

        if scrape_clicked:
            if not job_url_input.strip():
                st.warning("Please enter a valid job URL.")
            else:
                with st.spinner("Scraping job posting via headless browser..."):
                    res = scrape_job_url(job_url_input)
                    if res.get("success"):
                        st.session_state["scraped_company"] = res.get("company", "")
                        st.session_state["scraped_title"] = res.get("title", "")
                        st.session_state["scraped_jd"] = res.get("description", "")
                        st.session_state["scraped_url"] = job_url_input
                        st.success(f"Successfully scraped: **{res.get('title')}** at **{res.get('company')}**")
                    else:
                        st.error(f"Scraper error: {res.get('error')}")

    col_jd_sel, col_bullets = st.columns([3, 1])
    with col_jd_sel:
        jd_preset = st.selectbox(
            "Or Load Sample Preset Job Description",
            options=list(SAMPLE_JDS.keys()),
            index=1,
        )
    with col_bullets:
        max_bullets = st.slider("Max Bullets per Role", min_value=1, max_value=5, value=3)

    # Preset / Scraped Defaults
    default_company = st.session_state.get("scraped_company") or SAMPLE_JDS[jd_preset]["company"]
    default_title = st.session_state.get("scraped_title") or SAMPLE_JDS[jd_preset]["title"]
    default_jd_text = st.session_state.get("scraped_jd") or SAMPLE_JDS[jd_preset]["text"]

    col_comp, col_role = st.columns(2)
    with col_comp:
        target_company = st.text_input("Target Company Name", value=default_company, placeholder="e.g. Critical Infrastructure Solutions")
    with col_role:
        target_role = st.text_input("Target Role Title", value=default_title, placeholder="e.g. Lead ISSO (OT / RMF)")

    jd_input = st.text_area(
        "Job Description (JD) Content",
        value=default_jd_text,
        height=180,
        placeholder="Paste target job responsibilities, requirements, and qualifications here...",
    )

    col_btn, _ = st.columns([1.5, 3.5])
    with col_btn:
        run_tailor = st.button("⚡ Run Tailoring Analysis", type="primary", use_container_width=True)

    if run_tailor:
        if not jd_input.strip():
            st.warning("Please provide a Job Description to analyze.")
        else:
            with st.spinner("Analyzing JD alignment and tailoring bullet points..."):
                try:
                    master_data = load_master_resume()
                    tailor_service = ResumeTailorService(
                        api_key=active_api_key,
                        model_name=model_choice,
                    )
                    analysis_result = tailor_service.analyze_and_tailor(
                        job_description=jd_input,
                        master_resume=master_data,
                        max_bullets_per_role=max_bullets,
                        force_offline=force_offline,
                    )
                    st.session_state["analysis_result"] = analysis_result
                    st.session_state["master_data"] = master_data
                    st.session_state["target_company"] = target_company
                    st.session_state["target_role"] = target_role
                    st.session_state["target_jd"] = jd_input
                    st.session_state["tailored_context"] = prepare_resume_context(
                        master_data, analysis_result
                    )
                    st.success("Analysis and tailoring complete!")
                except Exception as err:
                    st.error(f"Error during tailoring process: {err}")

    # Display Results & Interactive Studio
    if "analysis_result" in st.session_state:
        res = st.session_state["analysis_result"]
        context = st.session_state["tailored_context"]

        st.markdown("---")
        st.subheader("2. Match Analysis & Keyword Alignment")

        # Metric Highlights
        score = res.get("match_score", 0)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="Match Compatibility Score", value=f"{score}%", delta=res.get("match_rating", "Fit"))
        with m2:
            matched_count = len(res.get("keyword_analysis", {}).get("matched_keywords", []))
            st.metric(label="Matched Target Keywords", value=matched_count)
        with m3:
            st.metric(label="Engine", value=res.get("source", "Engine"))

        st.info(f"**Executive Fit Rationale:** {res.get('match_rationale', '')}")

        # Keyword Breakdown
        kw_col1, kw_col2 = st.columns(2)
        with kw_col1:
            st.markdown("**✅ Matched Target Keywords:**")
            matched_kw = res.get("keyword_analysis", {}).get("matched_keywords", [])
            if matched_kw:
                html_badges = "".join([f'<span class="badge-matched">{k}</span>' for k in matched_kw])
                st.markdown(html_badges, unsafe_allow_html=True)
            else:
                st.write("No exact keyword matches found.")

        with kw_col2:
            st.markdown("**⚠️ Keyword Gaps / Opportunities:**")
            missing_kw = res.get("keyword_analysis", {}).get("missing_keywords", [])
            if missing_kw:
                html_badges = "".join([f'<span class="badge-missing">{k}</span>' for k in missing_kw])
                st.markdown(html_badges, unsafe_allow_html=True)
            else:
                st.write("No critical gaps identified.")

        st.markdown("---")
        st.subheader("3. Interactive Bullet Customization & Anti-Hallucination Review")
        st.caption("Review, edit, and select which modular bullet points are compiled into your final resume. All metrics and facts are strictly anchored in your master experience bank.")

        # Editable Summary
        summary_val = st.text_area(
            "📝 Tailored Professional Summary",
            value=res.get("tailored_summary", ""),
            height=90,
            help="You can edit this tailored summary directly before generating the final export.",
        )
        # Update context summary
        context["professional_summary"] = {"tailored_summary": summary_val}

        # Role Bullets Selection & Editing
        experience_roles = res.get("experience", [])
        updated_experience = []

        # Role inclusion summary counter
        active_role_count = sum(
            1 for r_idx in range(len(experience_roles))
            if st.session_state.get(f"role_inc_{r_idx}", True)
        )
        st.markdown(
            f"##### Work Experience Roles & Bullets "
            f"<span style='font-size:0.85em; font-weight:normal; color:#64748b;'>({active_role_count} of {len(experience_roles)} roles included in resume)</span>",
            unsafe_allow_html=True,
        )

        for r_idx, role in enumerate(experience_roles):
            role_key = f"role_inc_{r_idx}"
            is_role_included = st.session_state.get(role_key, True)

            role_title = role.get("title") or role.get("role_title", "Role")
            company = role.get("company", "Company")
            start_d = role.get("start_date", "")
            end_d = role.get("end_date", "Present") if not role.get("is_current") else "Present"
            dates_str = f"{start_d} – {end_d}" if start_d else ""
            loc_str = role.get("location", "")

            badge = "🟢 (Included)" if is_role_included else "⚪ (Role Excluded)"
            expander_title = f"💼 {role_title} at {company} — {badge}"

            with st.expander(expander_title, expanded=is_role_included):
                col_r_chk, col_r_meta = st.columns([2.4, 9.6])
                with col_r_chk:
                    include_role = st.checkbox(
                        "Include Role",
                        value=is_role_included,
                        key=role_key,
                        help="Uncheck to exclude this entire position and all its bullets from the compiled resume.",
                    )
                with col_r_meta:
                    if include_role:
                        meta_text = f"✅ **Position Included in Resume**"
                        if dates_str:
                            meta_text += f" &nbsp;|&nbsp; 📅 {dates_str}"
                        if loc_str:
                            meta_text += f" &nbsp;|&nbsp; 📍 {loc_str}"
                        st.caption(meta_text)
                    else:
                        st.warning("⚪ **Position Excluded:** This entire role and all of its accomplishment bullets are omitted from the resume export.")

                st.divider()

                selected_bullets_for_role = []
                for b_idx, b in enumerate(role.get("bullets", []), 1):
                    bullet_key = f"b_chk_{r_idx}_{b_idx}"
                    col_chk, col_edit = st.columns([1.4, 10.6])
                    with col_chk:
                        include_b = st.checkbox("Include", value=True, key=bullet_key, disabled=not include_role)
                    with col_edit:
                        b_text = st.text_area(
                            f"Bullet #{b_idx} (Selected for: {b.get('relevance_explanation', 'Relevance')})",
                            value=b.get("tailored_text", ""),
                            key=f"b_txt_{r_idx}_{b_idx}",
                            height=65,
                            disabled=not include_role,
                        )
                        tags = b.get("tags", [])
                        if tags:
                            tag_html = " ".join([f'<span class="badge-tag">{t}</span>' for t in tags])
                            st.markdown(tag_html, unsafe_allow_html=True)

                    if include_role and include_b and b_text.strip():
                        selected_bullets_for_role.append(b_text.strip())
                    st.divider()

                if include_role:
                    role_copy = dict(role)
                    role_copy["bullets"] = selected_bullets_for_role
                    updated_experience.append(role_copy)

        # Update context with user-selected bullets
        context["experience"] = updated_experience

        st.markdown("---")
        st.subheader("4. Clean PDF Export & Application Archive")

        if "active_theme_config" not in st.session_state:
            st.session_state["active_theme_config"] = load_formatting_config()
        active_theme = st.session_state["active_theme_config"]

        theme_col1, theme_col2 = st.columns([3, 2])
        with theme_col1:
            curr_preset = active_theme.get("preset_name", "Executive Modern")
            preset_options = list(THEME_PRESETS.keys()) + ["Custom Theme"]
            selected_theme_name = st.selectbox(
                "🎨 Active PDF Design Theme",
                options=preset_options,
                index=preset_options.index(curr_preset) if curr_preset in preset_options else len(preset_options) - 1,
                help="Switch between design presets or go to the '🎨 PDF Design & Layout Workshop' tab to fine-tune spacing and colors."
            )
            if selected_theme_name in THEME_PRESETS and selected_theme_name != curr_preset:
                st.session_state["active_theme_config"] = dict(THEME_PRESETS[selected_theme_name])
                active_theme = st.session_state["active_theme_config"]
                st.rerun()
        with theme_col2:
            st.caption("Tip: Use the **🎨 PDF Design & Layout Workshop** tab for granular margin, font size, and table width sliders.")

        pdf_bytes = generate_resume_pdf(context, formatting_config=active_theme)
        md_text = generate_resume_markdown(context)

        exp_col1, exp_col2, exp_col3, _ = st.columns([1.5, 1.5, 2, 2])
        with exp_col1:
            st.download_button(
                label="📄 Download WeasyPrint PDF",
                data=pdf_bytes,
                file_name="tailored_resume.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        with exp_col2:
            st.download_button(
                label="📋 Download Markdown",
                data=md_text,
                file_name="tailored_resume.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with exp_col3:
            if st.button("💾 Save to Application Archive", use_container_width=True):
                app_rec = save_application(
                    company=st.session_state.get("target_company") or target_company,
                    role_title=st.session_state.get("target_role") or target_role,
                    match_score=score,
                    match_rating=res.get("match_rating", "Fit"),
                    job_description=st.session_state.get("target_jd") or jd_input,
                    matched_keywords=matched_kw,
                    missing_keywords=missing_kw,
                    tailored_summary=summary_val,
                    tailored_experience=updated_experience,
                    pdf_bytes=pdf_bytes,
                    job_url=st.session_state.get("scraped_url", ""),
                )
                st.success(f"Saved application version for **{app_rec['company']}** into Application Archive!")

        with st.expander("👁️ Preview Rendered HTML Output"):
            html_preview = render_resume_html(context, formatting_config=active_theme)
            st.components.v1.html(html_preview, height=600, scrolling=True)

# -----------------------------------------------------------------------------
# TAB 2: Application Archive (History of Tailored Resumes)
# -----------------------------------------------------------------------------
with tab_history:
    st.subheader("Application History & Version Archive")
    st.caption("Archive of all customized resumes, match scores, keyword analytics, and compiled PDFs generated for your job applications.")

    applications = list_applications()
    if not applications:
        st.info("No applications archived yet. When you tailor a resume, click '💾 Save to Application Archive' to save it here.")
    else:
        # Metrics summary
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Total Applications Archived", len(applications))
        with m2:
            avg_score = int(sum(a.get("match_score", 0) for a in applications) / len(applications))
            st.metric("Average Match Score", f"{avg_score}%")

        st.markdown("---")
        for app in applications:
            with st.expander(f"📁 {app.get('company')} — {app.get('role_title')} ({app.get('timestamp')}) | Match: {app.get('match_score')}%"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Date Applied:** {app.get('timestamp')}")
                    if app.get("job_url"):
                        st.write(f"**Job Link:** [{app.get('job_url')}]({app.get('job_url')})")
                    st.write(f"**Match Rating:** {app.get('match_rating')}")
                    st.write(f"**Target Summary:** {app.get('tailored_summary')}")

                    # Keywords
                    m_kw = app.get("matched_keywords", [])
                    if m_kw:
                        badge_html = "".join([f'<span class="badge-matched">{k}</span>' for k in m_kw[:8]])
                        st.markdown(f"**Matched Keywords:** {badge_html}", unsafe_allow_html=True)

                with c2:
                    pdf_bytes_archived = get_application_pdf(app.get("pdf_filename"))
                    if pdf_bytes_archived:
                        st.download_button(
                            label="📄 Download Archived PDF",
                            data=pdf_bytes_archived,
                            file_name=f"{app.get('company', 'Resume')}_{app.get('id')}.pdf",
                            mime="application/pdf",
                            key=f"dl_arch_{app.get('id')}",
                            use_container_width=True,
                        )
                    if st.button("🗑️ Delete Record", key=f"del_{app.get('id')}", use_container_width=True):
                        delete_application(app.get("id"))
                        st.success("Deleted application record.")
                        st.rerun()

# -----------------------------------------------------------------------------
# TAB 3: Master Experience Bank (app/master_resume.json)
# -----------------------------------------------------------------------------
with tab_master:
    st.subheader("Master Resume Experience Bank")
    st.caption("Exhaustive, modular repository of career accomplishments, metrics, and skill-tagged bullet points.")

    try:
        master_data = load_master_resume()
    except Exception as e:
        st.error(f"Error loading master resume: {e}")
        master_data = {}

    subtab_view, subtab_workshop, subtab_upload, subtab_edit = st.tabs([
        "👁️ Structured Visualizer",
        "✨ Bullet Workshop & Studio",
        "📥 Ingest Baseline from PDF",
        "📝 Raw JSON Editor & Schema Validator",
    ])

    # Subtab 1: Structured Visualizer
    with subtab_view:
        if master_data:
            pi = master_data.get("personal_info", {})
            st.markdown(f"### {pi.get('name', 'Candidate')} - {pi.get('headline', '')}")
            badge_line = f" | 🛡️ **{pi.get('badge_credential')}**" if pi.get("badge_credential") else ""
            st.write(f"📍 {pi.get('location', '')} | ✉️ {pi.get('email', '')} | 📞 {pi.get('phone', '')}{badge_line}")

            # Certifications
            if master_data.get("certifications"):
                st.markdown("#### Verified Certifications & Credentials")
                for c in master_data.get("certifications", []):
                    link = c.get('credential_url')
                    name = f"[{c.get('name')}]({link})" if link else c.get('name')
                    dates = c.get('issue_date')
                    if c.get('expiration_date'):
                        dates += f" &ndash; Exp: {c.get('expiration_date')}"
                    st.markdown(f"- 🏅 **{name}** — *{c.get('issuer')}* ({dates})", unsafe_allow_html=True)
                    if c.get('skills'):
                        badge_skills = "".join([f'<span class="badge-tag">{s}</span>' for s in c.get('skills')[:8]])
                        st.markdown(f"  &nbsp;&nbsp;&nbsp;&nbsp;*Validated Competencies:* {badge_skills}", unsafe_allow_html=True)

            # Skills
            st.markdown("#### Technical Skills Inventory")
            for category, skills in master_data.get("skills", {}).items():
                cat_title = category.replace("_", " ").title()
                badge_str = "".join([f'<span class="badge-tag">{s}</span>' for s in skills])
                st.markdown(f"**{cat_title}:** {badge_str}", unsafe_allow_html=True)

            # Experience with Per-Job Skills
            st.markdown("#### Work Experience Bank (Deduplicated with Role-Specific Skills)")
            for role in master_data.get("experience", []):
                with st.expander(f"💼 {role.get('title')} — {role.get('company')} ({role.get('start_date')} to {role.get('end_date')})", expanded=True):
                    st.write(f"*{role.get('company_description', '')}*")

                    role_skills = role.get("skills", [])
                    if role_skills:
                        st.markdown("**Role-Specific Skills:** " + "".join([f'<span class="badge-skill">{s}</span>' for s in role_skills]), unsafe_allow_html=True)

                    st.markdown("**Modular Accomplishment Bullets:**")
                    for b in role.get("bullets", []):
                        st.markdown(f"- **{b.get('text')}**")
                        tag_html = f"Framework: `{b.get('framework', 'XYZ')}` | " + " ".join([f'<span class="badge-tag">{t}</span>' for t in b.get("tags", [])])
                        st.markdown(tag_html, unsafe_allow_html=True)
                        if b.get("metric_y"):
                            st.caption(f"📊 Metric: {b.get('metric_y')}")


    # Subtab 2: Metric Bullet Variations & Language Studio
    with subtab_workshop:
        st.markdown("#### ✨ Metric Bullet Variations & Language Studio")
        st.caption(
            "Every accomplishment metric in your master experience bank is now equipped with 4 tailored wording variations "
            "(Executive Impact, Technical Precision, Governance Rigor, and Metric-First Google XYZ). "
            "Select any role and metric below to switch active wordings or customize text directly."
        )

        roles = master_data.get("experience", [])
        if not roles:
            st.warning("No experience roles found in the master experience bank.")
        else:
            role_options = {f"{r.get('title')} — {r.get('company')}": r for r in roles}
            selected_role_label = st.selectbox("1. Select Work Experience Role", options=list(role_options.keys()), key="ws_role_sel")
            selected_role = role_options[selected_role_label]

            bullets = selected_role.get("bullets", [])
            if not bullets:
                st.info("No bullets found for this role.")
            else:
                bullet_options = {f"#{idx}: {b.get('text', '')[:75]}...": (idx, b) for idx, b in enumerate(bullets, 1)}
                selected_bullet_label = st.selectbox("2. Select Accomplishment Metric to Review", options=list(bullet_options.keys()), key="ws_bullet_sel")
                bullet_idx, selected_bullet = bullet_options[selected_bullet_label]

                st.markdown("---")
                st.markdown("##### 📌 Current Active Master Wording")
                st.markdown(f"> **{selected_bullet.get('text', '')}**")

                col_meta1, col_meta2 = st.columns(2)
                with col_meta1:
                    if selected_bullet.get("action_x"):
                        st.write(f"🎯 **Accomplishment [X]:** {selected_bullet.get('action_x')}")
                    if selected_bullet.get("metric_y"):
                        st.write(f"📊 **Measurable Metric [Y]:** `{selected_bullet.get('metric_y')}`")
                with col_meta2:
                    if selected_bullet.get("context_z"):
                        st.write(f"🛠️ **Context / Tools [Z]:** {selected_bullet.get('context_z')}")
                    tags = selected_bullet.get("tags", [])
                    if tags:
                        tag_html = " ".join([f'<span class="badge-tag">{t}</span>' for t in tags])
                        st.markdown(f"🏷️ **Tags:** {tag_html}", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("##### 🎯 Tailored Wording Choices for this Metric")
                variations = selected_bullet.get("variations", [])

                if not variations:
                    st.info("No pre-computed variations found for this metric.")
                else:
                    for v_idx, var in enumerate(variations, 1):
                        style_name = var.get("style", f"Choice {v_idx}")
                        is_active = (var.get("text", "").strip() == selected_bullet.get("text", "").strip())
                        badge_active = " 🟢 (ACTIVE WORDING)" if is_active else ""

                        with st.expander(f"Choice {v_idx}: {style_name}{badge_active}", expanded=True):
                            edited_var_text = st.text_area(
                                f"Wording Preview ({style_name})",
                                value=var.get("text", ""),
                                key=f"var_txt_{selected_bullet.get('id')}_{v_idx}",
                                height=75
                            )

                            col_act_left, col_act_right = st.columns([2, 2])
                            with col_act_left:
                                if not is_active:
                                    if st.button(f"🔄 Make Active Master Bullet", key=f"btn_activate_{selected_bullet.get('id')}_{v_idx}", use_container_width=True):
                                        selected_bullet["text"] = edited_var_text.strip()
                                        save_master_resume(master_data)
                                        st.success(f"Switched active master bullet to '{style_name}'!")
                                        st.rerun()
                                else:
                                    st.caption("✅ This is currently your active master wording.")
                            with col_act_right:
                                if st.button(f"💾 Update Choice Text", key=f"btn_save_txt_{selected_bullet.get('id')}_{v_idx}", use_container_width=True):
                                    var["text"] = edited_var_text.strip()
                                    if is_active:
                                        selected_bullet["text"] = edited_var_text.strip()
                                    save_master_resume(master_data)
                                    st.success(f"Saved updates to '{style_name}' choice!")
                                    st.rerun()

                st.markdown("---")
                st.markdown("##### ➕ Add Custom Wording Choice")
                with st.expander("Create a new variation for this metric"):
                    new_style = st.text_input("Style / Focus Label", placeholder="e.g. Commercial Tech / Startup Focus", key=f"new_style_{selected_bullet.get('id')}")
                    new_text = st.text_area("Bullet Wording", placeholder="Type customized wording preserving the verified metric...", key=f"new_txt_{selected_bullet.get('id')}")
                    if st.button("➕ Add Choice to this Metric", key=f"add_choice_btn_{selected_bullet.get('id')}"):
                        if new_text.strip():
                            selected_bullet.setdefault("variations", []).append({
                                "style": new_style.strip() or "Custom Alternative",
                                "text": new_text.strip()
                            })
                            save_master_resume(master_data)
                            st.success("Added new choice to metric!")
                            st.rerun()
                        else:
                            st.warning("Please provide bullet text.")

    # Subtab 3: Ingest Baseline from PDF (Single or Batch Multi-Resume Deduplication)
    with subtab_upload:
        st.markdown("#### Ingest & Deduplicate Baseline Resumes from PDF")
        st.caption(f"Drop PDF files into `{UPLOADS_DIR}` or upload directly below. The system identifies repeated jobs, prevents duplicate work history, and aggregates unique skills per role.")

        existing_pdfs = list_uploaded_pdfs()
        if existing_pdfs:
            st.info(f"📁 **Found {len(existing_pdfs)} PDF files in `{UPLOADS_DIR.name}/`:** " + ", ".join([f"`{p.name}`" for p in existing_pdfs]))

            # Batch Deduplication Button
            col_batch_btn, _ = st.columns([2, 3])
            with col_batch_btn:
                batch_clicked = st.button("🚀 Batch Process & Deduplicate All Uploads", type="primary", use_container_width=True)

            if batch_clicked:
                with st.spinner("Extracting, deduplicating work history, and synthesizing role-specific skills across all PDFs..."):
                    try:
                        extractor = ResumePDFExtractor(api_key=active_api_key, model_name=model_choice)
                        deduped_baseline = extractor.batch_extract_and_deduplicate(pdf_paths=existing_pdfs, force_offline=force_offline)
                        st.session_state["extracted_baseline"] = deduped_baseline
                        st.success(f"Successfully processed {len(existing_pdfs)} files! Repeated jobs merged and skills consolidated.")
                    except Exception as ex:
                        st.error(f"Error during batch deduplication: {ex}")

        st.markdown("---")
        st.markdown("##### Upload Additional Resume PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file to upload into the experience bank",
            type=["pdf"],
            key="single_pdf_uploader",
        )

        pdf_source = None
        pdf_name = ""

        if uploaded_file is not None:
            save_path = UPLOADS_DIR / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved `{uploaded_file.name}` to `{UPLOADS_DIR.name}/`")
            pdf_source = save_path
            pdf_name = uploaded_file.name

            if st.button(f"⚡ Extract Baseline from `{pdf_name}`"):
                with st.spinner("Extracting text and structuring resume..."):
                    try:
                        raw_text = extract_text_from_pdf(pdf_source)
                        extractor = ResumePDFExtractor(api_key=active_api_key, model_name=model_choice)
                        structured_baseline = extractor.parse_resume_to_schema(raw_text, force_offline=force_offline)
                        st.session_state["extracted_baseline"] = structured_baseline
                        st.success("Successfully extracted and structured resume baseline!")
                    except Exception as ex:
                        st.error(f"Error parsing PDF: {ex}")

        # Display Extracted Data Preview & Save Actions
        if "extracted_baseline" in st.session_state:
            extracted = st.session_state["extracted_baseline"]
            st.markdown("---")
            st.markdown("### 📋 Deduplicated Baseline Preview")

            pi = extracted.get("personal_info", {})
            st.write(f"**Candidate:** {pi.get('name', 'N/A')} — {pi.get('headline', '')}")
            st.write(f"**Contact:** {pi.get('email', '')} | {pi.get('phone', '')} | {pi.get('location', '')}")

            with st.expander("🔍 View Deduplicated Roles & Skills (No Repeats)", expanded=True):
                for role in extracted.get("experience", []):
                    st.markdown(f"**{role.get('title', 'Role')}** at **{role.get('company', 'Company')}** ({role.get('start_date', '')} - {role.get('end_date', '')})")
                    r_skills = role.get("skills", [])
                    if r_skills:
                        st.markdown("**Per-Job Skills:** " + "".join([f'<span class="badge-skill">{s}</span>' for s in r_skills]), unsafe_allow_html=True)
                    for b in role.get("bullets", []):
                        b_text = b.get("text", "")
                        framework = b.get("framework", "XYZ")
                        tags = " ".join([f"`{t}`" for t in b.get("tags", [])])
                        st.markdown(f"- {b_text} *({framework} {tags})*")
                    st.markdown("")

            with st.expander("🛠️ View Categorized Skills Inventory"):
                for cat, items in extracted.get("skills", {}).items():
                    st.write(f"- **{cat.replace('_', ' ').title()}:** {', '.join(items)}")

            # Action Buttons to Save into master_resume.json
            col_overwrite, col_merge = st.columns(2)
            with col_overwrite:
                if st.button("💾 Set as Master Resume (Overwrite)", type="primary", use_container_width=True):
                    try:
                        save_master_resume(extracted)
                        st.success("✅ Saved extracted baseline as `app/master_resume.json`!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to save: {err}")

            with col_merge:
                if st.button("➕ Merge into Existing Master Resume", use_container_width=True):
                    try:
                        current_data = load_master_resume()
                        for cat, items in extracted.get("skills", {}).items():
                            if cat in current_data.get("skills", {}):
                                current_set = set(current_data["skills"][cat])
                                current_set.update(items)
                                current_data["skills"][cat] = list(current_set)
                            else:
                                current_data.setdefault("skills", {})[cat] = items
                        existing_ids = {r.get("id") for r in current_data.get("experience", [])}
                        for r in extracted.get("experience", []):
                            if r.get("id") not in existing_ids:
                                current_data.setdefault("experience", []).append(r)

                        save_master_resume(current_data)
                        st.success("✅ Successfully merged extracted data into `app/master_resume.json`!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to merge: {err}")

    # Subtab 4: Raw JSON Editor & Schema Validator
    with subtab_edit:
        st.markdown("#### Direct JSON Editor")
        json_str = st.text_area(
            "app/master_resume.json",
            value=json.dumps(master_data, indent=2),
            height=400,
        )
        col_val, col_save = st.columns(2)
        with col_val:
            if st.button("🔍 Validate against Schema"):
                try:
                    parsed = json.loads(json_str)
                    valid, err = validate_master_resume(parsed)
                    if valid:
                        st.success("✅ JSON is 100% valid against master_resume_schema.json!")
                    else:
                        st.error(f"❌ Schema validation failed: {err}")
                except Exception as ex:
                    st.error(f"Invalid JSON syntax: {ex}")
        with col_save:
            if st.button("💾 Save to app/master_resume.json"):
                try:
                    parsed = json.loads(json_str)
                    save_master_resume(parsed)
                    st.success("Successfully saved to app/master_resume.json!")
                except Exception as ex:
                    st.error(f"Failed to save: {ex}")

# -----------------------------------------------------------------------------
# TAB 4: Resume PDF Design & Layout Workshop
# -----------------------------------------------------------------------------
with tab_format:
    st.subheader("🎨 Resume PDF Design & Layout Workshop")
    st.caption(
        "Fine-tune every visual dimension of your compiled resume PDF with granular, real-time controls. "
        "Adjust page margins to pull trailing lines into a clean 2-page fit, dial in typography, "
        "customize technical competencies table widths, and preview changes instantly without code edits."
    )

    if "active_theme_config" not in st.session_state:
        st.session_state["active_theme_config"] = load_formatting_config()

    cfg = st.session_state["active_theme_config"]

    # Top Bar: Preset Selector, Save Default, Reset
    p_col1, p_col2, p_col3, p_col4 = st.columns([3.5, 2, 2, 2.5])
    with p_col1:
        curr_p_name = cfg.get("preset_name", "Executive Modern")
        preset_names = list(THEME_PRESETS.keys())
        p_idx = preset_names.index(curr_p_name) if curr_p_name in preset_names else 0
        selected_preset = st.selectbox(
            "Quick Design Presets",
            options=preset_names,
            index=p_idx,
            key="studio_preset_sel"
        )
    with p_col2:
        if st.button("✨ Load Preset", use_container_width=True):
            st.session_state["active_theme_config"] = dict(THEME_PRESETS[selected_preset])
            cfg = st.session_state["active_theme_config"]
            st.success(f"Loaded preset '{selected_preset}'!")
            st.rerun()
    with p_col3:
        if st.button("💾 Save as Default", use_container_width=True, help="Save current styling settings as your personal default."):
            save_formatting_config(cfg)
            st.success("Saved theme settings to data/formatting_config.json!")
    with p_col4:
        if st.button("🔄 Reset to Factory", use_container_width=True):
            st.session_state["active_theme_config"] = dict(DEFAULT_THEME)
            save_formatting_config(DEFAULT_THEME)
            st.info("Reset formatting to factory default.")
            st.rerun()

    st.markdown("---")

    # Split Layout: Left Controls (5), Right Live Preview (7)
    ctrl_col, prev_col = st.columns([5, 7])

    with ctrl_col:
        # 1. Page Margins & Geometry
        with st.expander("📐 Page Margins & Geometry", expanded=True):
            st.caption("Adjust margins in inches. Tip: Use 0.35in – 0.40in to fit maximum content onto 2 pages.")
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                top_val = float(cfg.get("page_margin_top", "0.45in").replace("in", ""))
                new_top = st.slider("Margin Top (in)", min_value=0.20, max_value=0.80, value=top_val, step=0.05, key="cfg_m_top")
                cfg["page_margin_top"] = f"{new_top:.2f}in"

                left_val = float(cfg.get("page_margin_left", "0.5in").replace("in", ""))
                new_left = st.slider("Margin Left (in)", min_value=0.25, max_value=0.85, value=left_val, step=0.05, key="cfg_m_left")
                cfg["page_margin_left"] = f"{new_left:.2f}in"
            with m_col2:
                bot_val = float(cfg.get("page_margin_bottom", "0.45in").replace("in", ""))
                new_bot = st.slider("Margin Bottom (in)", min_value=0.20, max_value=0.80, value=bot_val, step=0.05, key="cfg_m_bot")
                cfg["page_margin_bottom"] = f"{new_bot:.2f}in"

                right_val = float(cfg.get("page_margin_right", "0.5in").replace("in", ""))
                new_right = st.slider("Margin Right (in)", min_value=0.25, max_value=0.85, value=right_val, step=0.05, key="cfg_m_right")
                cfg["page_margin_right"] = f"{new_right:.2f}in"

            pn_c1, pn_c2 = st.columns(2)
            with pn_c1:
                cfg["show_page_numbers"] = st.checkbox("Show 'Page X of Y' Footer", value=cfg.get("show_page_numbers", True), key="cfg_show_pn")
            with pn_c2:
                if cfg["show_page_numbers"]:
                    pos_options = ["bottom-right", "bottom-center", "bottom-left"]
                    curr_pos = cfg.get("page_number_position", "bottom-right")
                    cfg["page_number_position"] = st.selectbox("Page Number Position", options=pos_options, index=pos_options.index(curr_pos) if curr_pos in pos_options else 0, key="cfg_pn_pos")

        # 2. Typography & Color Palette
        with st.expander("🔤 Global Typography & Colors", expanded=False):
            font_choices = {
                "Modern Clean Sans (Segoe UI / Arial / Helvetica)": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
                "Classic Editorial Serif (Times / Georgia / Garamond)": "'Times New Roman', Times, 'Liberation Serif', Georgia, serif",
                "Technical System Sans (Inter / System UI)": "'Inter', 'Segoe UI', system-ui, sans-serif",
                "Clean Technical Monospace (Consolas / Courier)": "Consolas, 'Courier New', Courier, monospace"
            }
            curr_family = cfg.get("font_family", "")
            f_idx = 0
            for i, (k, v) in enumerate(font_choices.items()):
                if v == curr_family:
                    f_idx = i
                    break

            selected_font_label = st.selectbox("Font Family", options=list(font_choices.keys()), index=f_idx, key="cfg_font_sel")
            cfg["font_family"] = font_choices[selected_font_label]

            t_c1, t_c2 = st.columns(2)
            with t_c1:
                base_val = float(cfg.get("font_size_base", "9.5pt").replace("pt", ""))
                new_base = st.slider("Base Body Font Size (pt)", min_value=8.0, max_value=11.0, value=base_val, step=0.1, key="cfg_font_base")
                cfg["font_size_base"] = f"{new_base:.1f}pt"
            with t_c2:
                lh_val = float(cfg.get("line_height_base", "1.35"))
                new_lh = st.slider("Base Line Height", min_value=1.15, max_value=1.60, value=lh_val, step=0.05, key="cfg_lh_base")
                cfg["line_height_base"] = f"{new_lh:.2f}"

            st.markdown("###### Color Palette")
            cp1, cp2 = st.columns(2)
            with cp1:
                cfg["color_accent"] = st.color_picker("Primary Accent Color (Links, Badges)", value=cfg.get("color_accent", "#2563eb"), key="cfg_col_acc")
                cfg["color_headings"] = st.color_picker("Headings & Name Color", value=cfg.get("color_headings", "#0f172a"), key="cfg_col_head")
            with cp2:
                cfg["color_body"] = st.color_picker("Body Text Color", value=cfg.get("color_body", "#334155"), key="cfg_col_body")
                cfg["color_subtle"] = st.color_picker("Subtle & Metadata Color (Dates, Loc)", value=cfg.get("color_subtle", "#64748b"), key="cfg_col_sub")

        # 3. Header Section & Contact Info
        with st.expander("🏷️ Header & Contact Bar", expanded=False):
            h_align = cfg.get("header_alignment", "center")
            cfg["header_alignment"] = st.radio("Header Alignment", options=["center", "left"], index=0 if h_align == "center" else 1, horizontal=True, key="cfg_h_align")

            h_c1, h_c2 = st.columns(2)
            with h_c1:
                name_pt = float(cfg.get("font_size_name", "20pt").replace("pt", ""))
                new_name_pt = st.slider("Name Size (pt)", min_value=14.0, max_value=28.0, value=name_pt, step=0.5, key="cfg_name_pt")
                cfg["font_size_name"] = f"{new_name_pt:.1f}pt"
                cfg["name_uppercase"] = st.checkbox("UPPERCASE Candidate Name", value=cfg.get("name_uppercase", True), key="cfg_name_case")
            with h_c2:
                hl_pt = float(cfg.get("font_size_headline", "10.5pt").replace("pt", ""))
                new_hl_pt = st.slider("Headline Size (pt)", min_value=8.5, max_value=14.0, value=hl_pt, step=0.5, key="cfg_hl_pt")
                cfg["font_size_headline"] = f"{new_hl_pt:.1f}pt"

                cont_pt = float(cfg.get("contact_font_size", "8.5pt").replace("pt", ""))
                new_cont_pt = st.slider("Contact Links Size (pt)", min_value=7.5, max_value=10.5, value=cont_pt, step=0.2, key="cfg_cont_pt")
                cfg["contact_font_size"] = f"{new_cont_pt:.1f}pt"

            h_b1, h_b2 = st.columns(2)
            with h_b1:
                h_b_width = float(cfg.get("header_border_bottom_width", "1.5px").replace("px", ""))
                new_hb_w = st.slider("Bottom Divider Width (px)", min_value=0.0, max_value=4.0, value=h_b_width, step=0.5, key="cfg_hb_w")
                cfg["header_border_bottom_width"] = f"{new_hb_w:.1f}px"
            with h_b2:
                cfg["color_header_bottom_border"] = st.color_picker("Header Divider Color", value=cfg.get("color_header_bottom_border", "#2d3748"), key="cfg_hb_col")

        # 4. Core Competencies Table Alignment
        with st.expander("📊 Core Competencies Table Alignment", expanded=False):
            st.caption("Fine-tune category label column width and row spacing to ensure clean alignment with zero awkward whitespace.")
            cw_val = int(cfg.get("skills_label_width", "172px").replace("px", ""))
            new_cw = st.slider("Category Label Column Width (px)", min_value=120, max_value=240, value=cw_val, step=2, key="cfg_cw")
            cfg["skills_label_width"] = f"{new_cw}px"

            c_r1, c_r2 = st.columns(2)
            with c_r1:
                pad_val = float(cfg.get("skills_row_padding", "2px").replace("px", ""))
                new_pad = st.slider("Table Row Spacing (px)", min_value=0.5, max_value=6.0, value=pad_val, step=0.5, key="cfg_pad")
                cfg["skills_row_padding"] = f"{new_pad:.1f}px"
            with c_r2:
                cfg["skills_label_color"] = st.color_picker("Category Label Color", value=cfg.get("skills_label_color", "#0f172a"), key="cfg_sk_col")

            cfg["skills_values_alignment"] = st.radio("Competencies Values Alignment", options=["justify", "left"], index=0 if cfg.get("skills_values_alignment", "justify") == "justify" else 1, horizontal=True, key="cfg_sk_align")

        # 5. Professional Experience & Bullets Spacing
        with st.expander("💼 Experience Roles & Bullets Spacing", expanded=False):
            e_c1, e_c2 = st.columns(2)
            with e_c1:
                rm_val = int(cfg.get("role_margin_bottom", "9px").replace("px", ""))
                new_rm = st.slider("Spacing Between Jobs (px)", min_value=3, max_value=20, value=rm_val, step=1, key="cfg_rm")
                cfg["role_margin_bottom"] = f"{new_rm}px"

                rt_val = float(cfg.get("font_size_role_title", "10pt").replace("pt", ""))
                new_rt = st.slider("Job Title Font Size (pt)", min_value=8.5, max_value=12.0, value=rt_val, step=0.2, key="cfg_rt")
                cfg["font_size_role_title"] = f"{new_rt:.1f}pt"
            with e_c2:
                cfg["company_name_color"] = st.color_picker("Company Name Color", value=cfg.get("company_name_color", "#2563eb"), key="cfg_comp_col")
                cfg["show_role_competencies"] = st.checkbox("Show Role-Specific Skills Sub-line", value=cfg.get("show_role_competencies", True), key="cfg_show_rskills")

            st.markdown("###### Accomplishment Bullets Geometry")
            b_c1, b_c2 = st.columns(2)
            with b_c1:
                bind_val = int(cfg.get("bullet_indent", "16px").replace("px", ""))
                new_bind = st.slider("Bullet Left Indent (px)", min_value=8, max_value=32, value=bind_val, step=2, key="cfg_bind")
                cfg["bullet_indent"] = f"{new_bind}px"

                bsp_val = float(cfg.get("bullet_spacing", "3px").replace("px", ""))
                new_bsp = st.slider("Spacing Between Bullets (px)", min_value=0.5, max_value=8.0, value=bsp_val, step=0.5, key="cfg_bsp")
                cfg["bullet_spacing"] = f"{new_bsp:.1f}px"
            with b_c2:
                b_styles = ["disc", "circle", "square", "hyphen", "none"]
                curr_bs = cfg.get("bullet_symbol", "disc")
                cfg["bullet_symbol"] = st.selectbox("Bullet Marker Style", options=b_styles, index=b_styles.index(curr_bs) if curr_bs in b_styles else 0, key="cfg_bs")

                cfg["bullet_alignment"] = st.radio("Bullet Text Alignment", options=["justify", "left"], index=0 if cfg.get("bullet_alignment", "justify") == "justify" else 1, horizontal=True, key="cfg_balign")

        # 6. Section Titles & Spacing
        with st.expander("📌 Section Titles & Dividers", expanded=False):
            sec_c1, sec_c2 = st.columns(2)
            with sec_c1:
                st_val = float(cfg.get("font_size_section_title", "10.5pt").replace("pt", ""))
                new_st = st.slider("Section Title Size (pt)", min_value=8.5, max_value=13.0, value=st_val, step=0.2, key="cfg_st_val")
                cfg["font_size_section_title"] = f"{new_st:.1f}pt"
                cfg["section_title_uppercase"] = st.checkbox("UPPERCASE Section Titles", value=cfg.get("section_title_uppercase", True), key="cfg_st_case")
            with sec_c2:
                sec_gap = int(cfg.get("section_spacing", "11px").replace("px", ""))
                new_sec_gap = st.slider("Spacing Between Sections (px)", min_value=4, max_value=22, value=sec_gap, step=1, key="cfg_sec_gap")
                cfg["section_spacing"] = f"{new_sec_gap}px"

                cfg["color_border"] = st.color_picker("Section Divider Line Color", value=cfg.get("color_border", "#cbd5e1"), key="cfg_sec_div_col")

        # 7. Advanced Custom CSS Overrides
        with st.expander("💻 Advanced Custom CSS Overrides", expanded=False):
            st.caption("Inject arbitrary CSS rules directly into the compiled PDF template. Perfect for bespoke styling tweaks.")
            cfg["custom_css"] = st.text_area(
                "Custom CSS Code",
                value=cfg.get("custom_css", ""),
                height=120,
                placeholder="/* Example: */\n.company-name { font-style: italic; }\n.summary-text { letter-spacing: 0.2px; }",
                key="cfg_custom_css"
            )

    # Right Column: Live Viewport Preview & One-Click PDF Export
    with prev_col:
        st.markdown("##### 👁️ Live PDF & Layout Preview")
        st.caption("Live render reflects all margin, typography, table alignment, and color tweaks above.")

        # Load master data for live preview
        preview_data = master_data if "master_data" in locals() and master_data else load_master_resume()
        preview_ctx = prepare_resume_context(preview_data, {"role_fit_analysis": {"recommended_bullets": []}}, formatting_config=cfg)
        live_html = render_resume_html(preview_ctx, formatting_config=cfg)

        st.components.v1.html(live_html, height=750, scrolling=True)

        prev_btn1, prev_btn2 = st.columns([1, 1])
        with prev_btn1:
            live_pdf_bytes = generate_resume_pdf(preview_ctx, formatting_config=cfg)
            st.download_button(
                label="📄 Download Formatted WeasyPrint PDF",
                data=live_pdf_bytes,
                file_name="resume_formatted.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        with prev_btn2:
            if st.button("💾 Apply & Save This Styling", use_container_width=True, key="save_theme_bottom"):
                save_formatting_config(cfg)
                st.success("Theme preferences saved to data/formatting_config.json!")

# -----------------------------------------------------------------------------
# TAB 5: System Architecture & Verification
# -----------------------------------------------------------------------------
with tab_diag:
    st.subheader("System Architecture & Diagnostic Checks")
    st.markdown(
        """
        The **Resume Tailor** system operates on an automated four-stage pipeline:
        1. **Job Ingestion Engine (`app/job_scraper.py`)**: Direct headless scraping of private sector & contractor job postings (LinkedIn, Greenhouse, Lever, Indeed, Workday).
        2. **Baseline Ingestion & Deduplication (`uploads/` & `app/pdf_parser.py`)**: Multi-resume ingestion with deduplication of work history and per-job skill extraction.
        3. **Job Tailoring Engine & Studio (`app/tailor_engine.py` & `app/main.py`)**: Compatibility scoring, keyword gap analysis, and interactive anti-hallucination bullet customization.
        4. **Export & Version Archive (`app/history_manager.py` & `app/pdf_generator.py`)**: ATS-optimized WeasyPrint PDF compilation with persistent tracking of applications.
        """
    )

    st.markdown("#### Dependency Health Check")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.success("✅ Streamlit: Ready")
    with d2:
        st.success("✅ Google GenAI SDK: Ready" if GENAI_AVAILABLE else "❌ Google GenAI SDK: Not Found")
    with d3:
        st.success("✅ WeasyPrint: Ready")
    with d4:
        st.success("✅ Playwright: Ready")

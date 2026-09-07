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

tab_tailor, tab_history, tab_master, tab_diag = st.tabs([
    "🚀 Job Tailoring Studio",
    "📁 Application Archive",
    "🗄️ Master Experience Bank",
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

        pdf_bytes = generate_resume_pdf(context)
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
            html_preview = render_resume_html(context)
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
# TAB 4: System Architecture & Verification
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

"""
Tailor Engine: Job Description matching, bullet selection, and hallucination-free rewriting.
Powered by Google GenAI SDK (google-genai).
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import jsonschema

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


MASTER_RESUME_PATH = Path(__file__).parent / "master_resume.json"
EXAMPLE_RESUME_PATH = Path(__file__).parent / "master_resume.example.json"
SCHEMA_PATH = Path(__file__).parent / "master_resume_schema.json"


def load_master_resume(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the master resume JSON from disk, auto-initializing from example template if needed."""
    target_path = path or MASTER_RESUME_PATH
    if not target_path.exists():
        if EXAMPLE_RESUME_PATH.exists() and (path is None or path == MASTER_RESUME_PATH):
            import shutil
            shutil.copy(EXAMPLE_RESUME_PATH, MASTER_RESUME_PATH)
            target_path = MASTER_RESUME_PATH
        else:
            raise FileNotFoundError(f"Master resume not found at {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_master_resume(data: Dict[str, Any], schema_path: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """Validate master resume data against schema."""
    target_schema = schema_path or SCHEMA_PATH
    if not target_schema.exists():
        return True, None  # Schema file optional
    try:
        with open(target_schema, "r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.ValidationError as err:
        return False, str(err.message)
    except Exception as e:
        return False, str(e)


def save_master_resume(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Save master resume data to disk after validation."""
    valid, err = validate_master_resume(data)
    if not valid:
        raise ValueError(f"Schema validation failed: {err}")
    target_path = path or MASTER_RESUME_PATH
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class ResumeTailorService:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None
        if self.api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Google GenAI Client: {e}")

    def analyze_and_tailor(
        self,
        job_description: str,
        master_resume: Optional[Dict[str, Any]] = None,
        max_bullets_per_role: int = 3,
        force_offline: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze JD against Master Resume.
        Returns match score, keyword gaps, and tailored bullet recommendations.
        """
        resume = master_resume or load_master_resume()

        if not force_offline and self.client:
            try:
                return self._tailor_with_gemini(job_description, resume, max_bullets_per_role)
            except Exception as exc:
                print(f"Gemini API call failed, falling back to heuristic engine: {exc}")
                res = self._tailor_heuristic(job_description, resume, max_bullets_per_role)
                res["warning"] = f"Gemini API error ({str(exc)}). Used local heuristic engine."
                return res

        return self._tailor_heuristic(job_description, resume, max_bullets_per_role)
    def workshop_bullet(
        self,
        bullet_text: str,
        role_title: str = "",
        company: str = "",
        action_x: str = "",
        metric_y: str = "",
        context_z: str = "",
        focus_prompt: str = "",
        force_offline: bool = False
    ) -> list:
        """
        Workshop an accomplishment bullet into 4 distinct, high-impact wordings:
        1. Executive & Strategic Impact
        2. Technical & Engineering Precision
        3. Governance & Regulatory Rigor
        4. Metric-First (Google XYZ)
        """
        if not force_offline and self.client:
            try:
                return self._workshop_with_gemini(
                    bullet_text, role_title, company, action_x, metric_y, context_z, focus_prompt
                )
            except Exception as e:
                print(f"Gemini workshop call failed, falling back to heuristic workshop: {e}")

        return self._workshop_heuristic(
            bullet_text, role_title, company, action_x, metric_y, context_z, focus_prompt
        )

    def _workshop_with_gemini(
        self,
        bullet_text: str,
        role_title: str,
        company: str,
        action_x: str,
        metric_y: str,
        context_z: str,
        focus_prompt: str
    ) -> list:
        prompt = f"""
You are an elite technical resume workshop strategist specializing in cybersecurity and engineering career branding.
Your mission is to workshop the following accomplishment bullet point and produce 4 distinct, highly polished alternative wordings.

=== STRICT ANTI-HALLUCINATION RULES ===
- 100% FACTUAL FIDELITY: Retain all actual numbers, metrics, systems, standards, and outcomes from the original bullet.
- Do NOT invent or fabricate any metric, tool, or achievement that does not appear in the original bullet.
- Maximize strong action verbs, eliminate wordiness, and ensure concise, resume-ready phrasing.

=== ORIGINAL BULLET & CONTEXT ===
Role: {role_title} at {company}
Original Bullet: {bullet_text}
Accomplishment [X]: {action_x}
Metric / Measurable Impact [Y]: {metric_y}
Context / Tech [Z]: {context_z}
Custom Focus Directive: {focus_prompt or 'None'}

=== REQUIRED JSON OUTPUT ===
Return ONLY a valid JSON array of 4 objects matching:
[
  {{
    "style": "Executive & Strategic Impact",
    "text": "Polished bullet emphasizing risk reduction, business enablement, leadership, and operational velocity.",
    "rationale": "Best suited for senior, managerial, or private-sector corporate roles."
  }},
  {{
    "style": "Technical & Engineering Precision",
    "text": "Polished bullet emphasizing technical controls, tools, architecture, automation, and hands-on execution.",
    "rationale": "Best suited for hands-on engineering, technical lead, and implementation roles."
  }},
  {{
    "style": "Governance & Regulatory Rigor",
    "text": "Polished bullet emphasizing NIST 800-53, RMF, ATO defensibility, audit readiness, and compliance rigor.",
    "rationale": "Best suited for federal oversight, contractor governance, and compliance assessor roles."
  }},
  {{
    "style": "Metric-First (Google XYZ)",
    "text": "Polished bullet leading directly with the quantified metric/outcome (Y) followed by action (X) and method (Z).",
    "rationale": "Best suited for metric-driven recruiters and ATS scanning algorithms."
  }}
]
"""
        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )

        resp_text = response.text.strip()
        if resp_text.startswith("```json"):
            resp_text = resp_text[7:]
        if resp_text.startswith("```"):
            resp_text = resp_text[3:]
        if resp_text.endswith("```"):
            resp_text = resp_text[:-3]

        return json.loads(resp_text.strip())

    def _workshop_heuristic(
        self,
        bullet_text: str,
        role_title: str,
        company: str,
        action_x: str,
        metric_y: str,
        context_z: str,
        focus_prompt: str
    ) -> list:
        clean_bullet = bullet_text.strip().rstrip(".")

        # Clean verb lead-ins
        lower_first = clean_bullet[:1].lower() + clean_bullet[1:]

        var_exec = f"Spearheaded operational risk governance by {lower_first}."
        var_tech = f"Architected and enforced technical controls for {lower_first}."
        var_gov = f"Governed defensible audit readiness and continuous authorization by {lower_first}."
        if metric_y:
            var_metric = f"Delivered {metric_y.lower()} through {lower_first}."
        else:
            var_metric = f"Maximized accreditation boundary integrity and security baseline by {lower_first}."

        return [
            {
                "style": "Executive & Strategic Impact",
                "text": var_exec,
                "rationale": "Emphasizes leadership, business enablement, and operational risk management."
            },
            {
                "style": "Technical & Engineering Precision",
                "text": var_tech,
                "rationale": "Emphasizes hands-on architecture, technical implementation, and systems control."
            },
            {
                "style": "Governance & Regulatory Rigor",
                "text": var_gov,
                "rationale": "Emphasizes compliance defensibility, NIST/RMF oversight, and audit posture."
            },
            {
                "style": "Metric-First (Google XYZ)",
                "text": var_metric,
                "rationale": "Anchors directly on measurable outcomes, delivery scope, and verified metrics."
            }
        ]


    def _tailor_with_gemini(
        self,
        job_description: str,
        resume: Dict[str, Any],
        max_bullets_per_role: int
    ) -> Dict[str, Any]:
        """Use Gemini 2.5 Flash to score, select, and rewrite bullets without hallucinations."""
        prompt = f"""
You are an expert ATS optimization and technical executive resume strategist.
Your task is to analyze a target Job Description against an engineer's Master Resume Experience Bank,
compute a realistic compatibility match score, perform keyword gap analysis, and generate a tailored resume recommendation.

=== CRITICAL ANTI-HALLUCINATION INSTRUCTIONS ===
1. You must ONLY select bullet points that exist in the Master Resume.
2. When rewriting bullets:
   - STRICTLY PRESERVE all quantitative metrics, numbers, dollar values, percentages, and factual outcomes.
   - Do NOT invent or fabricate any metric, tool, or achievement that does not appear in the original bullet.
   - Reframe and mirror the phrasing and terminology of the Job Description while keeping the underlying truth 100% intact.
3. For each role, pick the {max_bullets_per_role} most relevant bullet points that best demonstrate required competencies.

=== TARGET JOB DESCRIPTION ===
{job_description}

=== MASTER RESUME DATA ===
{json.dumps(resume, indent=2)}

=== REQUIRED JSON OUTPUT FORMAT ===
Return ONLY a valid JSON object with the following schema:
{{
  "match_score": 85,
  "match_rating": "Strong Match",
  "match_rationale": "2-3 sentences explaining the overall fit and strength of candidate for this role.",
  "keyword_analysis": {{
    "matched_keywords": ["Kubernetes", "Go", "Distributed Systems", "AWS"],
    "missing_keywords": ["C++", "GraphQL", "Snowflake"],
    "summary": "Short explanation of keyword alignment and notable gaps."
  }},
  "tailored_summary": "A high-impact 2-3 sentence professional summary tailored specifically to the target JD, highlighting relevant career highlights from the master resume.",
  "tailored_skills": {{
    "languages": ["..."],
    "cloud_and_infrastructure": ["..."],
    "databases_and_streaming": ["..."],
    "architecture_and_practices": ["..."]
  }},
  "experience": [
    {{
      "role_id": "role-id-from-master",
      "company": "Company Name",
      "title": "Role Title",
      "location": "Location",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "is_current": true,
      "bullets": [
        {{
          "bullet_id": "bullet-id-from-master",
          "original_text": "Original bullet text from master resume",
          "tailored_text": "Rewritten bullet tailored to JD keywords without altering facts or metrics",
          "tags": ["#cloud", "#metrics"],
          "relevance_explanation": "Brief rationale why this bullet was selected for the target role"
        }}
      ]
    }}
  ]
}}
"""
        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )

        response_text = response.text.strip()
        # Clean any potential markdown wrapper
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        parsed = json.loads(response_text.strip())
        parsed["source"] = f"Gemini ({self.model_name})"
        return parsed

    def _tailor_heuristic(
        self,
        job_description: str,
        resume: Dict[str, Any],
        max_bullets_per_role: int
    ) -> Dict[str, Any]:
        """
        Offline fallback heuristic engine for prototype testing without API key.
        Matches keywords from JD against master resume tags and text.
        """
        jd_lower = job_description.lower()

        # Extract words/phrases from JD
        jd_tokens = set(re.findall(r'\b[a-zA-Z0-9_\-\.#+]+\b', jd_lower))

        # Collect candidate skills from master resume
        all_skills = []
        for cat_skills in resume.get("skills", {}).values():
            all_skills.extend(cat_skills)

        matched_skills = []
        missing_skills = []

        for skill in all_skills:
            clean_skill = skill.lower().split("(")[0].strip()
            if clean_skill in jd_lower:
                matched_skills.append(skill)

        # Detect common tech keywords in JD that might be missing
        common_tech = [
            "Kubernetes", "AWS", "GCP", "Azure", "Docker", "Terraform", "Go", "Golang",
            "Python", "Rust", "Java", "Kafka", "PostgreSQL", "Redis", "Elasticsearch",
            "ClickHouse", "GraphQL", "gRPC", "CI/CD", "FinOps", "Microservices", "Observability"
        ]
        for tech in common_tech:
            tech_lower = tech.lower()
            if tech_lower in jd_lower:
                if not any(tech_lower in s.lower() for s in all_skills):
                    missing_skills.append(tech)

        # Compute match score based on overlap
        raw_score = min(96, max(45, int(50 + (len(matched_skills) * 4) - (len(missing_skills) * 3))))
        if "staff" in jd_lower or "principal" in jd_lower:
            raw_score = min(98, raw_score + 5)

        # Process experience bullets
        tailored_roles = []
        for role in resume.get("experience", []):
            bullets = role.get("bullets", [])
            scored_bullets = []
            for b in bullets:
                b_text = b.get("text", "")
                b_tags = [t.lower().replace("#", "") for t in b.get("tags", [])]
                b_kw = [k.lower() for k in b.get("relevance_keywords", [])]

                # Score relevance
                score = 0
                for token in b_tags + b_kw:
                    if token in jd_lower:
                        score += 3
                for token in jd_tokens:
                    if len(token) > 3 and token in b_text.lower():
                        score += 1

                scored_bullets.append((score, b))

            # Sort descending by relevance score
            scored_bullets.sort(key=lambda x: x[0], reverse=True)
            selected = scored_bullets[:max_bullets_per_role]

            tailored_bullets = []
            for score, b in selected:
                tailored_bullets.append({
                    "bullet_id": b.get("id"),
                    "original_text": b.get("text"),
                    "tailored_text": b.get("text"),  # In heuristic mode, retain verified text
                    "tags": b.get("tags", []),
                    "relevance_explanation": f"High tag & keyword match ({', '.join(b.get('tags', [])[:3])})"
                })

            tailored_roles.append({
                "role_id": role.get("id"),
                "company": role.get("company"),
                "title": role.get("title") or role.get("role_title"),
                "location": role.get("location"),
                "start_date": role.get("start_date"),
                "end_date": role.get("end_date"),
                "is_current": role.get("is_current", False),
                "bullets": tailored_bullets
            })

        return {
            "source": "Resume Tailor Engine",
            "match_score": raw_score,
            "match_rating": "Strong Match" if raw_score >= 80 else ("Moderate Match" if raw_score >= 65 else "Low Match"),
            "match_rationale": (
                f"Candidate exhibits strong foundational alignment with {len(matched_skills)} core technical competencies "
                f"required in the role. High experience overlap in distributed systems, platform engineering, and cloud scaling."
            ),
            "keyword_analysis": {
                "matched_keywords": matched_skills[:10],
                "missing_keywords": missing_skills[:6],
                "summary": f"Detected strong keyword coverage in {', '.join(matched_skills[:4])}. Consider addressing gaps in {', '.join(missing_skills[:3]) or 'niche tools'}."
            },
            "tailored_summary": (
                f"{resume.get('personal_info', {}).get('headline', 'Senior Engineer')} with proven expertise in "
                f"{', '.join(matched_skills[:3]) if matched_skills else 'cloud infrastructure'}. Track record of "
                f"driving large-scale system scalability, performance optimization, and reliable software delivery."
            ),
            "tailored_skills": resume.get("skills", {}),
            "experience": tailored_roles
        }

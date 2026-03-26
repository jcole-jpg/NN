from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env.local"
load_dotenv(ENV_PATH)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))
RUNTIME_STATUS: Dict[str, Dict[str, str]] = {}


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from .env.local.")
    return OpenAI(api_key=api_key)


def _set_status(operation: str, mode: str, detail: str = "") -> None:
    RUNTIME_STATUS[operation] = {"mode": mode, "detail": detail}


def get_runtime_status() -> Dict[str, Dict[str, str]]:
    return dict(RUNTIME_STATUS)


def _chat_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        timeout=OPENAI_TIMEOUT_SECONDS,
    )

    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return parts[0].strip() if parts and parts[0].strip() else text.strip()


def _normalise_experience(items: Any) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []

    normalised = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalised.append(
            {
                "title": str(item.get("title", "")).strip(),
                "company": str(item.get("company", "")).strip(),
                "dates": str(item.get("dates", "")).strip(),
                "bullets": _string_list(item.get("bullets", [])),
            }
        )
    return normalised


def _normalise_education(items: Any) -> List[Dict[str, str]]:
    if not isinstance(items, list):
        return []

    normalised = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalised.append(
            {
                "degree": str(item.get("degree", "")).strip(),
                "school": str(item.get("school", "")).strip(),
                "year": str(item.get("year", "")).strip(),
            }
        )
    return normalised


def _normalise_jobs(items: Any) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []

    jobs = []
    for item in items:
        if not isinstance(item, dict):
            continue
        fit_score = item.get("fit_score", 0)
        try:
            fit_score_value = max(0, min(100, int(fit_score)))
        except (TypeError, ValueError):
            fit_score_value = 0

        jobs.append(
            {
                "title": str(item.get("title", "")).strip(),
                "company": str(item.get("company", "")).strip(),
                "location": str(item.get("location", "")).strip(),
                "salary_range": str(item.get("salary_range", "")).strip(),
                "required_skills": _string_list(item.get("required_skills", [])),
                "description": str(item.get("description", "")).strip(),
                "fit_score": fit_score_value,
                "fit_reason": str(item.get("fit_reason", "")).strip(),
            }
        )

    return sorted(jobs, key=lambda job: job["fit_score"], reverse=True)


def _fallback_parse_cv(text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lowered = text.lower()

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone_match = re.search(r"(\+?\d[\d\s().-]{7,}\d)", text)

    name = ""
    for line in lines[:5]:
        if "@" not in line and len(line.split()) <= 5 and re.search(r"[A-Za-z]", line):
            name = line
            break

    common_skills = [
        "python",
        "javascript",
        "typescript",
        "react",
        "next.js",
        "nextjs",
        "node.js",
        "node",
        "fastapi",
        "streamlit",
        "sql",
        "postgresql",
        "mysql",
        "machine learning",
        "data analysis",
        "excel",
        "tableau",
        "power bi",
        "figma",
        "product design",
        "ui design",
        "ux research",
        "aws",
        "docker",
        "git",
        "communication",
        "leadership",
        "project management",
        "openai",
    ]
    detected_skills = []
    for skill in common_skills:
        if skill in lowered:
            detected_skills.append(skill.replace("nextjs", "next.js"))

    summary = ""
    summary_match = re.search(
        r"(summary|profile|about)\s*[:\n]+(.+?)(?:\n[A-Z][A-Za-z /&]+:|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if summary_match:
        summary = " ".join(part.strip() for part in summary_match.group(2).splitlines() if part.strip())
    elif len(lines) > 3:
        summary = " ".join(lines[1:4])

    experience_items: List[Dict[str, Any]] = []
    experience_section = re.search(
        r"(experience|work history|professional experience)\s*[:\n]+(.+?)(?:\n(?:education|skills|projects|certifications)\b|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if experience_section:
        section_lines = [line.strip(" -\t") for line in experience_section.group(2).splitlines() if line.strip()]
        title = section_lines[0] if section_lines else "Recent Role"
        company = section_lines[1] if len(section_lines) > 1 else ""
        bullets = [line for line in section_lines[2:6] if len(line.split()) > 3]
        experience_items.append(
            {
                "title": title,
                "company": company,
                "dates": "",
                "bullets": bullets or [summary or "Delivered work across cross-functional projects."],
            }
        )

    education_items: List[Dict[str, str]] = []
    education_section = re.search(
        r"(education)\s*[:\n]+(.+?)(?:\n(?:experience|skills|projects|certifications)\b|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if education_section:
        section_lines = [line.strip(" -\t") for line in education_section.group(2).splitlines() if line.strip()]
        if section_lines:
            education_items.append(
                {
                    "degree": section_lines[0],
                    "school": section_lines[1] if len(section_lines) > 1 else "",
                    "year": section_lines[2] if len(section_lines) > 2 else "",
                }
            )

    return {
        "name": name,
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
        "summary": summary,
        "skills": list(dict.fromkeys(detected_skills)),
        "experience": experience_items,
        "education": education_items,
    }


def _fit_score(profile: Dict[str, Any], required_skills: List[str]) -> int:
    candidate_skills = {skill.lower() for skill in profile.get("skills", [])}
    required = {skill.lower() for skill in required_skills}
    overlap = len(candidate_skills & required)
    coverage = int((overlap / max(len(required), 1)) * 70)
    experience_bonus = min(len(profile.get("experience", [])) * 10, 20)
    summary_bonus = 10 if profile.get("summary") else 0
    return max(45, min(98, coverage + experience_bonus + summary_bonus))


def _fallback_job_listings(profile: Dict[str, Any], job_title: str, location: str) -> List[Dict[str, Any]]:
    companies = ["Northstar Labs", "Atlas AI", "BrightPath", "Vertex Systems", "BlueHarbor", "Signal Works", "Lattice Studio", "Nimbus Group"]
    salary_ranges = ["$70k-$90k", "$85k-$105k", "$95k-$125k", "$110k-$140k", "$120k-$150k", "$130k-$165k", "$90k-$120k", "$100k-$135k"]
    skill_pool = list(dict.fromkeys(profile.get("skills", []) + ["Communication", "Problem Solving", "Stakeholder Management", "Analysis", "Presentation"]))
    if not skill_pool:
        skill_pool = ["Communication", "Problem Solving", "Analysis", "Teamwork", "Execution"]

    listings = []
    base_title = job_title.strip() or "Career Specialist"
    for index, company in enumerate(companies):
        required_skills = skill_pool[index:index + 4]
        while len(required_skills) < 4:
            required_skills.append(skill_pool[len(required_skills) % len(skill_pool)])

        fit_score = _fit_score(profile, required_skills)
        listings.append(
            {
                "title": base_title if index < 4 else f"Senior {base_title}",
                "company": company,
                "location": location or ["Remote", "New York, NY", "London, UK", "Paris, FR", "San Francisco, CA", "Berlin, DE", "Austin, TX", "Toronto, CA"][index],
                "salary_range": salary_ranges[index],
                "required_skills": required_skills,
                "description": (
                    f"{company} is hiring a {base_title} to drive measurable impact across cross-functional initiatives. "
                    f"The role blends execution, communication, and problem solving in a fast-moving environment."
                ),
                "fit_score": fit_score,
                "fit_reason": _first_sentence(
                    f"Your existing background lines up with {len(set(skill.lower() for skill in profile.get('skills', [])) & set(skill.lower() for skill in required_skills))} of the core skills for this role."
                ),
            }
        )

    return sorted(listings, key=lambda job: job["fit_score"], reverse=True)


def _fallback_skill_gap(profile: Dict[str, Any], target_job: Dict[str, Any]) -> Dict[str, Any]:
    profile_skills = {skill.strip() for skill in profile.get("skills", []) if skill.strip()}
    required_skills = {skill.strip() for skill in target_job.get("required_skills", []) if skill.strip()}
    matched = sorted(profile_skills & required_skills)
    missing = sorted(required_skills - profile_skills)

    recommendations = [
        {
            "skill": skill,
            "why_important": f"{skill} appears directly in the target role requirements and will strengthen your fit for similar openings.",
            "how_to_learn": f"Build one portfolio-ready example using {skill}, then add the result to your CV and interview stories.",
        }
        for skill in missing
    ]

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "recommendations": recommendations,
    }


def _fallback_optimise_cv(profile: Dict[str, Any], target_job: Dict[str, Any]) -> Dict[str, Any]:
    required_skills = ", ".join(target_job.get("required_skills", [])[:4])
    summary_source = profile.get("summary") or "Experienced professional with a track record of delivering work across collaborative teams."
    summary = (
        f"{summary_source} I am targeting {target_job.get('title', 'this role')} opportunities where I can apply "
        f"{required_skills or 'my strongest skills'} to deliver clear business impact. "
        f"My experience shows consistent execution, adaptability, and cross-functional communication."
    )

    optimised_experience = []
    for item in profile.get("experience", []):
        bullets = item.get("bullets", [])
        reframed = []
        for bullet in bullets:
            clean_bullet = bullet.strip().rstrip(".")
            if clean_bullet:
                reframed.append(f"Applied role-relevant judgment and ownership to {clean_bullet.lower()}.")
        optimised_experience.append(
            {
                "title": item.get("title", ""),
                "company": item.get("company", ""),
                "dates": item.get("dates", ""),
                "bullets": reframed or bullets,
            }
        )

    return {"summary": summary, "experience": optimised_experience}


def _fallback_interview_questions(profile: Dict[str, Any], target_job: Dict[str, Any]) -> List[Dict[str, Any]]:
    experience = profile.get("experience", [])
    primary_experience = experience[0] if experience else {"title": "Recent Role", "company": "your team", "bullets": [profile.get("summary", "handled cross-functional work")]}
    situation = primary_experience.get("company", "my team")
    task = primary_experience.get("title", "my role")
    action = primary_experience.get("bullets", ["handled key responsibilities"])[0]

    prompts = [
        ("Behavioural", "Tell me about a time you took ownership of a difficult project."),
        ("Behavioural", "Describe a time you had to align different stakeholders."),
        ("Behavioural", "Tell me about a time you improved a process."),
        ("Technical", f"How have you used your core skills to succeed in a role like {target_job.get('title', 'this one')}?"),
        ("Technical", "Describe a technical or domain challenge you solved."),
        ("Technical", "How do you decide which tools or methods to use?"),
        ("Situational", "What would you do if priorities shifted suddenly in this role?"),
        ("Situational", "How would you handle a gap between your current skills and a new requirement?"),
        ("Company Fit", f"Why do you want to work at {target_job.get('company', 'this company')}?"),
        ("Company Fit", "What makes you a strong fit for this team?"),
    ]

    answers = []
    for category, question in prompts:
        answers.append(
            {
                "category": category,
                "question": question,
                "answer": (
                    f"Situation: In {situation}, I was working as {task}. "
                    f"Task: I needed to deliver strong results while keeping the team aligned. "
                    f"Action: I focused on {action}. "
                    f"Result: That experience strengthened the exact kind of ownership and execution this role requires."
                ),
            }
        )
    return answers


def parse_cv_with_ai(text: str) -> Dict[str, Any]:
    system_prompt = (
        "You are a CV parser. Extract the following fields as JSON: "
        "name, email, phone, summary, skills (array), experience (array of "
        "{title, company, dates, bullets[]}), education (array of {degree, school, year}). "
        "Return only valid JSON, no markdown."
    )

    try:
        payload = _chat_json(system_prompt, text)
        _set_status("parse_cv", "live")
        return {
            "name": str(payload.get("name", "")).strip(),
            "email": str(payload.get("email", "")).strip(),
            "phone": str(payload.get("phone", "")).strip(),
            "summary": str(payload.get("summary", "")).strip(),
            "skills": _string_list(payload.get("skills", [])),
            "experience": _normalise_experience(payload.get("experience", [])),
            "education": _normalise_education(payload.get("education", [])),
        }
    except Exception as exc:
        _set_status("parse_cv", "fallback", str(exc))
        return _fallback_parse_cv(text)


def generate_job_listings(profile: Dict[str, Any], job_title: str, location: str) -> List[Dict[str, Any]]:
    system_prompt = (
        "You are an expert recruiting analyst. Generate realistic job listings and calculate candidate fit. "
        "Return a JSON object with a single key called listings. Each listing must include: "
        "title, company, location, salary_range, required_skills, description, fit_score, fit_reason. "
        "Produce exactly 8 listings and sort them by fit_score descending."
    )

    user_prompt = f"""
Candidate profile:
{json.dumps(profile, indent=2)}

Target role: {job_title}
Preferred location: {location or "Flexible / remote"}

Instructions:
- Generate 8 realistic listings.
- Each description should be 2-3 sentences.
- fit_score must be an integer from 0 to 100.
- fit_reason must be one sentence explaining the score.
- required_skills must be a concise array.
"""

    try:
        payload = _chat_json(system_prompt, user_prompt)
        _set_status("job_search", "live")
        return _normalise_jobs(payload.get("listings", []))
    except Exception as exc:
        _set_status("job_search", "fallback", str(exc))
        return _fallback_job_listings(profile, job_title, location)


def analyze_skill_gap(profile: Dict[str, Any], target_job: Dict[str, Any]) -> Dict[str, Any]:
    system_prompt = (
        "You compare a candidate profile against a job and return a concise skills gap analysis. "
        "Return a JSON object with matched_skills, missing_skills, and recommendations."
    )

    user_prompt = f"""
Candidate profile:
{json.dumps(profile, indent=2)}

Target job:
{json.dumps(target_job, indent=2)}

Return:
- matched_skills: array
- missing_skills: array
- recommendations: array of objects with skill, why_important, how_to_learn
"""

    try:
        payload = _chat_json(system_prompt, user_prompt)
        _set_status("skill_gap", "live")
        recommendations = []
        for item in payload.get("recommendations", []):
            if not isinstance(item, dict):
                continue
            recommendations.append(
                {
                    "skill": str(item.get("skill", "")).strip(),
                    "why_important": str(item.get("why_important", "")).strip(),
                    "how_to_learn": str(item.get("how_to_learn", "")).strip(),
                }
            )

        return {
            "matched_skills": _string_list(payload.get("matched_skills", [])),
            "missing_skills": _string_list(payload.get("missing_skills", [])),
            "recommendations": recommendations,
        }
    except Exception as exc:
        _set_status("skill_gap", "fallback", str(exc))
        return _fallback_skill_gap(profile, target_job)


def optimise_cv(profile: Dict[str, Any], target_job: Dict[str, Any]) -> Dict[str, Any]:
    system_prompt = (
        "You are an expert CV editor. Rewrite the candidate summary and experience bullets to better fit the target job. "
        "You must only reframe real experience and never invent new facts. "
        "Return a JSON object with summary and experience."
    )

    user_prompt = f"""
Candidate profile:
{json.dumps(profile, indent=2)}

Target job:
{json.dumps(target_job, indent=2)}

Return:
- summary: 3-4 sentences
- experience: array using the same title, company, and dates, but improved bullets based only on the provided experience
"""

    try:
        payload = _chat_json(system_prompt, user_prompt)
        _set_status("optimise_cv", "live")
        return {
            "summary": str(payload.get("summary", "")).strip(),
            "experience": _normalise_experience(payload.get("experience", [])),
        }
    except Exception as exc:
        _set_status("optimise_cv", "fallback", str(exc))
        return _fallback_optimise_cv(profile, target_job)


def prepare_interview_questions(profile: Dict[str, Any], target_job: Dict[str, Any]) -> List[Dict[str, Any]]:
    system_prompt = (
        "You create interview preparation packs. Return a JSON object with a questions array. "
        "Generate exactly 10 interview questions with full STAR answers using only the candidate's real experience. "
        "Include 3 behavioural, 3 technical, 2 situational, and 2 company-fit questions."
    )

    user_prompt = f"""
Candidate profile:
{json.dumps(profile, indent=2)}

Target job:
{json.dumps(target_job, indent=2)}

Return each question as:
- question
- answer
- category
"""

    try:
        payload = _chat_json(system_prompt, user_prompt)
        _set_status("interview_prep", "live")
        questions = []
        for item in payload.get("questions", []):
            if not isinstance(item, dict):
                continue
            questions.append(
                {
                    "question": str(item.get("question", "")).strip(),
                    "answer": str(item.get("answer", "")).strip(),
                    "category": str(item.get("category", "")).strip() or "Interview Question",
                }
            )
        return questions
    except Exception as exc:
        _set_status("interview_prep", "fallback", str(exc))
        return _fallback_interview_questions(profile, target_job)

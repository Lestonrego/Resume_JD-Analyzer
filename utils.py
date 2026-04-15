# utils.py - Resume-JD Analyzer | Backend Logic

import re
import json
import hashlib
from io import BytesIO

from pypdf import PdfReader
from docx import Document

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GROQ_API_KEY    = "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"
MAX_ITERATIONS  = 3
MODEL_NAME      = "llama-3.3-70b-versatile"
TEMPERATURE     = 0   # fully deterministic

# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a world-class ATS specialist and senior HR consultant with 20+ years of experience.
PII (name, email, phone, LinkedIn, GitHub) has been redacted. Focus only on skills, experience, and qualifications.

CRITICAL SCORING RULES:
1. Be HARSH and REALISTIC. Most resumes score 40-70%. Only exceptional matches score 80%+.
2. EXPERIENCE MISMATCH: If JD requires Senior/Lead/Principal but resume is Fresher/Junior, overall_score MUST be below 45. If overqualified senior applies for fresher role, cap at 65.
3. overall_score = holistic fit (skills + exp level + domain). match_percentage = keyword overlap only. ats_compatibility.score = format only.
4. Never inflate scores to seem encouraging.

ALWAYS respond with ONLY this exact JSON (no markdown, no extra text):
{
    "overall_score": <int 0-100>,
    "match_percentage": <int 0-100>,
    "experience_analysis": {
        "resume_level": "<Fresher|Junior|Mid-Level|Senior|Executive>",
        "jd_level": "<Fresher|Junior|Mid-Level|Senior|Executive>",
        "level_match": <true|false>,
        "mismatch_reason": "<string or null>",
        "years_required": "<from JD or Not specified>",
        "years_detected": "<from resume or Not clear>"
    },
    "analysis": {
        "strengths": ["<str>","<str>","<str>"],
        "gaps": ["<str>","<str>","<str>"],
        "keyword_match": {
            "matched_keywords": ["<str>"],
            "missing_keywords": ["<str>"]
        }
    },
    "skill_recommendations": {
        "technical_skills": [{"skill":"<n>","priority":"<High|Medium|Low>","reason":"<why>","how_to_improve":"<steps>"}],
        "soft_skills":      [{"skill":"<n>","priority":"<High|Medium|Low>","reason":"<why>","how_to_improve":"<steps>"}]
    },
    "resume_improvements": {
        "formatting": ["<str>"],
        "content":    ["<str>"],
        "keywords_to_add": ["<str>"]
    },
    "ats_compatibility": {
        "score": <int 0-100>,
        "issues":      ["<str>"],
        "suggestions": ["<str>"]
    },
    "red_flags": ["<str>"],
    "interview_prep": ["<str>","<str>","<str>"],
    "summary": "<3-4 sentence honest assessment>"
}"""

# ─────────────────────────────────────────────
# PII REDACTION
# ─────────────────────────────────────────────
PII_PATTERNS = [
    (r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}',                  '[EMAIL]'),
    (r'(\+?\d[\d\s\-().]{7,}\d)',                         '[PHONE]'),
    (r'(https?://)?(www\.)?linkedin\.com/in/[\w\-]+/?',   '[LINKEDIN]'),
    (r'(https?://)?(www\.)?github\.com/[\w\-]+/?',        '[GITHUB]'),
    (r'https?://\S+',                                     '[URL]'),
]

def redact_pii(text: str) -> str:
    for p, r in PII_PATTERNS:
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    lines, done = [], False
    for line in text.split('\n'):
        s = line.strip()
        if s and not done and len(s.split()) <= 5 and ':' not in s and s.replace(' ','').isalpha():
            lines.append('[NAME REDACTED]'); done = True
        else:
            lines.append(line)
    return '\n'.join(lines)

# ─────────────────────────────────────────────
# TEXT EXTRACTION
# ─────────────────────────────────────────────
def extract_text(file) -> str:
    name = file.name.lower()
    if name.endswith('.pdf'):
        raw = file.read()
        try:
            text = "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(raw)).pages).strip()
        except Exception:
            text = ""
        if len(text) < 50:
            try:
                import pdfplumber
                with pdfplumber.open(BytesIO(raw)) as pdf:
                    text = "\n".join(p.extract_text() or "" for p in pdf.pages).strip()
            except Exception:
                pass
        if len(text) < 50:
            raise ValueError(f"Could not extract PDF text ({len(text)} chars). Try .docx or .txt.")
        return text
    elif name.endswith('.docx'):
        return "\n".join(p.text for p in Document(BytesIO(file.read())).paragraphs).strip()
    elif name.endswith('.txt'):
        return file.read().decode('utf-8').strip()
    raise ValueError("Unsupported format. Use PDF, DOCX, or TXT.")

# ─────────────────────────────────────────────
# HASH — detect if inputs changed
# ─────────────────────────────────────────────
def content_hash(resume: str, jd: str) -> str:
    return hashlib.md5((resume.strip() + "|||" + jd.strip()).encode()).hexdigest()

# ─────────────────────────────────────────────
# LLM SETUP — stateless, no memory injected into analysis
# ─────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=4096,
        model_kwargs={"seed": 42},
    )

# ─────────────────────────────────────────────
# ANALYZE — fully stateless (no memory = no score drift)
# ─────────────────────────────────────────────
def analyze(resume_text: str, jd_text: str, llm) -> dict:
    safe = redact_pii(resume_text)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"JOB DESCRIPTION:\n{jd_text}\n\nRESUME (PII redacted):\n{safe}\n\nReturn ONLY the JSON.")
    ]
    last_error, raw = None, None
    for attempt in range(1, MAX_ITERATIONS + 1):
        try:
            raw = llm.invoke(messages).content.strip()
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
            return json.loads(raw)
        except json.JSONDecodeError as e:
            last_error = str(e)
            if attempt < MAX_ITERATIONS:
                messages += [AIMessage(content=raw or ""), HumanMessage(content="Invalid JSON. Return ONLY raw JSON, nothing else.")]
        except Exception as e:
            raise RuntimeError(str(e))
    raise RuntimeError(f"Failed after {MAX_ITERATIONS} attempts: {last_error}")

# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────
def score_class(s): return "score-high" if s>=75 else ("score-mid" if s>=50 else "score-low")
def score_emoji(s): return "🟢" if s>=75 else ("🟡" if s>=50 else "🔴")

EXP_STYLES = {
    "Fresher":   ("exp-fresher",   "🌱"),
    "Junior":    ("exp-junior",    "🔰"),
    "Mid-Level": ("exp-mid",       "⚡"),
    "Senior":    ("exp-senior",    "🔥"),
    "Executive": ("exp-executive", "👑"),
}
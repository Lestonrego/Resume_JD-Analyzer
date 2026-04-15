# app.py - Resume-JD Analyzer | State-of-the-Art Edition
# Run with: streamlit run app.py

import streamlit as st
from datetime import datetime

from utils import (
    get_llm, analyze, extract_text, content_hash,
    score_class, score_emoji, EXP_STYLES
)

# ─────────────────────────────────────────────
# PAGE CONFIG & STYLES
# ─────────────────────────────────────────────
st.set_page_config(page_title="ResumeIQ Analyzer", page_icon="🎯", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0f1117; }
.main .block-container { padding-top: 2rem; max-width: 1400px; }
.hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border: 1px solid #2a2f3f; border-radius: 20px;
    padding: 40px 50px; margin-bottom: 30px; position: relative; overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, #6c63ff22 0%, transparent 70%); border-radius: 50%;
}
.hero h1 {
    font-size: 2.8em; font-weight: 700;
    background: linear-gradient(135deg, #fff 0%, #a78bfa 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; letter-spacing: -1px;
}
.hero p { color: #8892a4; font-size: 1.1em; margin: 8px 0 0; }
.score-ring-wrap {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    background: #1a1f2e; border: 1px solid #2a2f3f; border-radius: 20px;
    padding: 32px 24px; text-align: center; transition: all 0.3s;
}
.score-ring-wrap:hover { border-color: #6c63ff; transform: translateY(-2px); }
.score-number { font-size: 4em; font-weight: 700; font-family: 'DM Mono', monospace; line-height: 1; }
.score-label  { color: #8892a4; font-size: 0.85em; margin-top: 6px; letter-spacing: 0.05em; text-transform: uppercase; }
.score-sublabel { color: #6c7a8d; font-size: 0.75em; margin-top: 4px; }
.score-high { color: #34d399; }
.score-mid  { color: #fbbf24; }
.score-low  { color: #f87171; }
.exp-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 16px; border-radius: 30px; font-size: 0.85em; font-weight: 600; border: 1px solid; }
.exp-fresher   { background: #0d2137; border-color: #38bdf8; color: #38bdf8; }
.exp-junior    { background: #0d2e1c; border-color: #34d399; color: #34d399; }
.exp-mid       { background: #2d1f0d; border-color: #fbbf24; color: #fbbf24; }
.exp-senior    { background: #2d0d1c; border-color: #f87171; color: #f87171; }
.exp-executive { background: #1c0d2d; border-color: #a78bfa; color: #a78bfa; }
.mismatch-alert {
    background: linear-gradient(135deg, #2d1515, #1f0d0d); border: 1px solid #f87171;
    border-radius: 12px; padding: 18px 22px; margin: 16px 0;
    display: flex; align-items: flex-start; gap: 12px;
}
.mismatch-alert .icon { font-size: 1.5em; }
.mismatch-alert .text { color: #fca5a5; font-size: 0.95em; line-height: 1.6; }
.mismatch-alert strong { color: #f87171; display: block; margin-bottom: 4px; }
.section-title {
    font-size: 1.1em; font-weight: 600; color: #e2e8f0;
    text-transform: uppercase; letter-spacing: 0.08em; margin: 28px 0 14px;
    display: flex; align-items: center; gap: 10px;
}
.section-title::after { content: ''; flex: 1; height: 1px; background: #2a2f3f; }
.chip-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
.chip { display: inline-flex; align-items: center; gap: 5px; padding: 5px 14px; border-radius: 30px; font-size: 0.82em; font-weight: 500; }
.chip-green { background: #0d2e1c; border: 1px solid #34d39955; color: #34d399; }
.chip-red   { background: #2d1515;  border: 1px solid #f8717155; color: #f87171; }
.chip-blue  { background: #0d1f37;  border: 1px solid #60a5fa55; color: #60a5fa; }
.skill-row {
    background: #141920; border: 1px solid #2a2f3f; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 10px; display: flex; align-items: flex-start; gap: 14px;
}
.skill-priority { width: 8px; min-width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; }
.p-high   { background: #f87171; box-shadow: 0 0 8px #f8717166; }
.p-medium { background: #fbbf24; box-shadow: 0 0 8px #fbbf2466; }
.p-low    { background: #34d399; box-shadow: 0 0 8px #34d39966; }
.skill-content { flex: 1; }
.skill-name   { color: #e2e8f0; font-weight: 600; font-size: 0.95em; }
.skill-reason { color: #8892a4; font-size: 0.85em; margin-top: 4px; line-height: 1.5; }
.skill-how    { color: #60a5fa; font-size: 0.82em; margin-top: 6px; font-style: italic; }
.strength-item {
    background: #0d2e1c; border: 1px solid #34d39933; border-left: 3px solid #34d399;
    border-radius: 10px; padding: 12px 16px; color: #a7f3d0; font-size: 0.9em; line-height: 1.6; margin-bottom: 8px;
}
.gap-item {
    background: #2d1515; border: 1px solid #f8717133; border-left: 3px solid #f87171;
    border-radius: 10px; padding: 12px 16px; color: #fca5a5; font-size: 0.9em; line-height: 1.6; margin-bottom: 8px;
}
.improve-item {
    background: #141920; border: 1px solid #2a2f3f; border-left: 3px solid #6c63ff;
    border-radius: 10px; padding: 12px 16px; color: #c4c9d4; font-size: 0.9em; line-height: 1.6; margin-bottom: 8px;
}
.summary-box {
    background: linear-gradient(135deg, #1a1237, #0f1117); border: 1px solid #6c63ff44;
    border-radius: 14px; padding: 22px 26px; color: #c4b5fd; font-size: 1em; line-height: 1.8;
}
.privacy-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0d2e1c; border: 1px solid #34d39933;
    border-radius: 30px; padding: 5px 14px; font-size: 0.8em; color: #34d399; margin-bottom: 20px;
}
.history-item {
    background: #141920; border: 1px solid #2a2f3f; border-radius: 10px;
    padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
}
.history-score { font-family: 'DM Mono', monospace; font-weight: 600; color: #a78bfa; }
.history-meta  { color: #6c7a8d; font-size: 0.8em; }
.stFileUploader > div { background: #1a1f2e !important; border: 1px dashed #2a2f3f !important; border-radius: 12px !important; }
.stTextArea textarea { background: #1a1f2e !important; border: 1px solid #2a2f3f !important; color: #e2e8f0 !important; border-radius: 12px !important; }
.stButton > button { border-radius: 12px !important; font-family: 'DM Sans', sans-serif !important; }
.stTabs [data-baseweb="tab-list"] { background: #1a1f2e; border-radius: 10px; gap: 4px; }
.stTabs [data-baseweb="tab"]      { border-radius: 8px !important; color: #8892a4 !important; }
.stTabs [aria-selected="true"]    { background: #6c63ff22 !important; color: #a78bfa !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LLM SETUP — cached per session
# ─────────────────────────────────────────────
@st.cache_resource
def get_cached_llm():
    return get_llm()

llm = get_cached_llm()

for key, val in {"result": None, "score_history": [], "last_hash": None}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ═════════════════════════════════════════════
# UI
# ═════════════════════════════════════════════
st.markdown('<div class="hero"><h1>🎯 ResumeIQ Analyzer</h1><p>State-of-the-art resume intelligence · Experience-aware scoring · Privacy-first</p></div>', unsafe_allow_html=True)
st.markdown('<div class="privacy-pill">🔒 Name · Email · Phone · LinkedIn · GitHub redacted before AI analysis</div>', unsafe_allow_html=True)

# ── Sidebar: history ─────────────────────────
with st.sidebar:
    st.markdown("### 📈 Score History")
    if st.session_state.score_history:
        for e in reversed(st.session_state.score_history[-10:]):
            st.markdown(f'<div class="history-item"><div><div style="color:#e2e8f0;font-size:0.85em">{e["file"]}</div><div class="history-meta">{e["time"]}</div></div><div class="history-score">{score_emoji(e["overall"])} {e["overall"]}%</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#6c7a8d;font-size:0.85em">No analyses yet.</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div style="color:#8892a4;font-size:0.82em;line-height:1.7"><b style="color:#c4c9d4">Overall Score</b><br>Holistic fit: skills, exp level, domain.<br><br><b style="color:#c4c9d4">Match %</b><br>Keyword & skill overlap only.<br><br><b style="color:#c4c9d4">ATS Score</b><br>Format & parseability.<br><br><b style="color:#f87171">⚠ Exp mismatch penalized heavily.</b></div>', unsafe_allow_html=True)

# ── Inputs ───────────────────────────────────
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown('<div class="section-title">📎 Resume</div>', unsafe_allow_html=True)
    resume_file = st.file_uploader("Resume", type=["pdf","docx","txt"], label_visibility="collapsed")
with c2:
    st.markdown('<div class="section-title">📋 Job Description</div>', unsafe_allow_html=True)
    jd_file = st.file_uploader("JD File", type=["pdf","docx","txt"], label_visibility="collapsed")
    st.markdown('<p style="color:#6c7a8d;font-size:0.85em;text-align:center;margin:6px 0">— or paste below —</p>', unsafe_allow_html=True)
    jd_text_input = st.text_area("JD Text", height=140, placeholder="Paste job description here...", label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)
cb, cr = st.columns([4,1])
with cb: analyze_btn = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)
with cr:
    if st.button("🗑️ Reset", use_container_width=True):
        st.session_state.result = None
        st.session_state.last_hash = None
        st.rerun()

# ── Run analysis ─────────────────────────────
if analyze_btn:
    if not resume_file: st.error("⚠️ Upload a resume."); st.stop()
    if not jd_file and not jd_text_input.strip(): st.error("⚠️ Upload a JD or paste text."); st.stop()
    with st.spinner("🔍 Analyzing — this takes ~15 seconds..."):
        try:
            rtxt = extract_text(resume_file)
            jtxt = extract_text(jd_file) if jd_file else jd_text_input.strip()
            if len(rtxt) < 50: st.error("Resume too short."); st.stop()
            if len(jtxt) < 50: st.error("JD too short.");     st.stop()
            h = content_hash(rtxt, jtxt)
            if h == st.session_state.last_hash and st.session_state.result:
                st.info("ℹ️ Same inputs detected — showing cached result. Change resume or JD to re-analyze.")
            else:
                res = analyze(rtxt, jtxt, llm)
                st.session_state.result = res
                st.session_state.last_hash = h
                st.session_state.score_history.append({
                    "file": resume_file.name[:25],
                    "overall": res.get("overall_score", 0),
                    "time": datetime.now().strftime("%H:%M:%S"),
                })
        except Exception as e:
            st.error(f"❌ {e}"); st.stop()

# ── Display results ───────────────────────────
if st.session_state.result:
    R = st.session_state.result
    exp  = R.get("experience_analysis", {})
    ana  = R.get("analysis", {})
    skl  = R.get("skill_recommendations", {})
    imp  = R.get("resume_improvements", {})
    ats  = R.get("ats_compatibility", {})
    kw   = ana.get("keyword_match", {})
    overall   = R.get("overall_score", 0)
    match_pct = R.get("match_percentage", 0)
    ats_score = ats.get("score", 0)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Scores</div>', unsafe_allow_html=True)

    # Exp badges
    rl = exp.get("resume_level","Unknown"); jl = exp.get("jd_level","Unknown")
    rs, ri2 = EXP_STYLES.get(rl,("exp-junior","👤")); js, ji2 = EXP_STYLES.get(jl,("exp-junior","💼"))
    st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap"><span style="color:#8892a4;font-size:0.85em">Candidate:</span><span class="exp-badge {rs}">{ri2} {rl}</span><span style="color:#6c7a8d">→</span><span style="color:#8892a4;font-size:0.85em">Role requires:</span><span class="exp-badge {js}">{ji2} {jl}</span><span style="color:#6c7a8d;font-size:0.8em">({exp.get("years_required","?")} required · {exp.get("years_detected","?")} detected)</span></div>', unsafe_allow_html=True)

    if not exp.get("level_match", True) and exp.get("mismatch_reason"):
        st.markdown(f'<div class="mismatch-alert"><div class="icon">⚠️</div><div class="text"><strong>Experience Level Mismatch</strong>{exp["mismatch_reason"]}</div></div>', unsafe_allow_html=True)

    # Score cards
    sc1, sc2, sc3 = st.columns(3)
    for col, score, label, sub in [(sc1,overall,"Overall Match","Holistic fit"),(sc2,match_pct,"Keyword Match","Content alignment"),(sc3,ats_score,"ATS Score","Parseability")]:
        with col:
            st.markdown(f'<div class="score-ring-wrap"><div class="score-number {score_class(score)}">{score}%</div><div class="score-label">{label}</div><div class="score-sublabel">{sub}</div></div>', unsafe_allow_html=True)

    # Summary
    st.markdown('<div class="section-title">💬 Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="summary-box">{R.get("summary","")}</div>', unsafe_allow_html=True)

    # Red flags
    if R.get("red_flags"):
        st.markdown('<div class="section-title">🚩 Red Flags</div>', unsafe_allow_html=True)
        for f in R["red_flags"]:
            st.markdown(f'<div class="gap-item">🚩 {f}</div>', unsafe_allow_html=True)

    # Strengths & gaps
    st.markdown('<div class="section-title">💪 Strengths & Gaps</div>', unsafe_allow_html=True)
    sg1, sg2 = st.columns(2, gap="large")
    with sg1:
        st.markdown('<p style="color:#34d399;font-weight:600;margin-bottom:8px">✅ Strengths</p>', unsafe_allow_html=True)
        for s in ana.get("strengths",[]): st.markdown(f'<div class="strength-item">{s}</div>', unsafe_allow_html=True)
    with sg2:
        st.markdown('<p style="color:#f87171;font-weight:600;margin-bottom:8px">⚠️ Gaps</p>', unsafe_allow_html=True)
        for g in ana.get("gaps",[]): st.markdown(f'<div class="gap-item">{g}</div>', unsafe_allow_html=True)

    # Keywords
    st.markdown('<div class="section-title">🔑 Keywords</div>', unsafe_allow_html=True)
    kw1, kw2 = st.columns(2, gap="large")
    with kw1:
        st.markdown('<p style="color:#34d399;font-size:0.85em;font-weight:600">✓ MATCHED</p>', unsafe_allow_html=True)
        matched_chips = ' '.join(['<span class="chip chip-green">✓ ' + k + '</span>' for k in kw.get('matched_keywords',[])])
        st.markdown('<div class="chip-wrap">' + (matched_chips or '<span style="color:#6c7a8d">None</span>') + '</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#f87171;font-size:0.85em;font-weight:600">✗ MISSING</p>', unsafe_allow_html=True)
        missing_chips = ' '.join(['<span class="chip chip-red">✗ ' + k + '</span>' for k in kw.get('missing_keywords',[])])
        st.markdown('<div class="chip-wrap">' + (missing_chips or '<span style="color:#6c7a8d">None</span>') + '</div>', unsafe_allow_html=True)
    # Skills + interview prep tabs
    st.markdown('<div class="section-title">🛠️ Skills & Prep</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔧 Technical", "💼 Soft Skills", "🎤 Interview Prep"])
    for tab, slist in [(t1, skl.get("technical_skills",[])), (t2, skl.get("soft_skills",[]))]:
        with tab:
            for sk in slist:
                p = sk.get("priority","Medium").lower()
                st.markdown(f'<div class="skill-row"><div class="skill-priority p-{p}"></div><div class="skill-content"><div class="skill-name">{sk.get("skill","")} <span style="color:#6c7a8d;font-size:0.8em;font-weight:400">{sk.get("priority","")} Priority</span></div><div class="skill-reason">{sk.get("reason","")}</div><div class="skill-how">→ {sk.get("how_to_improve","")}</div></div></div>', unsafe_allow_html=True)
    with t3:
        for i, q in enumerate(R.get("interview_prep",[]), 1):
            st.markdown(f'<div class="improve-item"><span style="color:#a78bfa;font-weight:600;font-family:monospace">Q{i}.</span> {q}</div>', unsafe_allow_html=True)

    # Improvements
    st.markdown('<div class="section-title">📝 Resume Improvements</div>', unsafe_allow_html=True)
    ri1, ri2_col = st.columns(2, gap="large")
    with ri1:
        st.markdown('<p style="color:#a78bfa;font-size:0.85em;font-weight:600">FORMATTING</p>', unsafe_allow_html=True)
        for s in imp.get("formatting",[]): st.markdown(f'<div class="improve-item">{s}</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#a78bfa;font-size:0.85em;font-weight:600;margin-top:14px">CONTENT</p>', unsafe_allow_html=True)
        for s in imp.get("content",[]): st.markdown(f'<div class="improve-item">{s}</div>', unsafe_allow_html=True)
    with ri2_col:
        st.markdown('<p style="color:#60a5fa;font-size:0.85em;font-weight:600">KEYWORDS TO ADD</p>', unsafe_allow_html=True)
        add_chips = ' '.join(['<span class="chip chip-blue">+ ' + k + '</span>' for k in imp.get('keywords_to_add',[])])
        st.markdown('<div class="chip-wrap">' + (add_chips or '<span style="color:#6c7a8d">None</span>') + '</div>', unsafe_allow_html=True)
    # ATS
    st.markdown('<div class="section-title">🤖 ATS Optimization</div>', unsafe_allow_html=True)
    a1, a2 = st.columns(2, gap="large")
    with a1:
        st.markdown('<p style="color:#f87171;font-size:0.85em;font-weight:600">ISSUES</p>', unsafe_allow_html=True)
        for x in ats.get("issues",[]): st.markdown(f'<div class="gap-item">{x}</div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<p style="color:#34d399;font-size:0.85em;font-weight:600">TIPS</p>', unsafe_allow_html=True)
        for x in ats.get("suggestions",[]): st.markdown(f'<div class="strength-item">{x}</div>', unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;color:#3a4055;font-size:0.78em;padding:30px 0">ResumeIQ · LangChain + Groq LLaMA 3.3 70B · Deterministic · Experience-aware · Privacy-first</div>', unsafe_allow_html=True)
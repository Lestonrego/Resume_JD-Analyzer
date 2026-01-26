import sys
sys.stdin.reconfigure(encoding="utf-8")

from pypdf import PdfReader
from groq import Groq
from docx import Document
import json
import tkinter as tk
from tkinter import filedialog





SYSTEM_PROMPT = """
You are an expert ATS and HR professional.

ALWAYS respond ONLY in valid JSON with EXACTLY this structure:

{
"overall_score": number,
"match_percentage": number,
"analysis":{
    "strengths":[string],
    "gaps":[string],
    "keyword_match":{
        "matched_keywords":[string],
        "missing_keywords":[string]
    }
},
"skill_recommendations":{
    "technical_skills":[{
        "skill":string,
        "priority":"High|Medium|Low",
        "reason":string,
        "how_to_improve":string
    }],
    "soft_skills":[{
        "skill":string,
        "priority":"High|Medium|Low",
        "reason":string,
        "how_to_improve":string
    }]
},
"resume_improvements":{
    "formatting":[string],
    "content":[string],
    "keywords_to_add":[string]
},
"ats_compatibility":{
    "score":number,
    "issues":[string],
    "suggestions":[string]
},
"summary":string
}

Return ONLY JSON.
"""



root = tk.Tk()
root.withdraw()


def extract_pdf(path):
    reader = PdfReader(path)
    return "\n".join(p.extract_text() for p in reader.pages)

def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text(path):
    p = path.lower()
    if p.endswith(".pdf"):
        return extract_pdf(path)
    if p.endswith(".docx"):
        return extract_docx(path)
    if p.endswith(".txt"):
        return open(path,encoding="utf8").read()
    raise Exception("Unsupported file")


def analyze(resume,jd):

    prompt=f"""
JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":prompt}
        ],
        temperature=0.3,
        response_format={"type":"json_object"}
    )

    return json.loads(r.choices[0].message.content)



def pick(title):
    return filedialog.askopenfilename(parent=root,title=title)


def main():

    print("\nSELECT RESUME FILE")
    resume = pick("Resume")

    if not resume:
        print("Resume missing")
        return

    print("\nJOB DESCRIPTION INPUT:")
    print("1 → Upload JD File")
    print("2 → Paste JD Text")

    ch = input("Choose 1 or 2: ").strip()

    if ch=="1":
        jd = pick("JD File")
        if not jd:
            print("JD missing")
            return
        jd_text = extract_text(jd)

    elif ch=="2":
        print("\nPaste JD. Type END when finished:\n")
        lines=[]
        while True:
            l=input()
            if l.strip().upper()=="END":
                break
            lines.append(l)
        jd_text="\n".join(lines)

    else:
        print("Invalid choice")
        return

    resume_text = extract_text(resume)

    print("\nAnalyzing...\n")

    result = analyze(resume_text,jd_text)
    print(json.dumps(result, indent=4))

if __name__=="__main__":
    main()

import sys
sys.stdin.reconfigure(encoding="utf-8")

from pypdf import PdfReader
from groq import Groq
from docx import Document
import json
import tkinter as tk
from tkinter import filedialog



SYSTEM_PROMPT = """
You are NOT an HR assistant.

You are a STRICT ATS SCORING ENGINE.

You MUST behave like software, NOT like a human reviewer.

-------------------------
SCORING ALGORITHM
-------------------------

STEP 1:
Extract ALL required skills from JD.

STEP 2:
Extract ALL skills from resume.

STEP 3:
matched = intersection(resume_skills, jd_skills)

STEP 4:
match_percentage = round((len(matched) / len(jd_skills)) * 100)

STEP 5:
Experience Check:
If JD mentions REQUIRED experience (years / industry / role) AND resume has NO experience section:

Apply AUTOMATIC −25% penalty.

STEP 6:
overall_score = match_percentage / 10

-------------------------
MANDATORY RULES
-------------------------

• If resume has ZERO experience and JD requires experience:
  match_percentage MUST be BELOW 60.

• If less than 50% skills matched:
  match_percentage MUST be BELOW 50.

• Do NOT generate polite scores.

• Junior resume vs senior JD MUST score LOW.

• Different resumes MUST produce different scores.

• Never default to 80+.

• Missing experience is MAJOR FAILURE.

-------------------------

Return ONLY JSON using EXACT structure.

No commentary.
No explanation.
No prose.
Only JSON.
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
        temperature=0.8,
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

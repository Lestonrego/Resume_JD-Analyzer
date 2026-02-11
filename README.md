# Problems Faced and Solutions

1. Sometimes the resume PDF or DOCX file was not reading correctly, and some text was missing.

Solution:  
We used pypdf for PDF files and python-docx for Word files. We also added UTF-8 encoding to avoid special character errors.

---

2. The AI sometimes returned long text instead of proper structured data, which was difficult to use.

Solution:  
We added a strict system prompt and forced the AI to respond only in JSON format. This made the output clean and machine readable.

---

3. Initial results were not matching skills properly.

Solution:  
We improved the system prompt and provided both resume and job description clearly to the AI model for better comparison.

---

4. Resumes came in PDF, DOCX, and TXT formats.

Solution:  
We created a common function to detect file type and extract text accordingly.

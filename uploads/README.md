# Resume Uploads Folder

Drop existing resume PDF files into this folder (or upload them directly via the Streamlit web app under the **Experience Bank -> Ingest Resume PDF** tab).

The Resume Tailor system will:
1. Extract raw text and structure from your uploaded PDF using `pypdf`.
2. Process the text through the Gemini parsing engine.
3. Automatically categorize roles, dates, skills, and modular XYZ/CAR bullet points with skill tags (e.g., `#cloud`, `#leadership`, `#metrics`).
4. Allow you to review and save the extracted data directly into `app/master_resume.json`.

*Note: Individual PDF files in this folder are ignored by git to protect candidate privacy.*

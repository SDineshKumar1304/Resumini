import os

def extract_text(path: str) -> str:
    _, ext = os.path.splitext(path.lower())
    if ext == ".pdf":
        return _extract_pdf(path)
    elif ext in [".docx", ".doc"]:
        return _extract_docx(path)
    else:
        # try reading as text
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

def _extract_pdf(path: str) -> str:
    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber not installed. pip install pdfplumber to parse PDFs.")
        return ""
    text_parts = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)
    except Exception as e:
        print(f"PDF extraction failed: {e}")
        return ""

def _extract_docx(path: str) -> str:
    try:
        from docx import Document
    except ImportError:
        print("python-docx not installed. pip install python-docx to parse DOCX.")
        return ""
    try:
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"DOCX extraction failed: {e}")
        return ""

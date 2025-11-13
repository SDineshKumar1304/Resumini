import os
# from google.generativeai.types import tool 

# @tool
def extract_text(path: str) -> str:
    """
    Extract text content from a file (.pdf, .docx, or .txt).
    Used by the Agentic Resume Optimizer and ATS Analyzer.
    """
    print(f"📂 Processing file: {path}")
    _, ext = os.path.splitext(path.lower())

    if ext == ".pdf":
        print("🧾 Detected PDF file — extracting text...")
        return _extract_pdf(path)
    elif ext in [".docx", ".doc"]:
        print("📘 Detected Word document — extracting text...")
        return _extract_docx(path)
    else:
        print("📄 Reading plain text file...")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                print(f"✅ Text extraction complete ({len(text)} chars).")
                return text
        except Exception as e:
            print(f"⚠️ Text extraction failed: {e}")
            return ""


def _extract_pdf(path: str) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    """
    try:
        import pdfplumber
    except ImportError:
        print("⚠️ Missing dependency: install with `pip install pdfplumber`.")
        return ""

    text_parts = []
    try:
        with pdfplumber.open(path) as pdf:
            print(f"🔍 Reading {len(pdf.pages)} pages...")
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                print(f"  • Page {i} processed.")
        combined = "\n".join(text_parts)
        print(f"✅ PDF extraction complete ({len(combined)} chars).")
        return combined
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        return ""


def _extract_docx(path: str) -> str:
    """
    Extract text from a DOCX file using python-docx.
    """
    try:
        from docx import Document
    except ImportError:
        print("⚠️ Missing dependency: install with `pip install python-docx`.")
        return ""

    try:
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        print(f"✅ DOCX extraction complete ({len(text)} chars).")
        return text
    except Exception as e:
        print(f"❌ DOCX extraction failed: {e}")
        return ""


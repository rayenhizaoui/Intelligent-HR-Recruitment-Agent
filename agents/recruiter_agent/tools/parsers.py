"""
CV Parsing Tools

This module contains tools for parsing CVs/resumes from various formats,
cleaning text, and handling batch uploads.
"""

import re
import io
import unicodedata
from typing import Optional, Any, List
from langchain_core.tools import tool

try:
    import docx
    import PyPDF2
except ImportError:
    print("Warning: docx or PyPDF2 not installed. CV Parser will fail.")


# ── Text Cleaning Pipeline ──────────────────────────────────

@tool
def text_cleaner_pipeline(text: str) -> dict:
    """
    Clean and normalize raw text extracted from documents.

    Strips whitespace, removes emojis, normalizes unicode,
    and cleans up formatting artifacts.

    Args:
        text: Raw text to clean.

    Returns:
        Dictionary with 'cleaned_text' and 'stats'.
    """
    if not text:
        return {"cleaned_text": "", "stats": {"original_length": 0, "cleaned_length": 0}}

    original_length = len(text)

    # 1. Normalize unicode (NFKD → recompose to NFC)
    cleaned = unicodedata.normalize("NFKC", text)

    # 2. Remove emojis and special unicode symbols
    cleaned = re.sub(
        r"[^\w\s\.\,\-\+\#\/\(\)\[\]\:\;\@\&\%\!\?\'\"\=\>\<]",
        " ",
        cleaned,
        flags=re.UNICODE
    )

    # 3. Normalize whitespace (multiple spaces → single)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # 4. Normalize line breaks (multiple blank lines → double newline)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)

    # 5. Strip each line
    lines = [line.strip() for line in cleaned.split("\n")]
    cleaned = "\n".join(lines)

    # 6. Final strip
    cleaned = cleaned.strip()

    return {
        "cleaned_text": cleaned,
        "stats": {
            "original_length": original_length,
            "cleaned_length": len(cleaned),
            "reduction_percent": round((1 - len(cleaned) / max(original_length, 1)) * 100, 1)
        }
    }


def clean_text(text):
    """Basic text cleaning function (legacy helper)."""
    if not text:
        return ""
    result = text_cleaner_pipeline.invoke({"text": text})
    return result["cleaned_text"]


# ── CV Parser Tool ──────────────────────────────────────────

@tool
def cv_parser_tool(file_obj: Any) -> dict:
    """
    Parse a CV/Resume file object (Streamlit UploadedFile) and extract its text content.

    Supports PDF and DOCX formats.

    Args:
        file_obj: The file object (BytesIO-like) uploaded by the user.
                  Must have .name attribute ending in .pdf or .docx.

    Returns:
        A dictionary containing:
        - filename: Name of the file
        - filetype: 'pdf' or 'docx'
        - text: Cleaned extracted text
        - pages: Number of pages
        - word_count: Number of words
        - ocr_required: Boolean if OCR might be needed
        - error: Error message if parsing failed
    """
    result = {
        "filename": getattr(file_obj, "name", "unknown"),
        "filetype": None,
        "text": "",
        "pages": 0,
        "word_count": 0,
        "ocr_required": False,
        "error": None
    }

    if not hasattr(file_obj, "read"):
        result["error"] = "Invalid file object provided."
        return result

    filename = result["filename"]

    # PDF
    if filename.lower().endswith('.pdf'):
        result["filetype"] = "pdf"
        try:
            reader = PyPDF2.PdfReader(file_obj)
            result["pages"] = len(reader.pages)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            cleaned_text = clean_text(text)

            result["text"] = cleaned_text
            result["word_count"] = len(cleaned_text.split())

            if result["word_count"] < 50:
                result["ocr_required"] = True

        except Exception as e:
            result["error"] = f"PDF parsing error: {e}"
            return result

    # DOCX
    elif filename.lower().endswith('.docx'):
        result["filetype"] = "docx"
        try:
            doc = docx.Document(file_obj)

            text = "\n".join(p.text for p in doc.paragraphs if p.text)
            cleaned_text = clean_text(text)

            result["text"] = cleaned_text
            result["word_count"] = len(cleaned_text.split())

            if result["word_count"] < 50:
                result["ocr_required"] = True

        except Exception as e:
            result["error"] = f"DOCX parsing error: {e}"
            return result

    else:
        result["error"] = "Unsupported file type. Only PDF and DOCX are supported."
        return result

    return result


# ── Batch Upload Handler ────────────────────────────────────

@tool
def batch_cv_parser(file_objects: List[Any]) -> dict:
    """
    Parse multiple CV files at once. The agent can loop through 10+ CVs in a batch.

    Args:
        file_objects: A list of file objects (BytesIO-like), each with a .name attribute.

    Returns:
        Dictionary with:
        - total: Number of files processed
        - successful: Number successfully parsed
        - failed: Number that failed
        - results: List of individual parse results
    """
    results = []
    successful = 0
    failed = 0

    for file_obj in file_objects:
        try:
            parsed = cv_parser_tool.invoke({"file_obj": file_obj})
            results.append(parsed)
            if parsed.get("error"):
                failed += 1
            else:
                successful += 1
        except Exception as e:
            results.append({
                "filename": getattr(file_obj, "name", "unknown"),
                "error": str(e)
            })
            failed += 1

    return {
        "total": len(file_objects),
        "successful": successful,
        "failed": failed,
        "results": results
    }

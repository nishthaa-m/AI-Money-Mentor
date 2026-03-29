"""
Form 16 PDF Parser — extracts salary structure and tax details.
Uses PyMuPDF for text extraction + regex for field identification.
Works on both Part A (TDS details) and Part B (salary breakdown).
"""
from __future__ import annotations
import re
import fitz  # PyMuPDF


def parse_form16(pdf_bytes: bytes) -> dict:
    """
    Extract financial data from Form 16 PDF.
    Returns a dict compatible with UserProfile fields.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
    except Exception as e:
        return {"error": f"Could not read PDF: {str(e)}"}

    text_lower = text.lower()
    result = {"raw_text_length": len(text), "source": "form16"}

    # ── Gross Salary ──────────────────────────────────────────────────────────
    gross = _extract_amount(text, [
        r"gross\s+salary[^\d]*?([\d,]+)",
        r"total\s+gross[^\d]*?([\d,]+)",
        r"gross\s+total\s+income[^\d]*?([\d,]+)",
    ])
    if gross:
        result["annual_income"] = gross

    # ── Basic Salary ──────────────────────────────────────────────────────────
    basic = _extract_amount(text, [
        r"basic\s+(?:salary|pay)[^\d]*?([\d,]+)",
        r"basic[^\d\n]{0,20}([\d,]+)",
    ])
    if basic:
        result["basic_salary"] = basic

    # ── HRA ───────────────────────────────────────────────────────────────────
    hra = _extract_amount(text, [
        r"house\s+rent\s+allowance[^\d]*?([\d,]+)",
        r"\bhra\b[^\d]*?([\d,]+)",
    ])
    if hra:
        result["hra_received"] = hra

    # ── Standard Deduction ────────────────────────────────────────────────────
    std_ded = _extract_amount(text, [
        r"standard\s+deduction[^\d]*?([\d,]+)",
    ])
    if std_ded:
        result["standard_deduction_claimed"] = std_ded

    # ── Section 80C ───────────────────────────────────────────────────────────
    sec80c = _extract_amount(text, [
        r"80\s*c\b[^\d]*?([\d,]+)",
        r"life\s+insurance[^\d]*?([\d,]+)",
        r"provident\s+fund[^\d]*?([\d,]+)",
    ])
    if sec80c:
        result["section_80c_invested"] = sec80c

    # ── Section 80D ───────────────────────────────────────────────────────────
    sec80d = _extract_amount(text, [
        r"80\s*d\b[^\d]*?([\d,]+)",
        r"health\s+insurance[^\d]*?([\d,]+)",
        r"mediclaim[^\d]*?([\d,]+)",
    ])
    if sec80d:
        result["section_80d_self"] = sec80d

    # ── NPS / 80CCD ───────────────────────────────────────────────────────────
    nps = _extract_amount(text, [
        r"80\s*ccd[^\d]*?([\d,]+)",
        r"national\s+pension[^\d]*?([\d,]+)",
        r"\bnps\b[^\d]*?([\d,]+)",
    ])
    if nps:
        result["section_80ccd1b"] = nps

    # ── Home Loan Interest (Sec 24b) ──────────────────────────────────────────
    home_loan = _extract_amount(text, [
        r"(?:sec(?:tion)?\.?\s*)?24\s*[(\[]?\s*b\s*[)\]]?[^\d]*?([\d,]+)",
        r"home\s+loan\s+interest[^\d]*?([\d,]+)",
        r"interest\s+on\s+(?:housing|home)\s+loan[^\d]*?([\d,]+)",
    ])
    if home_loan:
        result["home_loan_interest"] = home_loan

    # ── TDS Deducted ──────────────────────────────────────────────────────────
    tds = _extract_amount(text, [
        r"tax\s+deducted\s+at\s+source[^\d]*?([\d,]+)",
        r"total\s+tds[^\d]*?([\d,]+)",
        r"tds\s+deducted[^\d]*?([\d,]+)",
    ])
    if tds:
        result["tds_deducted"] = tds

    # ── Taxable Income ────────────────────────────────────────────────────────
    taxable = _extract_amount(text, [
        r"taxable\s+income[^\d]*?([\d,]+)",
        r"net\s+taxable[^\d]*?([\d,]+)",
        r"income\s+chargeable\s+to\s+tax[^\d]*?([\d,]+)",
    ])
    if taxable:
        result["taxable_income_form16"] = taxable

    # ── Employer Name ─────────────────────────────────────────────────────────
    employer = _extract_text(text, [
        r"name\s+of\s+(?:the\s+)?employer[:\s]+([A-Za-z][^\n]{3,50})",
        r"employer[:\s]+([A-Za-z][^\n]{3,50})",
    ])
    if employer:
        result["employer"] = employer.strip()

    # ── PAN ───────────────────────────────────────────────────────────────────
    pan = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text)
    if pan:
        result["pan_masked"] = pan.group()[:5] + "XXXXX"

    # ── Financial Year ────────────────────────────────────────────────────────
    fy = re.search(r'(?:financial\s+year|f\.?y\.?)[:\s]*(\d{4}[-–]\d{2,4})', text_lower)
    if fy:
        result["financial_year"] = fy.group(1)

    result["fields_extracted"] = [k for k in result if k not in ("raw_text_length", "source", "error")]
    result["confidence"] = "high" if len(result["fields_extracted"]) >= 4 else "low"

    return result


def _extract_amount(text: str, patterns: list[str]) -> float | None:
    """Try each pattern, return first match as float."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "").strip()
            try:
                val = float(raw)
                if 1000 <= val <= 100_000_000:  # sanity: ₹1K to ₹10Cr
                    return val
            except ValueError:
                continue
    return None


def _extract_text(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

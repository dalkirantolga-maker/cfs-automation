import re
import pdfplumber


def extract_pdf_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")
    return text


def parse_delivery_order(text):
    data = {
        "Container No": "", "DO No": "", "BL No": "", "Acente": "", "Consignee": "",
        "Vessel": "", "Voyage": "", "Size/Type": "", "Seal No": "", "EXP Date": ""
    }

    m = re.search(r"\b[A-Z]{4}\d{7}\b", text)
    if m: data["Container No"] = m.group(0)

    m = re.search(r"DELIVERY ORDER NO\s*[:\-]?\s*([A-Z0-9]+)", text, re.I)
    if m: data["DO No"] = m.group(1)

    m = re.search(r"B/L\s*-\s*NO\s*[:\-]?\s*([A-Z0-9]+)", text, re.I)
    if m: data["BL No"] = m.group(1)

    m = re.search(r"VESSEL\s*[:\-]?\s*([A-Z0-9\s]+)", text, re.I)
    if m: data["Vessel"] = m.group(1).split("\n")[0].strip().upper()

    m = re.search(r"VOYAGE\s*[:\-]?\s*([A-Z0-9]+)", text, re.I)
    if m: data["Voyage"] = m.group(1)

    m = re.search(r"\b(20GP|20DC|20DV|40GP|40HC|40HQ|45HC)\b", text, re.I)
    if m: data["Size/Type"] = m.group(1).upper()

    m = re.search(r"SEAL\s*([A-Z0-9]{5,12})", text, re.I)
    if m: data["Seal No"] = m.group(1)

    m = re.search(r"EXP DATE\s*.*?(\d{2}-[A-Z]{3}-\d{2,4})", text, re.I | re.S)
    if m:
        data["EXP Date"] = m.group(1).upper()
    else:
        dates = re.findall(r"\b\d{2}-[A-Z]{3}-\d{2,4}\b", text, re.I)
        if dates: data["EXP Date"] = dates[0].upper()

    if "CMA CGM" in text.upper():
        data["Acente"] = "CMA CGM"

    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for line in lines[:20]:
        if not any(w in line.upper() for w in ["PAGE", "DELIVERY", "CMA", "B/L", "VESSEL", "VOYAGE"]):
            if len(line) > 3:
                data["Consignee"] = line
                break
    return data

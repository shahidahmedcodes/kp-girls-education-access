import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
KEYWORDS = ["enrol", "class", "gender parity", "number of government",
            "schools by", "transition", "survival"]

with pdfplumber.open(PDF_PATH) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        if page_number < 25:      # skip the table of contents
            continue
        lines = (page.extract_text() or "").split("\n")
        title = " | ".join(lines[1:3])
        if any(k in title.lower() for k in KEYWORDS):
            print(page_number, title[:140])
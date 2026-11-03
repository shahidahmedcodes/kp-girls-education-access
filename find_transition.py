import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2024_25.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        if page_number < 30:   # skip the table of contents pages
            continue
        text = page.extract_text() or ""
        if "transition" in text.lower():
            print("=" * 60)
            print("PDF page", page_number)
            for line in text.split("\n")[:14]:
                print(repr(line))
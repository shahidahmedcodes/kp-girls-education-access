import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2024_25.pdf"
TITLES = [
    "Number of Government Schools by Level & Gender",
    "Class Wise Boys Enrollment in Government Schools",
    "Class Wise Girls Enrollment in Government Schools",
]

with pdfplumber.open(PDF_PATH) as pdf:
    for title in TITLES:
        print("=" * 60)
        print(title)
        shown = False
        for page_number, page in enumerate(pdf.pages, start=1):
            if page_number < 30:   # skip the table of contents pages
                continue
            text = page.extract_text() or ""
            if title in text:
                print("found on pdf page", page_number)
                if not shown:
                    print("\n".join(text.split("\n")[:25]))
                    shown = True
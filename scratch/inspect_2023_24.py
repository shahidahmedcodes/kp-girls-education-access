import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
FULL_PAGES = [81, 135, 136, 268, 269]
TITLE_PAGES = [229, 230, 231, 232, 233, 270]

with pdfplumber.open(PDF_PATH) as pdf:
    for number in FULL_PAGES:
        page = pdf.pages[number - 1]
        lines = (page.extract_text() or "").split("\n")
        print("=" * 60)
        print("PDF page", number, "| tables found:", len(page.extract_tables()), "| lines:", len(lines))
        for line in lines[:16]:
            print(repr(line))
        print("...")
        for line in lines[-4:]:
            print(repr(line))
    print("=" * 60)
    print("Titles of the merged-district school pages:")
    for number in TITLE_PAGES:
        lines = (pdf.pages[number - 1].extract_text() or "").split("\n")
        print(number, " | ".join(lines[1:3])[:120])
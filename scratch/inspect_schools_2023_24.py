import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
PAGES = [79, 80, 81, 82, 83]

with pdfplumber.open(PDF_PATH) as pdf:
    for number in PAGES:
        page = pdf.pages[number - 1]
        lines = (page.extract_text() or "").split("\n")
        tables = page.extract_tables()
        print("=" * 60)
        print("PDF page", number, "|", " | ".join(lines[1:3])[:100], "| tables:", len(tables))
        for t_index, table in enumerate(tables):
            print("table", t_index, "has", len(table), "rows")
            for row in table[:6]:
                print(row)
            print("...")
            for row in table[-2:]:
                print(row)
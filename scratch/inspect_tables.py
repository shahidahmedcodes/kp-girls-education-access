import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2024_25.pdf"
PAGES = [73, 74, 157, 159]

with pdfplumber.open(PDF_PATH) as pdf:
    for number in PAGES:
        page = pdf.pages[number - 1]
        tables = page.extract_tables()
        print("=" * 60)
        print("PDF page", number, "| tables:", len(tables))
        for t_index, table in enumerate(tables):
            print("table", t_index, "has", len(table), "rows")
            for row in table[:6]:
                print(row)
            print("...")
            for row in table[-3:]:
                print(row)
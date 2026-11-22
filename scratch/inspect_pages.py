import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2024_25.pdf"
PAGES = [73, 74, 157, 158, 159, 160, 161, 162]


def rows_from_words(page, tol=3):
    """Rebuild table rows from word positions on the page."""
    words = page.extract_words()
    words.sort(key=lambda w: (w["top"], w["x0"]))
    rows, current, current_top = [], [], None
    for w in words:
        if current_top is None or abs(w["top"] - current_top) <= tol:
            current.append(w)
            if current_top is None:
                current_top = w["top"]
        else:
            rows.append(current)
            current, current_top = [w], w["top"]
    if current:
        rows.append(current)
    return [" ".join(x["text"] for x in sorted(r, key=lambda w: w["x0"])) for r in rows]


with pdfplumber.open(PDF_PATH) as pdf:
    for number in PAGES:
        page = pdf.pages[number - 1]
        print("=" * 60)
        print("PDF page", number, "| tables found by pdfplumber:", len(page.extract_tables()))
        rows = rows_from_words(page)
        for line in rows[:10]:
            print(line)
        print("...")
        for line in rows[-5:]:
            print(line)
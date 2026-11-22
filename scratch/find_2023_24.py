import pdfplumber

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
TITLES = [
    "gender parity index",
    "transition rate",
    "government schools by level",
    "class wise boys enrol",
    "class wise girls enrol",
]

with pdfplumber.open(PDF_PATH) as pdf:
    print("total pages:", len(pdf.pages))
    texts = [(page.extract_text() or "") for page in pdf.pages]

for title in TITLES:
    pages = [i for i, text in enumerate(texts, start=1) if title in text.lower()]
    print("=" * 60)
    print(title, "-> found on pdf pages:", pages)
    later = [p for p in pages if p >= 25]
    if later:
        print("first lines of pdf page", later[0])
        for line in texts[later[0] - 1].split("\n")[:12]:
            print(repr(line))
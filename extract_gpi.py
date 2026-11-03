import re
import pdfplumber
import pandas as pd

PDF_PATH = r"D:\edu-project\data\raw\asr_2024_25.pdf"
OUT_PATH = r"D:\edu-project\data\raw\gpi_2024_25_raw.csv"

# A pattern that matches one table row: a district name, then six numbers
pattern = re.compile(
    r"^(?P<district>[A-Za-z][A-Za-z .()/'-]+?)\s+"
    r"(?P<prim_boys>\d+\.\d)%\s+(?P<prim_girls>\d+\.\d)%\s+(?P<prim_gpi>\d+\.\d+)\s+"
    r"(?P<sec_boys>\d+\.\d)%\s+(?P<sec_girls>\d+\.\d)%\s+(?P<sec_gpi>\d+\.\d+)$"
)

rows = []
with pdfplumber.open(PDF_PATH) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        # only look at pages that contain the GPI table title
        if "Gender Parity Index (GPI) of Government Schools" not in text:
            continue
        for line in text.split("\n"):
            match = pattern.match(line.strip())
            if match:
                row = match.groupdict()
                row["pdf_page"] = page_number
                rows.append(row)

df = pd.DataFrame(rows)
print(df.head(10))
print("rows found:", len(df))
df.to_csv(OUT_PATH, index=False)
import pdfplumber
import pandas as pd
from district_names import canonical

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
GPI_PATH = r"D:\edu-project\data\processed\gpi_2024_25_clean.csv"
OUT_PATH = r"D:\edu-project\data\processed\schools_2023_24_settled.csv"

SETTLED_PAGES = {"primary": 80, "middle": 81, "high": 82, "higher_sec": 83}
MERGED_PAGES = [229, 230, 231, 232, 233]


def to_number(cell):
    """Blank cell -> 0, digits (commas allowed) -> number, anything else -> None."""
    if cell is None:
        return 0
    cell = cell.replace(",", "").strip()
    if cell == "":
        return 0
    return int(cell) if cell.isdigit() else None


def read_level(page_number):
    rows, totals = {}, None
    with pdfplumber.open(PDF_PATH) as pdf:
        for table in pdf.pages[page_number - 1].extract_tables():
            for row in table:
                if len(row) < 7:
                    continue
                name = (row[0] or "").replace("\n", " ").strip()
                numbers = [to_number(c) for c in row[1:7]]
                if not name or None in numbers:
                    continue          # header, spacer or garbled row
                record = {"boys": numbers[0], "girls": numbers[2], "total": numbers[4]}
                if name.lower() == "grand total":
                    totals = record
                else:
                    rows[name] = record
    return rows, totals


gpi = pd.read_csv(GPI_PATH)
settled = sorted(gpi[gpi["area"] == "Settled"]["district"])
schools = pd.DataFrame(index=settled)

for level, page in SETTLED_PAGES.items():
    rows, totals = read_level(page)
    df = pd.DataFrame.from_dict(rows, orient="index")
    df["district"] = [canonical(n) for n in df.index]
    unmatched = list(df.index[df["district"].isna()])
    df = df.dropna(subset=["district"]).set_index("district")
    missing = [d for d in settled if d not in df.index]
    print(f"[{level}] page {page}: districts found {len(df)} | unmatched names: {unmatched} | missing (treated as 0): {missing}")
    if totals:
        print(f"[{level}] boys: sum {int(df['boys'].sum())} vs Grand Total {totals['boys']} | "
              f"girls: sum {int(df['girls'].sum())} vs Grand Total {totals['girls']}")
    else:
        print(f"[{level}] no Grand Total row found")
    schools[f"boys_{level}"] = df["boys"].reindex(settled).fillna(0).astype(int)
    schools[f"girls_{level}"] = df["girls"].reindex(settled).fillna(0).astype(int)

levels = list(SETTLED_PAGES)
schools["boys_total"] = schools[[f"boys_{l}" for l in levels]].sum(axis=1)
schools["girls_total"] = schools[[f"girls_{l}" for l in levels]].sum(axis=1)
schools["grand_total"] = schools["boys_total"] + schools["girls_total"]
print("\nSettled districts, all schools: boys", int(schools["boys_total"].sum()),
      "| girls", int(schools["girls_total"].sum()), "| total", int(schools["grand_total"].sum()))

# ---- cross-check against the combined table on page 79 ----
check_rows = {}
with pdfplumber.open(PDF_PATH) as pdf:
    for table in pdf.pages[78].extract_tables():
        for row in table:
            if len(row) < 13:
                continue
            name = (row[0] or "").replace("\n", " ").strip()
            nums = [to_number(c) for c in row[1:13]]
            district = canonical(name) if name else None
            if district and None not in nums:
                check_rows[district] = nums
mismatch = []
for district, n in check_rows.items():
    mosque, b_prim, b_mid, b_high, b_hs, _, g_prim, g_mid, g_high, g_hs, _, _ = n
    s = schools.loc[district]
    expected = [b_prim + mosque, b_mid, b_high, b_hs, g_prim, g_mid, g_high, g_hs]
    actual = [s["boys_primary"], s["boys_middle"], s["boys_high"], s["boys_higher_sec"],
              s["girls_primary"], s["girls_middle"], s["girls_high"], s["girls_higher_sec"]]
    if expected != actual:
        mismatch.append(district)
print("\nPage 79 cross-check: districts compared:", len(check_rows),
      "| districts that differ:", mismatch)

schools.index.name = "district"
schools.to_csv(OUT_PATH)

# ---- a first look at the merged-district school pages ----
print("\n" + "=" * 60)
print("MERGED DISTRICT PAGES (for the next step)")
with pdfplumber.open(PDF_PATH) as pdf:
    for number in MERGED_PAGES:
        page = pdf.pages[number - 1]
        lines = (page.extract_text() or "").split("\n")
        tables = page.extract_tables()
        print("-" * 60)
        print("page", number, "|", " | ".join(lines[1:3])[:100], "| tables:", len(tables))
        for table in tables[:1]:
            for row in table[:5]:
                print(row)
            print("...")
            for row in table[-2:]:
                print(row)
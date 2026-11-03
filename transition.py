import re
import sys
import pdfplumber
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

PDF_PATH = r"D:\edu-project\data\raw\asr_2024_25.pdf"
GPI_PATH = r"D:\edu-project\data\processed\gpi_2024_25_clean.csv"
OUT_PATH = r"D:\edu-project\data\processed\transition_2024_25.csv"

gpi = pd.read_csv(GPI_PATH)


def make_key(name):
    name = name.lower().replace("bhettani", "bhetani").replace("bettani", "bhetani")
    return re.sub(r"[^a-z]", "", name)


CANONICAL = {make_key(d): d for d in gpi["district"]}

COLS = ["c5_boys", "c5_girls", "c5_total", "c6_boys", "c6_girls", "c6_total",
        "rep_boys", "rep_girls", "rep_total", "rate_boys", "rate_girls", "rate_total"]

pattern = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z .()/'-]*?)\s+"
    + r"\s+".join(rf"(?P<{c}>[\d,]+)" for c in COLS[:9]) + r"\s+"
    + r"\s+".join(rf"(?P<{c}>\d+\.\d+)%" for c in COLS[9:])
    + r"$"
)


def clean_name(text):
    text = text.replace("(cid:425)", "tt").strip()
    if "Area " in text:                      # garbled 'Settled / Merged Area' label
        text = text.split("Area ")[-1]
    text = re.sub(r"^(settled|merged)\s+", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


rows = []
with pdfplumber.open(PDF_PATH) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        if page_number < 30:                 # skip the table of contents
            continue
        text = page.extract_text() or ""
        if "Transition Rate" not in text or "Class-5 (2023-24)" not in text:
            continue
        for line in text.split("\n"):
            match = pattern.match(line.strip())
            if match:
                record = match.groupdict()
                record["name"] = clean_name(record["name"])
                record["pdf_page"] = page_number
                rows.append(record)

if not rows:
    print("No rows matched. Check the title text and the row pattern.")
    sys.exit()

raw = pd.DataFrame(rows)
print("rows matched:", len(raw), "| pages:", sorted(raw["pdf_page"].unique()))

for col in COLS:
    raw[col] = pd.to_numeric(raw[col].astype(str).str.replace(",", ""))

is_total = raw["name"].str.lower().str.contains("total")
totals = raw[is_total]
districts = raw[~is_total].copy()
districts["key"] = districts["name"].apply(make_key)
districts["district"] = districts["key"].map(CANONICAL)
districts = districts.drop_duplicates("key")

print("unmatched names:", districts[districts["district"].isna()]["name"].tolist())
districts = districts.dropna(subset=["district"])
print("districts found:", len(districts), "| missing:", sorted(set(gpi["district"]) - set(districts["district"])))

# Check 1: recompute the transition rate from the counts
for sex in ["boys", "girls"]:
    calc = (districts[f"c6_{sex}"] - districts[f"rep_{sex}"]) / districts[f"c5_{sex}"] * 100
    diff = (calc - districts[f"rate_{sex}"]).abs()
    print(f"[{sex}] districts where recomputed rate differs by more than 0.1:",
          districts[diff > 0.1]["district"].tolist())

# Check 2: do the districts add up to the report's Total rows?
for page_number, group in districts.groupby("pdf_page"):
    total_row = totals[(totals["pdf_page"] == page_number) & (totals["name"].str.lower() == "total")]
    if len(total_row):
        print(f"page {page_number}: districts sum class-5 boys =", int(group["c5_boys"].sum()),
              "| report Total =", int(total_row["c5_boys"].iloc[0]))
grand = totals[totals["name"].str.lower() == "grand total"]
if len(grand):
    print("all districts: class-5 boys =", int(districts["c5_boys"].sum()),
          "| report Grand Total =", int(grand["c5_boys"].iloc[0]))

# First look at the answers
districts["rate_gap"] = (districts["rate_boys"] - districts["rate_girls"]).round(1)
print("\nMedian transition rate: boys", districts["rate_boys"].median(), "| girls", districts["rate_girls"].median())
print("Districts where girls' rate is below boys':", int((districts["rate_gap"] > 0).sum()), "of", len(districts))
cols = ["district", "rate_boys", "rate_girls", "rate_gap"]
print("\nLargest boy-girl gap in transition rate:")
print(districts.sort_values("rate_gap", ascending=False)[cols].head(8).to_string(index=False))
print("\nLowest girls' transition rate:")
print(districts.sort_values("rate_girls")[cols].head(5).to_string(index=False))

districts.drop(columns=["key"]).to_csv(OUT_PATH, index=False)
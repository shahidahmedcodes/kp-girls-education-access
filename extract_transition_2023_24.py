import re
import pdfplumber
import pandas as pd
from district_names import canonical

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
DIR = r"D:\edu-project\data\processed"

COLS = ["c6_boys", "c6_girls", "c6_total", "rep_boys", "rep_girls", "rep_total",
        "c5_boys", "c5_girls", "c5_total", "pub_boys", "pub_girls", "pub_total"]

pattern = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z .()/'-]*?)\s+"
    + r"\s+".join(rf"(?P<{c}>[\d,]+)" for c in COLS[:9]) + r"\s+"
    + r"\s+".join(rf"(?P<{c}>\d+(?:\.\d+)?)%" for c in COLS[9:])
    + r"$"
)


def read_page(page_number):
    with pdfplumber.open(PDF_PATH) as pdf:
        text = pdf.pages[page_number - 1].extract_text() or ""
    rows = []
    for line in text.split("\n"):
        match = pattern.match(line.strip())
        if match:
            record = match.groupdict()
            for c in COLS:
                record[c] = float(record[c].replace(",", ""))
            rows.append(record)
    return pd.DataFrame(rows)


frames = []
for page, area in [(46, "Settled"), (226, "Merged")]:
    raw = read_page(page)
    if raw.empty:
        raise SystemExit(f"No rows matched on page {page}. Stopping.")
    is_total = raw["name"].str.lower().str.contains("total")
    totals = raw[is_total]
    d = raw[~is_total].copy()
    d["district"] = d["name"].apply(canonical)
    unmatched = d[d["district"].isna()]["name"].tolist()
    d = d.dropna(subset=["district"]).drop_duplicates("district")
    d["area"] = area
    print(f"[{area}] units: {len(d)} | unmatched names: {unmatched}")
    if len(totals):
        for _, row in totals.iterrows():
            print(f"[{area}] class-5 boys: sum of units {int(d['c5_boys'].sum())} | row '{row['name']}': {int(row['c5_boys'])}")
            print(f"[{area}] class-5 girls: sum of units {int(d['c5_girls'].sum())} | row '{row['name']}': {int(row['c5_girls'])}")
    else:
        print(f"[{area}] no Total row found on the page")
    frames.append(d)

d = pd.concat(frames, ignore_index=True)

# Check 1: recompute the rates from the counts; the report rounds to whole percentages
for sex in ["boys", "girls", "total"]:
    d[f"rate_{sex}"] = ((d[f"c6_{sex}"] - d[f"rep_{sex}"]) / d[f"c5_{sex}"] * 100).round(2)
    diff = (d[f"rate_{sex}"] - d[f"pub_{sex}"]).abs()
    print(f"[{sex}] units where recomputed rate differs from published by more than 0.6:",
          d[diff > 0.6]["district"].tolist())

# Check 2: class-6 counts here should equal class-6 enrolment in the enrolment table
enrol = pd.read_csv(DIR + r"\enrolment_2023_24.csv")
cls6 = enrol.pivot_table(index="district", columns="sex", values="class_6", aggfunc="sum")
d23 = d.set_index("district")
for sex in ["boys", "girls"]:
    mismatch = d23.index[(d23[f"c6_{sex}"] != cls6[sex].reindex(d23.index))]
    print(f"[{sex}] units where class 6 differs from the enrolment table:", list(mismatch))

# Check 3: class 5 (2023-24) in the 2024-25 transition table should equal class 5 in this year's enrolment
t24 = pd.read_csv(DIR + r"\transition_2024_25.csv")
t24["district"] = t24["district"].where(~t24["district"].str.startswith("South Waziristan"), "South Waziristan")
cols24 = ["c5_boys", "c5_girls", "c6_boys", "c6_girls", "rep_boys", "rep_girls"]
t24g = t24.groupby("district")[cols24].sum()
cls5 = enrol.pivot_table(index="district", columns="sex", values="class_5", aggfunc="sum")
for sex in ["boys", "girls"]:
    mismatch = t24g.index[(t24g[f"c5_{sex}"] != cls5[sex].reindex(t24g.index))]
    print(f"[{sex}] units where 2024-25 class-5 count differs from the 2023-24 class-5 enrolment:", list(mismatch))

# First look: 2023-24 against 2024-25 on the same units
for sex in ["boys", "girls"]:
    t24g[f"rate_{sex}"] = (t24g[f"c6_{sex}"] - t24g[f"rep_{sex}"]) / t24g[f"c5_{sex}"] * 100
common = d23.index.intersection(t24g.index)
print("\nunits in both years:", len(common))
print("Median transition rate (class 5 to 6):")
print(pd.DataFrame({
    "2023-24": [d23.loc[common, "rate_boys"].median(), d23.loc[common, "rate_girls"].median()],
    "2024-25": [t24g.loc[common, "rate_boys"].median(), t24g.loc[common, "rate_girls"].median()],
}, index=["boys", "girls"]).round(1))
change = (t24g.loc[common, "rate_girls"] - d23.loc[common, "rate_girls"]).round(1).sort_values()
print("\nGirls' rate, 2024-25 minus 2023-24 (percentage points):")
print("Biggest falls:")
print(change.head(5))
print("Biggest rises:")
print(change.tail(5))

d.drop(columns=["name"]).to_csv(DIR + r"\transition_2023_24.csv", index=False)
import pdfplumber
import pandas as pd
from district_names import canonical

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
DIR = r"D:\edu-project\data\processed"
GPI_PATH = DIR + r"\gpi_2024_25_clean.csv"
MERGED_PAGES = [229, 230]

# Merged-district totals (boys, girls, total) from the province-level table on page 205
KNOWN = {
    "primary": (2846, 2242, 5088),
    "middle": (458, 389, 847),
    "high": (314, 108, 422),
    "higher_sec": (27, 10, 37),
}


def to_number(cell):
    """Blank or '-' -> 0, digits (commas allowed) -> number, anything else -> None."""
    if cell is None:
        return 0
    cell = str(cell).replace(",", "").strip()
    if cell in ("", "-"):
        return 0
    return int(cell) if cell.isdigit() else None


# ---- 1. read the merged-district pages in order; a table ends at each 'Grand Total' row ----
groups, current = [], {}
with pdfplumber.open(PDF_PATH) as pdf:
    for page_number in MERGED_PAGES:
        for table in pdf.pages[page_number - 1].extract_tables():
            for row in table:
                if len(row) < 6:
                    continue
                name = (row[0] or "").replace("\n", " ").strip()
                if not name:
                    continue
                nums = [to_number(row[1]), to_number(row[3]), to_number(row[5])]
                if None in nums:
                    continue
                if name.lower() == "grand total":
                    groups.append((current, tuple(nums)))
                    current = {}
                else:
                    district = canonical(name)
                    if district:
                        current[district] = nums
print("tables closed by a Grand Total row:", len(groups), "| leftover rows:", len(current))

levels = {}
for rows, totals in groups:
    level = next((l for l, k in KNOWN.items() if k == totals), None)
    if level is None:
        print("  unrecognised Grand Total", totals, "with", len(rows), "rows (ignored)")
        continue
    levels[level] = rows
    print(f"  {level}: Grand Total {totals} with {len(rows)} districts")
if len(levels) < 4:
    raise SystemExit("Not all four levels were found: " + str(sorted(set(KNOWN) - set(levels))))

# ---- 2. build the merged table (13 comparison units) ----
gpi = pd.read_csv(GPI_PATH)
units = sorted({"South Waziristan" if d.startswith("South Waziristan") else d
                for d in gpi[gpi["area"] == "Merged"]["district"]})
merged = pd.DataFrame(index=units)
for level, rows in levels.items():
    df = pd.DataFrame.from_dict(rows, orient="index", columns=["boys", "girls", "total"])
    missing = [u for u in units if u not in df.index]
    bad = df.index[(df["boys"] + df["girls"]) != df["total"]].tolist()
    print(f"[{level}] districts: {len(df)} | missing (treated as 0): {missing} | boys+girls != total: {bad}")
    k = KNOWN[level]
    print(f"[{level}] boys sum {int(df['boys'].sum())} vs {k[0]} | girls sum {int(df['girls'].sum())} vs {k[1]}")
    merged[f"boys_{level}"] = df["boys"].reindex(units).fillna(0).astype(int)
    merged[f"girls_{level}"] = df["girls"].reindex(units).fillna(0).astype(int)

lv = list(KNOWN)
merged["boys_total"] = merged[[f"boys_{l}" for l in lv]].sum(axis=1)
merged["girls_total"] = merged[[f"girls_{l}" for l in lv]].sum(axis=1)
merged["grand_total"] = merged["boys_total"] + merged["girls_total"]
merged["area"] = "Merged"

# ---- 3. join with the settled districts: all 41 units ----
settled = pd.read_csv(DIR + r"\schools_2023_24_settled.csv").set_index("district")
settled["area"] = "Settled"
y23 = pd.concat([settled, merged])
y23.index.name = "district"
print("\nunits:", len(y23), "| boys", int(y23["boys_total"].sum()),
      "| girls", int(y23["girls_total"].sum()), "| total", int(y23["grand_total"].sum()))
y23.to_csv(DIR + r"\schools_2023_24.csv")

# ---- 4. compare with 2024-25 on the same units ----
y24 = pd.read_csv(DIR + r"\schools_2024_25.csv")
y24["district"] = y24["district"].where(~y24["district"].str.startswith("South Waziristan"), "South Waziristan")
y24 = y24.groupby("district").sum(numeric_only=True)
common = y23.index.intersection(y24.index)
print("units in both years:", len(common))

ratio23 = (y23.loc[common, "girls_middle"] / y23.loc[common, "boys_middle"]).median()
ratio24 = (y24.loc[common, "girls_middle"] / y24.loc[common, "boys_middle"]).median()
print("Median girls-per-boy MIDDLE SCHOOLS: 2023-24", round(ratio23, 2), "| 2024-25", round(ratio24, 2))

change = (y24.loc[common, ["boys_middle", "girls_middle"]] - y23.loc[common, ["boys_middle", "girls_middle"]])
change["total_change"] = change.sum(axis=1)
print("\nBiggest changes in the number of middle schools (2024-25 minus 2023-24):")
print(change.reindex(change["total_change"].abs().sort_values(ascending=False).index).head(6))
import os
import pandas as pd

RAW_PATH = r"D:\edu-project\data\raw\gpi_2024_25_raw.csv"
CLEAN_PATH = r"D:\edu-project\data\processed\gpi_2024_25_clean.csv"
TOTALS_PATH = r"D:\edu-project\data\processed\gpi_2024_25_totals.csv"

df = pd.read_csv(RAW_PATH)

# 1. Remove layout words stuck to the first district name on a page
df["district"] = (
    df["district"]
    .str.replace("Settled ", "", regex=False)
    .str.replace("Meraged Area ", "", regex=False)
    .str.strip()
)

# 2. Fix capitalisation (PESHAWAR -> Peshawar)
df["district"] = df["district"].apply(lambda s: s.title() if s.isupper() else s)

# 3. Add the area: settled districts are on page 51, merged areas on pages 52-53
df["area"] = df["pdf_page"].apply(lambda p: "Settled" if p == 51 else "Merged")

# 4. Make sure the number columns are numbers
num_cols = ["prim_boys", "prim_girls", "prim_gpi", "sec_boys", "sec_girls", "sec_gpi"]
df[num_cols] = df[num_cols].apply(pd.to_numeric)

# 5. Check that the repeated merged-area page (53) matches page 52
p52 = df[df["pdf_page"] == 52].drop(columns="pdf_page").reset_index(drop=True)
p53 = df[df["pdf_page"] == 53].drop(columns="pdf_page").reset_index(drop=True)
print("Pages 52 and 53 identical:", p52.equals(p53))

# 6. Separate the Total rows from the districts and remove duplicates
is_total = df["district"].isin(["Total", "Grand Total"])
totals = df[is_total]
districts = df[~is_total].drop_duplicates(subset="district").copy()
districts["report_year"] = "2024-25"

# 7. Data quality check: does girls / boys match the published GPI?
districts["prim_gpi_calc"] = (districts["prim_girls"] / districts["prim_boys"]).round(2)
districts["sec_gpi_calc"] = (districts["sec_girls"] / districts["sec_boys"]).round(2)
districts["prim_gpi_diff"] = (districts["prim_gpi_calc"] - districts["prim_gpi"]).abs()
districts["sec_gpi_diff"] = (districts["sec_gpi_calc"] - districts["sec_gpi"]).abs()
flagged = districts[(districts["prim_gpi_diff"] > 0.03) | (districts["sec_gpi_diff"] > 0.03)]
print("Rows where calculated GPI differs by more than 0.03:", len(flagged))
print(flagged[["district", "prim_gpi", "prim_gpi_calc", "sec_gpi", "sec_gpi_calc"]])

# 8. Summary
print("Districts:", len(districts))
print(districts["area"].value_counts())
cols = ["district", "area", "sec_gpi"]
print("Lowest secondary GPI:")
print(districts.sort_values("sec_gpi")[cols].head(5))
print("Highest secondary GPI:")
print(districts.sort_values("sec_gpi")[cols].tail(5))

# 9. Save
os.makedirs(os.path.dirname(CLEAN_PATH), exist_ok=True)
districts.to_csv(CLEAN_PATH, index=False)
totals.to_csv(TOTALS_PATH, index=False)
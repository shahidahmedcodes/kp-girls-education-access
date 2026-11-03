import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

GPI = r"D:\edu-project\data\processed\gpi_2024_25_clean.csv"
MID = r"D:\edu-project\data\processed\middle_preview_2024_25.csv"
OUT = r"D:\edu-project\data\processed\district_summary_2024_25.csv"

gpi = pd.read_csv(GPI)[["district", "area", "prim_gpi", "sec_gpi"]]
mid = pd.read_csv(MID)

df = gpi.merge(mid, on="district", how="inner", validate="one_to_one")
print("rows after merge:", len(df))

# 1. Do our classes 6-8 ratios agree with the report's published GPI (classes 6-10)?
corr = df["girls_per_boy_enrol"].corr(df["sec_gpi"])
print("Correlation, our classes 6-8 ratio vs published secondary GPI:", round(corr, 3))
df["gap"] = (df["girls_per_boy_enrol"] - df["sec_gpi"]).round(2)
biggest = df.reindex(df["gap"].abs().sort_values(ascending=False).index)
print("\nDistricts where the two measures differ most:")
print(biggest[["district", "area", "girls_per_boy_enrol", "sec_gpi", "gap"]].head(8))

# 2. Do districts with relatively more girls' middle schools have higher parity?
c2 = df["girls_per_boy_schools"].corr(df["girls_per_boy_enrol"])
print("\nCorrelation, girls-per-boy middle SCHOOLS vs girls-per-boy ENROLMENT:", round(c2, 3))
print(df.groupby("area")[["girls_per_boy_enrol", "girls_per_boy_schools"]].median().round(2))

df.to_csv(OUT, index=False)
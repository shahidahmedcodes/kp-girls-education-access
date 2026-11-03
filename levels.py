import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

ENROL = r"D:\edu-project\data\processed\enrolment_2024_25.csv"
OUT = r"D:\edu-project\data\processed\levels_2024_25.csv"

df = pd.read_csv(ENROL)

levels = {
    "primary_1_5": ["class_1", "class_2", "class_3", "class_4", "class_5"],
    "middle_6_8": ["class_6", "class_7", "class_8"],
    "high_9_10": ["class_9", "class_10"],
    "higher_sec_11_12": ["class_11", "class_12"],
}
for name, cols in levels.items():
    df[name] = df[cols].sum(axis=1)

boys = df[df["sex"] == "boys"].set_index("district")
girls = df[df["sex"] == "girls"].set_index("district")

ratios = pd.DataFrame(index=boys.index)
for name in levels:
    ratios[name] = (girls[name] / boys[name]).round(2)
ratios = ratios.replace([float("inf")], float("nan"))
ratios["drop_primary_to_middle"] = (ratios["primary_1_5"] - ratios["middle_6_8"]).round(2)

print("Median girls-per-boy ratio by level:")
print(ratios[list(levels)].median().round(2))

print("\nDistricts with the biggest drop from primary to middle:")
print(ratios.sort_values("drop_primary_to_middle", ascending=False).head(8))

ratios.to_csv(OUT)
import re
import pdfplumber
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

PDF_PATH = r"D:\edu-project\data\raw\asr_2023_24.pdf"
DIR = r"D:\edu-project\data\processed"

COLS = ["nursery", "prep", "class_1", "class_2", "class_3", "class_4", "class_5", "sub_nursery_5",
        "class_6", "class_7", "class_8", "sub_6_8", "class_9", "class_10", "sub_9_10",
        "class_11", "class_12", "sub_11_12", "grand_total"]
CLASS_COLS = ["nursery", "prep"] + [f"class_{n}" for n in range(1, 13)]

ALIASES = {
    "abbottabad": "Abbottabad", "bannu": "Bannu", "battagram": "Battagram",
    "buner": "Bunner", "bunner": "Bunner", "charsadda": "Charsadda",
    "chitrallower": "Chitral Lower", "lowerchitral": "Chitral Lower",
    "chitralupper": "Chitral Upper", "upperchitral": "Chitral Upper",
    "dikhan": "Dera Ismail Khan", "deraismailkhan": "Dera Ismail Khan",
    "dirbala": "Dir Upper", "dirpayan": "Dir Lower", "hangu": "Hangu", "haripur": "Haripur",
    "karak": "Karak", "kohat": "Kohat",
    "kolaipalas": "Kolai Palas", "kolaipallas": "Kolai Palas",
    "lakki": "Lakki Marwat", "lakkimarwat": "Lakki Marwat",
    "lowerkohistan": "Kohistan Lower", "kohistanlower": "Kohistan Lower",
    "upperkohistan": "Kohistan Upper", "kohistanupper": "Kohistan Upper",
    "malakand": "Malakand", "mansehra": "Mansehra", "mardan": "Mardan",
    "nowshehra": "Nowshera", "nowshera": "Nowshera", "peshawar": "Peshawar",
    "shangla": "Shangla", "swabi": "Swabi", "swat": "Swat", "tank": "Tank", "torghar": "Torghar",
    "bajaur": "Bajaur", "khyber": "Khyber", "kurram": "Kurram", "kurraam": "Kurram",
    "mohmand": "Mohmand", "northwaziristan": "North Waziristan", "orakzai": "Orakzai",
    "southwaziristan": "South Waziristan",
    "subdivbettani": "SD Bhetani (Lakki Marwat)", "subdivbhetani": "SD Bhetani (Lakki Marwat)",
    "subdivdarraadamkhel": "SD Dara Adam Khel (Kohat)", "subdivdaraadamkhel": "SD Dara Adam Khel (Kohat)",
    "subdivdrazanda": "SD Darazinda (Dera Ismail Khan)", "subdivdarazinda": "SD Darazinda (Dera Ismail Khan)",
    "subdivhassankhel": "SD Hassan Khel (Peshawar)", "subdivhasankhel": "SD Hassan Khel (Peshawar)",
    "subdivjandola": "SD Jandola (Tank)", "subdivwazir": "SD Wazir (Bannu)",
}

ROW = re.compile(r"^(?P<name>[A-Za-z][A-Za-z .()/'-]*?)\s+(?P<nums>(?:\d+\s+){18}\d+)$")


def make_key(name):
    return re.sub(r"[^a-z]", "", name.lower())


def read_tables(page_number):
    """Read the rows of a page; start a new table after each 'Grand Total' row."""
    with pdfplumber.open(PDF_PATH) as pdf:
        text = pdf.pages[page_number - 1].extract_text() or ""
    tables, current = [], []
    for line in text.split("\n"):
        match = ROW.match(line.strip())
        if not match:
            continue
        record = dict(zip(COLS, [int(x) for x in match.group("nums").split()]))
        record["name"] = match.group("name").strip()
        current.append(record)
        if record["name"].lower() == "grand total":
            tables.append(pd.DataFrame(current))
            current = []
    if current:
        tables.append(pd.DataFrame(current))
    return tables


def tidy(table, label):
    is_total = table["name"].str.lower() == "grand total"
    total_row = table[is_total]
    d = table[~is_total].copy()
    d["district"] = d["name"].apply(lambda n: ALIASES.get(make_key(n)))
    unmatched = d[d["district"].isna()]["name"].tolist()
    d = d.dropna(subset=["district"]).drop_duplicates("district")

    bad = d[
        (d[CLASS_COLS[:7]].sum(axis=1) != d["sub_nursery_5"])
        | (d[["class_6", "class_7", "class_8"]].sum(axis=1) != d["sub_6_8"])
        | (d[["class_9", "class_10"]].sum(axis=1) != d["sub_9_10"])
        | (d[["class_11", "class_12"]].sum(axis=1) != d["sub_11_12"])
        | (d[["sub_nursery_5", "sub_6_8", "sub_9_10", "sub_11_12"]].sum(axis=1) != d["grand_total"])
    ]
    print(f"[{label}] units: {len(d)} | unmatched names: {unmatched}")
    print(f"[{label}] rows failing their own subtotals: {bad['district'].tolist()}")
    if len(total_row):
        print(f"[{label}] sum of units: {int(d['grand_total'].sum())} | Grand Total row: {int(total_row['grand_total'].iloc[0])}")
    return d


settled_boys = tidy(read_tables(135)[0], "settled boys")
settled_girls = tidy(read_tables(136)[0], "settled girls")

t268 = read_tables(268)
print("page 268 tables found:", len(t268))
if len(t268) < 2:
    raise SystemExit("Expected a boys table and a girls table on page 268. Stopping.")
merged_boys = tidy(t268[0], "merged boys")
merged_girls = tidy(t268[1], "merged girls")
merged_total = tidy(read_tables(269)[0], "merged boys+girls")

gap = (merged_boys.set_index("district")["grand_total"]
       + merged_girls.set_index("district")["grand_total"]
       - merged_total.set_index("district")["grand_total"])
print("merged: districts where boys + girls differs from the page-269 total:", gap[gap != 0].index.tolist())

frames = []
for df, area, sex in [(settled_boys, "Settled", "boys"), (settled_girls, "Settled", "girls"),
                      (merged_boys, "Merged", "boys"), (merged_girls, "Merged", "girls")]:
    part = df[["district"] + CLASS_COLS + ["grand_total"]].copy()
    part["area"] = area
    part["sex"] = sex
    frames.append(part)
y23 = pd.concat(frames, ignore_index=True)
y23.to_csv(DIR + r"\enrolment_2023_24.csv", index=False)

# ---- compare with 2024-25 on the same 41 units ----
LEVELS = {
    "primary": ["class_1", "class_2", "class_3", "class_4", "class_5"],
    "middle": ["class_6", "class_7", "class_8"],
    "high": ["class_9", "class_10"],
    "higher_sec": ["class_11", "class_12"],
}


def girls_per_boy(df):
    df = df.copy()
    for name, cols in LEVELS.items():
        df[name] = df[cols].sum(axis=1)
    boys = df[df["sex"] == "boys"].set_index("district")[list(LEVELS)]
    girls = df[df["sex"] == "girls"].set_index("district")[list(LEVELS)]
    return (girls / boys).replace([float("inf")], float("nan")).round(2)


y24 = pd.read_csv(DIR + r"\enrolment_2024_25.csv")
y24["district"] = y24["district"].where(~y24["district"].str.startswith("South Waziristan"), "South Waziristan")
y24 = y24.groupby(["district", "sex"], as_index=False)[CLASS_COLS].sum()

r23, r24 = girls_per_boy(y23), girls_per_boy(y24)
common = r23.index.intersection(r24.index)
print("\nunits in 2023-24:", len(r23), "| in 2024-25:", len(r24), "| in both:", len(common))
print("in only one year:", sorted(set(r23.index) ^ set(r24.index)))

summary = pd.DataFrame({"2023-24": r23.loc[common].median(), "2024-25": r24.loc[common].median()}).round(2)
print("\nMedian girls-per-boy ratio by level:")
print(summary)

change = (r24.loc[common, "middle"] - r23.loc[common, "middle"]).round(2).sort_values()
print("\nMiddle (classes 6-8) ratio, 2024-25 minus 2023-24:")
print("Biggest falls:")
print(change.head(5))
print("Biggest rises:")
print(change.tail(5))
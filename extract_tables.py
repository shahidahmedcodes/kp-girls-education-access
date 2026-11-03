import re
import pdfplumber
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

PDF_PATH = r"D:\edu-project\data\raw\asr_2024_25.pdf"
GPI_PATH = r"D:\edu-project\data\processed\gpi_2024_25_clean.csv"
OUT_DIR = r"D:\edu-project\data\processed"

SCHOOL_PAGES = [73, 74]
BOYS_PAGES = [157, 158, 159]
GIRLS_PAGES = [160, 161, 162]

SCHOOL_COLS = [
    "boys_primary", "boys_middle", "boys_high", "boys_higher_sec", "boys_total",
    "girls_primary", "girls_middle", "girls_high", "girls_higher_sec", "girls_total",
    "grand_total",
]
CLASS_COLS = ["nursery", "prep"] + [f"class_{n}" for n in range(1, 13)] + ["grand_total"]

gpi = pd.read_csv(GPI_PATH)


def clean_name(text):
    """Fix the font glitch and line breaks in district names."""
    text = text.replace("(cid:425)", "tt").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def make_key(name):
    """A simplified version of a name, used only for matching."""
    name = name.lower().replace("bhettani", "bhetani").replace("bettani", "bhetani")
    return re.sub(r"[^a-z]", "", name)


CANONICAL = {make_key(d): d for d in gpi["district"]}


def to_number(cell):
    """Blank cell -> 0, digits -> number, anything else -> None (garbled)."""
    if cell is None or cell.strip() == "":
        return 0
    if cell.strip().isdigit():
        return int(cell.strip())
    return None


def read_pages(pages, columns):
    district_rows, total_rows, orphan_rows = [], [], []
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_number in pages:
            for table in pdf.pages[page_number - 1].extract_tables():
                for row in table:
                    if len(row) < 2 + len(columns):
                        continue
                    name = clean_name(row[1] or row[0] or "")
                    if name.lower() in ("settled", "merged areas", "merged area"):
                        name = ""
                    cells = row[2:2 + len(columns)]
                    numbers = [to_number(c) for c in cells]
                    filled = sum(1 for c in cells if c and c.strip())
                    if None in numbers or filled < 5:
                        continue  # header, spacer or garbled row
                    record = dict(zip(columns, numbers))
                    record.update(name=name, filled=filled, pdf_page=page_number)
                    if name == "":
                        orphan_rows.append(record)      # numbers but no name
                    elif "total" in name.lower():
                        total_rows.append(record)
                    else:
                        district_rows.append(record)
    return pd.DataFrame(district_rows), pd.DataFrame(total_rows), pd.DataFrame(orphan_rows)


def report_total(totals):
    row = totals[totals["name"] == "Grand Total"]
    return int(row["grand_total"].iloc[0]) if len(row) else None


def tidy(frame, totals, orphans, label):
    frame = frame.copy()
    frame["key"] = frame["name"].apply(make_key)
    frame = frame.sort_values("filled", ascending=False).drop_duplicates("key")
    frame["district"] = frame["key"].map(CANONICAL)
    unmatched = frame[frame["district"].isna()]["name"].tolist()
    frame = frame.dropna(subset=["district"])
    missing = sorted(set(gpi["district"]) - set(frame["district"]))

    # Guided repair: one district missing + one nameless row that fits the gap exactly
    target = report_total(totals)
    if len(missing) == 1 and len(orphans) > 0 and target is not None:
        gap = target - int(frame["grand_total"].sum())
        candidates = orphans[orphans["grand_total"] == gap].drop_duplicates(subset="grand_total")
        if len(candidates) == 1:
            new = pd.DataFrame([candidates.iloc[0].to_dict()])
            new["district"] = missing[0]
            new["key"] = make_key(missing[0])
            frame = pd.concat([frame, new], ignore_index=True)
            print(f"[{label}] REPAIR: nameless row (total {gap}) assigned to {missing[0]} because it matches the gap exactly")
            missing = sorted(set(gpi["district"]) - set(frame["district"]))

    print(f"[{label}] districts found: {len(frame)} | unmatched names: {unmatched} | missing: {missing}")
    return frame.sort_values("district").reset_index(drop=True)


def check_schools(df, totals):
    boys_sum = df[["boys_primary", "boys_middle", "boys_high", "boys_higher_sec"]].sum(axis=1)
    girls_sum = df[["girls_primary", "girls_middle", "girls_high", "girls_higher_sec"]].sum(axis=1)
    ok = (boys_sum == df["boys_total"]) & (girls_sum == df["girls_total"]) \
        & (df["boys_total"] + df["girls_total"] == df["grand_total"])
    print("[schools] rows whose numbers do not add up:", df[~ok]["district"].tolist())
    print("[schools] sum of districts:", int(df["grand_total"].sum()), "| report Grand Total:", report_total(totals))


def check_enrolment(df, totals, label):
    class_sum = df[CLASS_COLS[:-1]].sum(axis=1)
    print(f"[{label}] rows where classes do not add to the row total:", df[class_sum != df["grand_total"]]["district"].tolist())
    print(f"[{label}] sum of districts:", int(df["grand_total"].sum()), "| report Grand Total:", report_total(totals))


# ---- run everything ----
s_raw, s_tot, s_orph = read_pages(SCHOOL_PAGES, SCHOOL_COLS)
b_raw, b_tot, b_orph = read_pages(BOYS_PAGES, CLASS_COLS)
g_raw, g_tot, g_orph = read_pages(GIRLS_PAGES, CLASS_COLS)

schools = tidy(s_raw, s_tot, s_orph, "schools")
boys = tidy(b_raw, b_tot, b_orph, "boys enrolment")
girls = tidy(g_raw, g_tot, g_orph, "girls enrolment")

check_schools(schools, s_tot)
check_enrolment(boys, b_tot, "boys enrolment")
check_enrolment(girls, g_tot, "girls enrolment")

# ---- first look at the answers (classes 6-8 = middle school) ----
mid_boys = boys.set_index("district")[["class_6", "class_7", "class_8"]].sum(axis=1)
mid_girls = girls.set_index("district")[["class_6", "class_7", "class_8"]].sum(axis=1)
preview = pd.DataFrame({"boys_6_8": mid_boys, "girls_6_8": mid_girls})
preview["girls_per_boy_enrol"] = (preview["girls_6_8"] / preview["boys_6_8"]).round(2)
s = schools.set_index("district")
preview["boys_mid_schools"] = s["boys_middle"]
preview["girls_mid_schools"] = s["girls_middle"]
preview["girls_per_boy_schools"] = (preview["girls_mid_schools"] / preview["boys_mid_schools"]).round(2)

ranked = preview.sort_values("girls_per_boy_enrol")
print("\nLowest girls-per-boy enrolment in classes 6-8:")
print(ranked.head(8))
print("\nHighest:")
print(ranked.tail(5))

# ---- save ----
boys["sex"] = "boys"
girls["sex"] = "girls"
keep = ["district", "sex"] + CLASS_COLS
pd.concat([boys[keep], girls[keep]]).to_csv(OUT_DIR + r"\enrolment_2024_25.csv", index=False)
schools[["district"] + SCHOOL_COLS].to_csv(OUT_DIR + r"\schools_2024_25.csv", index=False)
preview.to_csv(OUT_DIR + r"\middle_preview_2024_25.csv")
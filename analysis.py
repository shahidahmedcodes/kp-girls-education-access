import os
import numpy as np
import pandas as pd
from sqlalchemy import text
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from db_utils import get_engine

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

OUT = r"D:\edu-project\data\processed"
FIG = r"D:\edu-project\figures"
os.makedirs(FIG, exist_ok=True)

engine = get_engine()
with engine.connect() as conn:
    df = pd.read_sql(text("SELECT * FROM v_unit_year"), conn)
skip = ["unit", "area", "report_year", "low_base", "above_100"]
for c in df.columns:
    if c not in skip:
        df[c] = pd.to_numeric(df[c])
df["merged"] = (df["area"] == "Merged").astype(float)
df.to_csv(OUT + r"\v_unit_year.csv", index=False)

rng = np.random.default_rng(42)


def spearman(x, y):
    """Spearman correlation = ordinary correlation of the ranks (no scipy needed)."""
    rx = pd.Series(np.asarray(x, dtype=float)).rank().values
    ry = pd.Series(np.asarray(y, dtype=float)).rank().values
    if rx.std() == 0 or ry.std() == 0:
        return np.nan
    return float(np.corrcoef(rx, ry)[0, 1])


def boot_ci(x, y, n=3000):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    stats = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        stats.append(spearman(x[i], y[i]))
    return np.nanpercentile(stats, [2.5, 97.5])


def ols(target, predictors, data):
    X = np.column_stack([np.ones(len(data))] + [data[p].values for p in predictors])
    y = data[target].values
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    r2 = 1 - ((y - X @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return beta, r2


for year, d in df.groupby("report_year"):
    print("\n" + "=" * 70)
    print(f"{year}: {len(d)} units")

    ok = d[~d["low_base"]]
    pairs = [
        ("girls-per-boy middle SCHOOLS vs middle ENROLMENT", "schools_gpb_middle", "gpb_middle", d),
        ("primary vs middle enrolment ratio", "gpb_primary", "gpb_middle", d),
        (f"middle schools ratio vs girls' transition ({len(ok)} units, low-base removed)",
         "schools_gpb_middle", "trans_girls", ok),
    ]
    for label, a, b, data in pairs:
        lo, hi = boot_ci(data[a], data[b])
        print(f"Spearman {label}: {spearman(data[a], data[b]):.2f}  (95% bootstrap interval {lo:.2f} to {hi:.2f})")

    print("\nMedians by area:")
    print(d.groupby("area")[["gpb_primary", "gpb_middle", "gpb_high", "schools_gpb_middle", "trans_girls"]]
          .median().round(2))

    print("\nRegression of the middle enrolment ratio (R-squared = share of variation explained):")
    for label, preds in [("schools ratio only", ["schools_gpb_middle"]),
                         ("merged-area flag only", ["merged"]),
                         ("both", ["schools_gpb_middle", "merged"])]:
        beta, r2 = ols("gpb_middle", preds, d)
        print(f"  {label}: R2 = {r2:.2f} | coefficients (intercept first) = {np.round(beta, 2)}")

# ---- chart 1: schools ratio against enrolment ratio, 2024-25 ----
d = df[df["report_year"] == "2024-25"]
fig, ax = plt.subplots(figsize=(7, 5))
for area, colour in [("Settled", "tab:blue"), ("Merged", "tab:orange")]:
    sub = d[d["area"] == area]
    ax.scatter(sub["schools_gpb_middle"], sub["gpb_middle"], label=area, color=colour)
for _, row in d.nsmallest(5, "gpb_middle").iterrows():
    ax.annotate(row["unit"], (row["schools_gpb_middle"], row["gpb_middle"]), fontsize=8,
                xytext=(4, 4), textcoords="offset points")
ax.set_xlabel("Girls' middle schools per boys' middle school")
ax.set_ylabel("Girls per boy enrolled in classes 6-8")
ax.set_title("KP districts, 2024-25 (government schools)")
ax.legend()
fig.tight_layout()
fig.savefig(FIG + r"\schools_vs_enrolment_2024_25.png", dpi=150)

# ---- chart 2: median girls per boy by level and year ----
med = df.groupby("report_year")[["gpb_primary", "gpb_middle", "gpb_high"]].median()
fig, ax = plt.subplots(figsize=(7, 5))
width = 0.35
for i, (year, row) in enumerate(med.iterrows()):
    ax.bar(np.arange(3) + i * width, row.values, width, label=year)
ax.set_xticks(np.arange(3) + width / 2)
ax.set_xticklabels(["Primary (1-5)", "Middle (6-8)", "High (9-10)"])
ax.set_ylabel("Median girls per boy enrolled")
ax.set_title("Where parity drops, by level (41 units)")
ax.legend()
fig.tight_layout()
fig.savefig(FIG + r"\median_by_level.png", dpi=150)
print("\nSaved two charts in", FIG)
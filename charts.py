import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = r"D:\edu-project\data\processed\v_unit_year.csv"
FIG = r"D:\edu-project\figures"
os.makedirs(FIG, exist_ok=True)

df = pd.read_csv(DATA)
SOURCE = "Source: KP Elementary & Secondary Education Dept, Annual School Census 2023-24 and 2024-25; government schools only."

# ---- chart 1: median girls per boy by level ----
med = df.groupby("report_year")[["gpb_primary", "gpb_middle", "gpb_high"]].median()
fig, ax = plt.subplots(figsize=(7.5, 5.4))
width = 0.36
x = np.arange(3)
for i, (year, row) in enumerate(med.iterrows()):
    bars = ax.bar(x + i * width, row.values, width, label=year)
    for rect, val in zip(bars, row.values):
        ax.text(rect.get_x() + rect.get_width() / 2, val + 0.012, f"{val:.2f}",
                ha="center", fontsize=9)
ax.axhline(1.0, color="grey", linestyle="--", linewidth=1)
ax.text(-0.3, 1.02, "parity = 1.0", ha="left", fontsize=8, color="grey")
ax.set_ylim(0, 1.12)
ax.set_xticks(x + width / 2)
ax.set_xticklabels(["Primary (classes 1-5)", "Middle (6-8)", "High (9-10)"])
ax.set_ylabel("Median girls enrolled per boy (41 districts)")
ax.set_title("Where gender parity drops, by school level")
ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.86))
fig.text(0.01, 0.01, SOURCE, fontsize=6.5, color="grey")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG + r"\median_by_level.png", dpi=150)

# ---- chart 2: schools ratio vs enrolment ratio, dot size = girls enrolled in classes 6-8 ----
d = df[df["report_year"] == "2024-25"].copy()
size = 25 + 450 * d["enrol_girls_middle"] / d["enrol_girls_middle"].max()
fig, ax = plt.subplots(figsize=(8.4, 5.8))
for area, colour in [("Settled", "tab:blue"), ("Merged", "tab:orange")]:
    m = d["area"] == area
    ax.scatter(d.loc[m, "schools_gpb_middle"], d.loc[m, "gpb_middle"], s=size[m],
               color=colour, alpha=0.7, edgecolor="white", label=area)

# label position for each unit, in data coordinates (clear space, with a thin leader line)
LABELS = {
    "Kohistan Lower": (0.55, 0.075),
    "Kohistan Upper": (0.55, 0.125),
    "Kolai Palas": (0.55, 0.175),
    "Torghar": (0.58, 0.225),
    "Battagram": (0.80, 0.150),
    "Mohmand": (1.00, 0.230),
    "Orakzai": (1.50, 0.250),
    "SD Hassan Khel (Peshawar)": (1.45, 0.760),
}
for unit, (tx, ty) in LABELS.items():
    row = d[d["unit"] == unit]
    if row.empty:
        print("label skipped, unit not found:", unit)
        continue
    r = row.iloc[0]
    ax.annotate(unit, xy=(r["schools_gpb_middle"], r["gpb_middle"]), xytext=(tx, ty),
                fontsize=8, arrowprops=dict(arrowstyle="-", color="grey", lw=0.6),
                va="center")

ax.set_xlim(0.15, 2.05)
ax.set_xlabel("Girls' middle schools per boys' middle school")
ax.set_ylabel("Girls enrolled per boy, classes 6-8")
ax.set_title("More girls' schools do not always mean more girls enrolled (KP, 2024-25)")
ax.legend(title="Area", loc="upper left")
fig.text(0.01, 0.045, "Dot size = girls enrolled in classes 6-8. Ratios from units with few schools are noisy.",
         fontsize=7, color="grey")
fig.text(0.01, 0.01, SOURCE, fontsize=6.5, color="grey")
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(FIG + r"\schools_vs_enrolment_2024_25.png", dpi=150)
print("saved two charts in", FIG)
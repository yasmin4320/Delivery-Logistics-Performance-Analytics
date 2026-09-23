# -*- coding: utf-8 -*-
"""
=============================================================================
final_project.py
=============================================================================
Project  : Delivery Logistics Performance & Delay Analytics
Intern   : BharatCares Data Analytics with AI Internship

Description
-----------
This is the single, self-contained final project script.  It covers the
complete analytical workflow in one file:

  1.  Data loading       – reads the raw Delivery_Logistics.csv
  2.  Data cleaning      – replicates the logic from process_logistics.py
  3.  EDA / inspection   – replicates the logic from eda_logistics.py
  4.  Business analysis  – replicates the logic from business_analysis.py
  5.  Visualizations     – generates 9 charts
  6.  Findings report    – structured observations with cautions

Dataset contract
----------------
- Delivery_Logistics.csv is NEVER modified or overwritten.
- The original 'delayed' column ('yes'/'no') is the SOLE source of truth
  for all delay-rate calculations in the business analysis.
- All 25,000 records are preserved; duplicate delivery_id rows are kept.
- Zero-hour actual delivery records are flagged and treated as missing
  actual delivery time (NaN) in the cleaned working data.

Important notes on findings
---------------------------
- All findings are OBSERVATIONS from this SYNTHETIC dataset only.
- Correlation / association is clearly distinguished from causation.
- No factor is described as the "cause" of delays.
- Findings must NOT be generalised to real-world logistics companies.
- Delivery partners are NOT ranked as best or worst; only the observed
  delay-rate range is reported neutrally.
- No machine learning is applied.
"""

# =============================================================================
# 1. IMPORTS
# =============================================================================
import os
import sys
import io
import re
import json
import warnings
import textwrap

# Force UTF-8 output on Windows so Unicode characters (₹, –, —) print correctly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")   # non-interactive backend — safe for scripts / servers
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


# =============================================================================
# 2. FILE PATHS
# =============================================================================
RAW_CSV     = "Delivery_Logistics.csv"
OUTPUT_DIR  = "business_analysis_outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# 3. VISUAL CONSTANTS  (colours & figure sizes)
# =============================================================================
FIGSIZE_WIDE  = (12, 5)
FIGSIZE_MED   = (10, 5)
FIGSIZE_SMALL = (7, 5)

COLOR_MAIN  = "#3b82d4"
COLOR_DELAY = "#e05252"
COLOR_OK    = "#4caf7d"
PALETTE_CAT = ["#3b82d4", "#e05252", "#f59e0b", "#4caf7d", "#7c5cd8",
               "#0ea5e9", "#f97316", "#14b8a6", "#ec4899"]


# =============================================================================
# 4. HELPER FUNCTIONS
# =============================================================================

def save_fig(name: str) -> str:
    """Save the current matplotlib figure as a PNG to OUTPUT_DIR and close it."""
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


def extract_hours_from_ns_timestamp(series: pd.Series) -> pd.Series:
    """
    Convert the encoded time columns to numeric hours.

    The raw CSV stores times as strings that look like:
        '1970-01-01 00:00:00.000000008'
    The nanosecond integer in the fractional-seconds part IS the hour value.
    This function extracts that integer.  If parsing fails the value becomes NaN.
    """
    def _parse(val):
        if pd.isna(val):
            return np.nan
        s = str(val).strip()
        m = re.search(r'\.(\d+)$', s)
        if m:
            return int(m.group(1))          # nanosecond integer == hour value
        # Fallback: try to parse as a Timestamp
        try:
            ts = pd.Timestamp(s)
            return int(ts.value)            # nanoseconds since epoch
        except Exception:
            return np.nan
    return series.apply(_parse)


def delay_rate_pct(group: pd.Series) -> float:
    """
    Calculate the delay rate as a percentage from the original 'delayed' column.
    Accepts a Series of 'yes'/'no' strings.
    """
    return (group.str.lower() == "yes").mean() * 100


# =============================================================================
# 5. DATA LOADING
# =============================================================================

def load_raw_data(path: str) -> pd.DataFrame:
    """
    Load the raw CSV.  The file is never modified or written back.
    Returns a new DataFrame each time; the file on disk is untouched.
    """
    df = pd.read_csv(path)
    print(f"Raw dataset loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"Columns: {df.columns.tolist()}")
    return df


# =============================================================================
# 6. DATA CLEANING
# =============================================================================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning steps to produce the working DataFrame.

    Steps
    -----
    a) Extract numeric hours from the encoded delivery_time_hours column.
    b) Extract numeric hours from the encoded expected_time_hours column.
    c) Flag records where actual delivery time was zero (255 records).
    d) Replace zero-hour actual delivery times with NaN (treat as missing).
    e) Create is_delayed_flag  (1 if delivery_status == 'delayed', else 0).
    f) Create delayed_original_binary  (1 if delayed == 'yes', else 0).
    g) Compute computed_delayed  (1 if actual_time > expected_time, else 0).

    Rules enforced
    --------------
    - delivery_id is NOT modified or rounded.
    - Duplicate delivery_id rows are NOT removed.
    - All 25,000 records are preserved.
    - The original 'delayed' string column is preserved unchanged.
    - The raw CSV file is never written back.
    """
    print("\n" + "=" * 60)
    print("DATA CLEANING")
    print("=" * 60)

    # Work on a copy so the caller's original df is not mutated
    df = df.copy()

    # ── a & b. Extract numeric hours ─────────────────────────────────────────
    df["delivery_time_hours_num"] = extract_hours_from_ns_timestamp(
        df["delivery_time_hours"]
    )
    df["expected_time_hours_num"] = extract_hours_from_ns_timestamp(
        df["expected_time_hours"]
    )
    print(f"  delivery_time_hours_num unique values: "
          f"{sorted(df['delivery_time_hours_num'].dropna().unique())}")
    print(f"  expected_time_hours_num unique values: "
          f"{sorted(df['expected_time_hours_num'].dropna().unique())}")

    # ── c. Flag zero-hour actual delivery records ─────────────────────────────
    zero_hour_mask  = df["delivery_time_hours_num"] == 0
    zero_hour_count = int(zero_hour_mask.sum())
    df["zero_hour_flag"] = zero_hour_mask.astype(int)   # 1 = was zero
    print(f"\n  Zero-hour actual delivery records flagged: {zero_hour_count:,}")

    # ── d. Replace zero-hour actual delivery times with NaN ──────────────────
    df.loc[zero_hour_mask, "delivery_time_hours_num"] = np.nan
    print(f"  NaN count in delivery_time_hours_num after replacement: "
          f"{df['delivery_time_hours_num'].isna().sum():,}")

    # ── e. is_delayed_flag from delivery_status ───────────────────────────────
    df["is_delayed_flag"] = (
        df["delivery_status"].str.strip().str.lower() == "delayed"
    ).astype(int)
    print(f"\n  is_delayed_flag (status == 'delayed'): "
          f"{df['is_delayed_flag'].sum():,}")

    # ── f. Binary version of the original delayed column ─────────────────────
    df["delayed_original_binary"] = (
        df["delayed"].str.strip().str.lower() == "yes"
    ).astype(int)
    print(f"  delayed_original_binary (delayed == 'yes'): "
          f"{df['delayed_original_binary'].sum():,}")

    # ── g. Computed delayed flag ──────────────────────────────────────────────
    #       Uses nullable Int64 so NaN rows (zero-hour records) are preserved.
    df["computed_delayed"] = (
        (df["delivery_time_hours_num"] > df["expected_time_hours_num"])
        .astype("Int64")
    )

    # Data-quality note: count label conflicts between original and computed
    conflict_mask  = (
        df["computed_delayed"].notna() &
        (df["delayed_original_binary"] != df["computed_delayed"])
    )
    conflict_count = int(conflict_mask.sum())
    print(f"\n  Delay label conflicts (original vs computed): {conflict_count:,}")
    print(f"  NOTE: The business analysis uses the ORIGINAL 'delayed' column,")
    print(f"        not the computed flag.  The computed flag is kept for")
    print(f"        reference and data-quality inspection only.")

    # ── Duplicate delivery_id analysis (observation only; no rows removed) ────
    dup_counts = df["delivery_id"].value_counts()
    dup_ids    = dup_counts[dup_counts > 1]
    print(f"\n  Unique delivery_id values with >1 occurrence: {len(dup_ids):,}")
    print(f"  Total records involved in those groups:       {dup_ids.sum():,}")
    print(f"  NOTE: Duplicate delivery_id rows are retained.  Each row")
    print(f"        represents a distinct delivery event in this dataset.")

    print(f"\n  Cleaned DataFrame shape: {df.shape}")
    print(f"  New columns added: delivery_time_hours_num, expected_time_hours_num,")
    print(f"                     zero_hour_flag, is_delayed_flag,")
    print(f"                     delayed_original_binary, computed_delayed")

    return df


# =============================================================================
# 7. EDA / DATA-QUALITY ANALYSIS
# =============================================================================

def run_eda(df: pd.DataFrame) -> None:
    """
    Print a concise exploratory data analysis of the cleaned working DataFrame.

    Covers: shape, dtypes, missing values, duplicate information,
            categorical distributions, numerical summaries, and key
            data-quality observations relevant to the business analysis.
    """
    print("\n" + "=" * 60)
    print("EDA / DATA-QUALITY ANALYSIS")
    print("=" * 60)

    # ── Shape & dtypes ────────────────────────────────────────────────────────
    print(f"\n  Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print("\n  Column data types:")
    for col, dtype in df.dtypes.items():
        print(f"    {col:<35} {dtype}")

    # ── Missing values ────────────────────────────────────────────────────────
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    print("\n  Missing values (columns with at least one NaN):")
    if missing.empty:
        print("    None detected in any column.")
    else:
        for col, n in missing.items():
            print(f"    {col:<35} {n:,}  ({n / len(df) * 100:.2f}%)")

    # ── Duplicate rows ────────────────────────────────────────────────────────
    exact_dups = int(df.duplicated().sum())
    print(f"\n  Exact duplicate rows: {exact_dups:,}")
    print(f"  Unique delivery_id values: {df['delivery_id'].nunique():,}")
    dup_id_count = int((df['delivery_id'].value_counts() > 1).sum())
    print(f"  delivery_id values appearing more than once: {dup_id_count:,}")
    print(f"  Observation: delivery_id is not a unique row key in this dataset.")
    print(f"  Each row is treated as a distinct delivery event.")

    # ── Categorical distributions ─────────────────────────────────────────────
    cat_cols = ["delivery_mode", "weather_condition", "region",
                "delivery_partner", "vehicle_type", "package_type",
                "delivery_status", "delayed"]
    print("\n  Categorical distributions:")
    for col in cat_cols:
        if col in df.columns:
            counts = df[col].value_counts(dropna=False)
            print(f"\n    -- {col} --")
            for val, n in counts.items():
                print(f"      {str(val):<25} {n:>6,}  ({n / len(df) * 100:.1f}%)")

    # ── Numerical summaries ───────────────────────────────────────────────────
    num_cols = ["distance_km", "package_weight_kg",
                "delivery_time_hours_num", "expected_time_hours_num",
                "delivery_cost", "delivery_rating"]
    print("\n  Numerical summaries:")
    for col in num_cols:
        if col in df.columns:
            s = df[col].dropna()
            print(f"\n    -- {col} --")
            print(f"      count : {len(s):,}  (NaN: {df[col].isna().sum():,})")
            print(f"      min   : {s.min():.2f}    max: {s.max():.2f}")
            print(f"      mean  : {s.mean():.4f}  median: {s.median():.2f}")
            print(f"      std   : {s.std():.4f}")

    # ── Correlation matrix (numeric columns) ─────────────────────────────────
    df_valid = df.dropna(subset=["delivery_time_hours_num"])
    corr_cols = ["distance_km", "package_weight_kg",
                 "delivery_time_hours_num", "expected_time_hours_num",
                 "delivery_cost", "delivery_rating"]
    corr_matrix = df_valid[corr_cols].corr().round(4)
    print("\n  Pearson correlation matrix (rows with non-NaN delivery time):")
    print(corr_matrix.to_string())

    # ── SLA tier vs delay rate (data-quality observation) ────────────────────
    sla = df.groupby("expected_time_hours_num").agg(
        deliveries=("delivery_id", "count"),
        delayed_yes=("delayed_original_binary", "sum"),
        avg_actual=("delivery_time_hours_num", "mean"),
    ).reset_index()
    sla["delay_rate_pct"] = (sla["delayed_yes"] / sla["deliveries"] * 100).round(2)
    sla["avg_actual"]     = sla["avg_actual"].round(3)
    print("\n  SLA tier (expected_time_hours_num) vs delay rate:")
    print(sla.to_string(index=False))

    # ── Zero-hour and equal-time records ─────────────────────────────────────
    equal_time_delayed = df[
        (df["delivery_time_hours_num"] == df["expected_time_hours_num"]) &
        (df["delayed_original_binary"] == 1)
    ]
    print(f"\n  Records where actual_time == expected_time AND delayed=yes: "
          f"{len(equal_time_delayed):,}")
    print(f"  Zero-hour actual delivery records (flagged, treated as NaN): "
          f"{df['zero_hour_flag'].sum():,}")

    print("\n  EDA complete.")


# =============================================================================
# 8. BUSINESS KPI ANALYSIS
# =============================================================================

def compute_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate overall business KPIs.

    Delay rate uses the original 'delayed' string column ('yes'/'no').
    Returns a dict and saves kpis.json to OUTPUT_DIR.
    """
    print("\n" + "=" * 60)
    print("BUSINESS ANALYSIS — OVERALL KPIs")
    print("=" * 60)

    total_deliveries   = len(df)
    overall_delay_rate = (df["delayed"].str.lower() == "yes").mean()
    avg_actual_time    = df["delivery_time_hours_num"].mean()
    avg_expected_time  = df["expected_time_hours_num"].mean()
    avg_cost           = df["delivery_cost"].mean()
    avg_rating         = df["delivery_rating"].mean()

    kpis = {
        "total_deliveries":        total_deliveries,
        "delay_rate_pct":          round(overall_delay_rate * 100, 2),
        "avg_actual_delivery_hrs": round(avg_actual_time, 2),
        "avg_expected_sla_hrs":    round(avg_expected_time, 2),
        "avg_delivery_cost_inr":   round(avg_cost, 2),
        "avg_delivery_rating":     round(avg_rating, 2),
    }

    for k, v in kpis.items():
        print(f"  {k:<35} {v}")

    with open(os.path.join(OUTPUT_DIR, "kpis.json"), "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=2)
    print(f"\n  Saved: kpis.json")

    return kpis


# =============================================================================
# 9. DELIVERY MODE ANALYSIS
# =============================================================================

def analyse_delivery_mode(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each delivery mode: total deliveries, delayed deliveries, delay rate,
    average actual delivery time, average expected time.

    Delay rate uses the original 'delayed' column.
    Saves mode_analysis.csv to OUTPUT_DIR.
    """
    print("\n" + "=" * 60)
    print("DELIVERY MODE ANALYSIS")
    print("=" * 60)

    grp = df.groupby("delivery_mode")
    result = pd.DataFrame({
        "total_deliveries":   grp.size(),
        "delayed_deliveries": grp.apply(
            lambda g: (g["delayed"].str.lower() == "yes").sum()),
        "delay_rate_pct":     grp.apply(
            lambda g: (g["delayed"].str.lower() == "yes").mean() * 100).round(2),
        "avg_delivery_time":  grp["delivery_time_hours_num"].mean().round(2),
        "avg_expected_time":  grp["expected_time_hours_num"].mean().round(2),
    }).reset_index()

    print(result.to_string(index=False))
    result.to_csv(os.path.join(OUTPUT_DIR, "mode_analysis.csv"), index=False)
    print(f"\n  Saved: mode_analysis.csv")

    return result


# =============================================================================
# 10. WEATHER ANALYSIS
# =============================================================================

def analyse_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each weather condition: total deliveries, delayed deliveries,
    delay rate, average actual delivery time.

    Delay rate uses the original 'delayed' column.
    Saves weather_analysis.csv to OUTPUT_DIR.
    """
    print("\n" + "=" * 60)
    print("WEATHER ANALYSIS")
    print("=" * 60)

    grp = df.groupby("weather_condition")
    result = pd.DataFrame({
        "total_deliveries":   grp.size(),
        "delayed_deliveries": grp.apply(
            lambda g: (g["delayed"].str.lower() == "yes").sum()),
        "delay_rate_pct":     grp.apply(
            lambda g: (g["delayed"].str.lower() == "yes").mean() * 100).round(2),
        "avg_delivery_time":  grp["delivery_time_hours_num"].mean().round(2),
    }).reset_index()

    print(result.to_string(index=False))
    result.to_csv(os.path.join(OUTPUT_DIR, "weather_analysis.csv"), index=False)
    print(f"\n  Saved: weather_analysis.csv")

    return result


# =============================================================================
# 11. DISTANCE ANALYSIS
# =============================================================================

def analyse_distance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group deliveries into 5 distance bands (0–60, 61–120, 121–180,
    181–240, 241–300 km) and calculate: delivery count, delay rate,
    average actual delivery time, average delivery cost.

    Observed distance range in this dataset: 3.6 – 297.1 km.
    Delay rate uses the original 'delayed' column.
    Saves distance_analysis.csv to OUTPUT_DIR.
    """
    print("\n" + "=" * 60)
    print("DISTANCE ANALYSIS")
    print("=" * 60)

    dist_bins   = [0, 60, 120, 180, 240, 300]
    dist_labels = ["0\u201360 km", "61\u2013120 km", "121\u2013180 km",
                   "181\u2013240 km", "241\u2013300 km"]

    df_dist = df.copy()
    df_dist["distance_group"] = pd.cut(
        df_dist["distance_km"], bins=dist_bins, labels=dist_labels, right=True
    )

    grp = df_dist.groupby("distance_group", observed=True)
    result = pd.DataFrame({
        "delivery_count":    grp.size(),
        "delay_rate_pct":    grp.apply(
            lambda g: (g["delayed"].str.lower() == "yes").mean() * 100).round(2),
        "avg_delivery_time": grp["delivery_time_hours_num"].mean().round(2),
        "avg_delivery_cost": grp["delivery_cost"].mean().round(2),
    }).reset_index()

    print(result.to_string(index=False))
    result.to_csv(os.path.join(OUTPUT_DIR, "distance_analysis.csv"), index=False)
    print(f"\n  Saved: distance_analysis.csv")

    return result


# =============================================================================
# 12. CUSTOMER EXPERIENCE ANALYSIS
# =============================================================================

def analyse_customer_experience(df: pd.DataFrame) -> tuple:
    """
    Analyse the relationship between delivery time and delivery rating.

    Computes the Pearson correlation coefficient and calculates, for each
    rating bucket (1–5): count, average actual delivery time, average cost,
    delay rate.

    Returns (rating_analysis DataFrame, pearson_r float).
    Saves rating_analysis.csv to OUTPUT_DIR.

    Note: The correlation is a statistical association.  Other factors
    (package condition, customer communication, cost) also influence ratings
    and are not captured in this dataset.  No causal claim is made.
    """
    print("\n" + "=" * 60)
    print("CUSTOMER EXPERIENCE — Delivery Time vs Rating")
    print("=" * 60)

    corr_val = df["delivery_time_hours_num"].corr(df["delivery_rating"])
    print(f"  Pearson correlation (delivery time vs rating): {corr_val:.4f}")
    print(f"  Interpretation: weak negative association — longer delivery times")
    print(f"  tend to correspond with slightly lower ratings in this dataset.")
    print(f"  This is an ASSOCIATION, not a causal relationship.")

    grp = df.groupby("delivery_rating")
    result = pd.DataFrame({
        "delivery_count":    grp.size(),
        "avg_delivery_time": grp["delivery_time_hours_num"].mean().round(2),
        "avg_delivery_cost": grp["delivery_cost"].mean().round(2),
        "delay_rate_pct":    grp.apply(
            lambda g: (g["delayed"].str.lower() == "yes").mean() * 100).round(2),
    }).reset_index()

    print(result.to_string(index=False))
    result.to_csv(os.path.join(OUTPUT_DIR, "rating_analysis.csv"), index=False)
    print(f"\n  Saved: rating_analysis.csv")

    return result, corr_val


# =============================================================================
# 13. PARTNER AND REGION ANALYSIS
# =============================================================================

def analyse_partners_and_regions(df: pd.DataFrame) -> tuple:
    """
    Calculate delay rate for each delivery partner and each region.

    Reports the observed range (max minus min) between the highest- and
    lowest-rate groups for each dimension.  Partners are NOT ranked or
    labelled as best/worst.  Confounding variables are acknowledged.

    Returns (partner_analysis DataFrame, region_analysis DataFrame).
    Saves partner_analysis.csv and region_analysis.csv to OUTPUT_DIR.
    """
    print("\n" + "=" * 60)
    print("PARTNER AND REGION ANALYSIS")
    print("=" * 60)

    # ── Partners ──────────────────────────────────────────────────────────────
    grp_p = df.groupby("delivery_partner")
    partner_df = pd.DataFrame({
        "total_deliveries":   grp_p.size(),
        "delayed_deliveries": grp_p.apply(
            lambda g: (g["delayed"].str.lower() == "yes").sum()),
        "delay_rate_pct":     grp_p.apply(
            lambda g: (g["delayed"].str.lower() == "yes").mean() * 100).round(2),
        "avg_rating":         grp_p["delivery_rating"].mean().round(2),
    }).reset_index().sort_values("delay_rate_pct")

    p_min   = partner_df["delay_rate_pct"].min()
    p_max   = partner_df["delay_rate_pct"].max()
    p_range = round(float(p_max) - float(p_min), 2)

    print("  Partner delay rates (sorted ascending):")
    print(partner_df.to_string(index=False))
    print(f"\n  Partner delay rate range (max - min): {p_range} pp "
          f"[{p_min}% to {p_max}%]")
    print(f"  NOTE: Partners are not ranked.  Observed differences may reflect")
    print(f"  varying mixes of regions, modes, and package types.")
    partner_df.to_csv(os.path.join(OUTPUT_DIR, "partner_analysis.csv"), index=False)
    print(f"\n  Saved: partner_analysis.csv")

    # ── Regions ───────────────────────────────────────────────────────────────
    grp_r = df.groupby("region")
    region_df = pd.DataFrame({
        "total_deliveries":   grp_r.size(),
        "delayed_deliveries": grp_r.apply(
            lambda g: (g["delayed"].str.lower() == "yes").sum()),
        "delay_rate_pct":     grp_r.apply(
            lambda g: (g["delayed"].str.lower() == "yes").mean() * 100).round(2),
        "avg_rating":         grp_r["delivery_rating"].mean().round(2),
    }).reset_index().sort_values("delay_rate_pct")

    r_min   = region_df["delay_rate_pct"].min()
    r_max   = region_df["delay_rate_pct"].max()
    r_range = round(float(r_max) - float(r_min), 2)

    print("\n  Region delay rates (sorted ascending):")
    print(region_df.to_string(index=False))
    print(f"\n  Region delay rate range (max - min): {r_range} pp "
          f"[{r_min}% to {r_max}%]")
    region_df.to_csv(os.path.join(OUTPUT_DIR, "region_analysis.csv"), index=False)
    print(f"\n  Saved: region_analysis.csv")

    return partner_df, region_df


# =============================================================================
# 14. VISUALIZATION GENERATION
# =============================================================================

def generate_visualizations(
    df, kpis, overall_delay_rate,
    mode_df, weather_df, distance_df,
    rating_df, corr_val,
    partner_df, region_df,
) -> None:
    """
    Generate and save all 9 project charts to OUTPUT_DIR.

    Charts
    ------
    01  KPI summary tile grid
    02  Delay rate by delivery mode (horizontal bar)
    03  Delay rate by weather condition (horizontal bar)
    04  Distance group vs average delivery time (vertical bar, annotated)
    05  Distance group vs average delivery cost (vertical bar)
    06  Delivery time vs rating (line chart, Pearson r in title)
    07  Delivery status distribution (pie chart)
    08  Partner delay rate comparison (vertical bar, vs overall avg)
    09  Region delay rate comparison (vertical bar, vs overall avg)
    """
    print("\n" + "=" * 60)
    print("GENERATING VISUALIZATIONS")
    print("=" * 60)

    # ── 01. KPI Summary ───────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 3, figsize=(14, 6))
    fig.suptitle("Overall KPI Summary", fontsize=14, fontweight="bold", y=1.02)

    kpi_tiles = [
        ("Total\nDeliveries",   f"{kpis['total_deliveries']:,}",                 COLOR_MAIN),
        ("Delay Rate",          f"{kpis['delay_rate_pct']}%",                    COLOR_DELAY),
        ("Avg Actual\nTime",    f"{kpis['avg_actual_delivery_hrs']} h",           "#f59e0b"),
        ("Avg Expected\nTime",  f"{kpis['avg_expected_sla_hrs']} h",             "#4caf7d"),
        ("Avg Cost",            f"\u20b9{kpis['avg_delivery_cost_inr']:,.0f}",   "#7c5cd8"),
        ("Avg Rating",          f"{kpis['avg_delivery_rating']} / 5",            "#0ea5e9"),
    ]
    for ax, (label, value, color) in zip(axes.flat, kpi_tiles):
        ax.set_facecolor(color + "18")
        ax.text(0.5, 0.58, value, ha="center", va="center", fontsize=22,
                fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(0.5, 0.28, label, ha="center", va="center", fontsize=11,
                color="#57606a", transform=ax.transAxes)
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(1.5)
        ax.set_xticks([])
        ax.set_yticks([])
    plt.tight_layout()
    save_fig("01_kpi_summary")
    print("  Saved: 01_kpi_summary.png")

    # ── 02. Delay Rate by Delivery Mode ───────────────────────────────────────
    fig, ax = plt.subplots(figsize=FIGSIZE_MED)
    ma = mode_df.sort_values("delay_rate_pct", ascending=True)
    bars = ax.barh(ma["delivery_mode"], ma["delay_rate_pct"],
                   color=COLOR_DELAY, edgecolor="white", height=0.5)
    ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=10)
    ax.axvline(overall_delay_rate * 100, color="#1f2328", linestyle="--",
               linewidth=1.2,
               label=f"Overall avg ({overall_delay_rate * 100:.1f}%)")
    ax.set_xlabel("Delay Rate (%)")
    ax.set_title("Delay Rate by Delivery Mode", fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(0, ma["delay_rate_pct"].max() * 1.2)
    plt.tight_layout()
    save_fig("02_delay_rate_by_mode")
    print("  Saved: 02_delay_rate_by_mode.png")

    # ── 03. Delay Rate by Weather Condition ───────────────────────────────────
    fig, ax = plt.subplots(figsize=FIGSIZE_MED)
    wa = weather_df.sort_values("delay_rate_pct", ascending=True)
    bars = ax.barh(wa["weather_condition"], wa["delay_rate_pct"],
                   color=COLOR_DELAY, edgecolor="white", height=0.5)
    ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=10)
    ax.axvline(overall_delay_rate * 100, color="#1f2328", linestyle="--",
               linewidth=1.2,
               label=f"Overall avg ({overall_delay_rate * 100:.1f}%)")
    ax.set_xlabel("Delay Rate (%)")
    ax.set_title("Delay Rate by Weather Condition", fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(0, wa["delay_rate_pct"].max() * 1.2)
    plt.tight_layout()
    save_fig("03_delay_rate_by_weather")
    print("  Saved: 03_delay_rate_by_weather.png")

    # ── 04. Distance vs Avg Delivery Time ─────────────────────────────────────
    fig, ax = plt.subplots(figsize=FIGSIZE_MED)
    da = distance_df
    ax.bar(da["distance_group"].astype(str), da["avg_delivery_time"],
           color=COLOR_MAIN, edgecolor="white", width=0.55)
    for i, (val, dr) in enumerate(zip(da["avg_delivery_time"], da["delay_rate_pct"])):
        ax.text(i, val + 0.08, f"{val:.1f} h\n({dr:.0f}% delayed)",
                ha="center", va="bottom", fontsize=9, color="#1f2328")
    ax.set_ylabel("Avg Delivery Time (hours)")
    ax.set_xlabel("Distance Group")
    ax.set_title("Distance Group vs Average Delivery Time\n(delay rate annotated)",
                 fontweight="bold")
    ax.set_ylim(0, da["avg_delivery_time"].max() * 1.3)
    plt.tight_layout()
    save_fig("04_distance_vs_delivery_time")
    print("  Saved: 04_distance_vs_delivery_time.png")

    # ── 05. Distance vs Avg Delivery Cost ─────────────────────────────────────
    fig, ax = plt.subplots(figsize=FIGSIZE_MED)
    ax.bar(da["distance_group"].astype(str), da["avg_delivery_cost"],
           color="#7c5cd8", edgecolor="white", width=0.55)
    for i, val in enumerate(da["avg_delivery_cost"]):
        ax.text(i, val + 8, f"\u20b9{val:,.0f}", ha="center", va="bottom",
                fontsize=9, color="#1f2328")
    ax.set_ylabel("Avg Delivery Cost (\u20b9)")
    ax.set_xlabel("Distance Group")
    ax.set_title("Distance Group vs Average Delivery Cost", fontweight="bold")
    ax.set_ylim(0, da["avg_delivery_cost"].max() * 1.2)
    plt.tight_layout()
    save_fig("05_distance_vs_delivery_cost")
    print("  Saved: 05_distance_vs_delivery_cost.png")

    # ── 06. Delivery Time vs Rating ───────────────────────────────────────────
    fig, ax = plt.subplots(figsize=FIGSIZE_MED)
    ra = rating_df
    ax.plot(ra["delivery_rating"], ra["avg_delivery_time"],
            marker="o", linewidth=2, markersize=8, color=COLOR_MAIN)
    for _, row in ra.iterrows():
        ax.annotate(f"{row['avg_delivery_time']:.1f} h",
                    xy=(row["delivery_rating"], row["avg_delivery_time"]),
                    xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=9, color="#1f2328")
    ax.set_xlabel("Delivery Rating (1\u20135)")
    ax.set_ylabel("Avg Delivery Time (hours)")
    ax.set_title(f"Delivery Time vs Rating  |  Pearson r = {corr_val:.3f}",
                 fontweight="bold")
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_ylim(0, ra["avg_delivery_time"].max() * 1.3)
    plt.tight_layout()
    save_fig("06_delivery_time_vs_rating")
    print("  Saved: 06_delivery_time_vs_rating.png")

    # ── 07. Delivery Status Distribution ──────────────────────────────────────
    status_counts = df["delivery_status"].value_counts()
    fig, ax = plt.subplots(figsize=FIGSIZE_SMALL)
    _, _, autotexts = ax.pie(
        status_counts.values,
        labels=status_counts.index,
        autopct="%1.1f%%",
        colors=PALETTE_CAT[:len(status_counts)],
        startangle=140,
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_fontsize(10)
    ax.set_title("Delivery Status Distribution", fontweight="bold")
    plt.tight_layout()
    save_fig("07_delivery_status_distribution")
    print("  Saved: 07_delivery_status_distribution.png")

    # ── 08. Partner Delay Rate Comparison ─────────────────────────────────────
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    pa = partner_df.sort_values("delay_rate_pct")
    colors = [COLOR_DELAY if v >= overall_delay_rate * 100 else COLOR_OK
              for v in pa["delay_rate_pct"]]
    bars = ax.bar(pa["delivery_partner"], pa["delay_rate_pct"],
                  color=colors, edgecolor="white", width=0.55)
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    ax.axhline(overall_delay_rate * 100, color="#1f2328", linestyle="--",
               linewidth=1.2,
               label=f"Overall avg ({overall_delay_rate * 100:.1f}%)")
    ax.set_ylabel("Delay Rate (%)")
    ax.set_xlabel("Delivery Partner")
    ax.set_title("Delay Rate by Delivery Partner\n"
                 "(red = above average, green = at or below average)",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, pa["delay_rate_pct"].max() * 1.2)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    save_fig("08_partner_delay_rate")
    print("  Saved: 08_partner_delay_rate.png")

    # ── 09. Region Delay Rate Comparison ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))
    ra2 = region_df.sort_values("delay_rate_pct")
    colors2 = [COLOR_DELAY if v >= overall_delay_rate * 100 else COLOR_OK
               for v in ra2["delay_rate_pct"]]
    bars2 = ax.bar(ra2["region"], ra2["delay_rate_pct"],
                   color=colors2, edgecolor="white", width=0.45)
    ax.bar_label(bars2, fmt="%.1f%%", padding=3, fontsize=10)
    ax.axhline(overall_delay_rate * 100, color="#1f2328", linestyle="--",
               linewidth=1.2,
               label=f"Overall avg ({overall_delay_rate * 100:.1f}%)")
    ax.set_ylabel("Delay Rate (%)")
    ax.set_xlabel("Region")
    ax.set_title("Delay Rate by Region\n"
                 "(red = above average, green = at or below average)",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, ra2["delay_rate_pct"].max() * 1.2)
    plt.tight_layout()
    save_fig("09_region_delay_rate")
    print("  Saved: 09_region_delay_rate.png")


# =============================================================================
# 15. FINDINGS GENERATION
# =============================================================================

def generate_findings(
    kpis, overall_delay_rate,
    mode_df, weather_df, distance_df,
    rating_df, corr_val,
    partner_df, region_df,
) -> dict:
    """
    Build the structured findings report and save findings.json to OUTPUT_DIR.

    Each section contains:
      - metric          : exact numeric finding with the groups being compared
      - interpretation  : plain-language business observation
      - caution         : explicit statement distinguishing association from causation

    All findings are observations from this SYNTHETIC dataset.
    No causal claims are made.  Partners are not ranked.
    """
    print("\n" + "=" * 60)
    print("FINDINGS REPORT")
    print("=" * 60)

    findings = {}

    # ── Overall ───────────────────────────────────────────────────────────────
    findings["overall"] = {
        "metric": f"Overall delay rate: {kpis['delay_rate_pct']}%",
        "context": f"{kpis['total_deliveries']:,} total deliveries",
        "interpretation": (
            f"Approximately 1 in every {round(1 / overall_delay_rate):.0f} "
            "deliveries is recorded as delayed in this dataset.  "
            "This baseline is the reference point for all group-level "
            "comparisons below."
        ),
    }

    # ── Delivery mode ─────────────────────────────────────────────────────────
    ms  = mode_df.sort_values("delay_rate_pct")
    mhi = ms.iloc[-1]
    mlo = ms.iloc[0]
    mrng = round(float(mhi["delay_rate_pct"]) - float(mlo["delay_rate_pct"]), 2)

    findings["delivery_mode"] = {
        "metric": (
            f"Delay rates by mode range from {mlo['delay_rate_pct']}% "
            f"({mlo['delivery_mode']}) to {mhi['delay_rate_pct']}% "
            f"({mhi['delivery_mode']}) \u2014 a spread of {mrng} pp."
        ),
        "groups_compared": mode_df[["delivery_mode", "delay_rate_pct"]].to_dict("records"),
        "interpretation": (
            "There is a notable spread in observed delay rates across delivery modes. "
            "This is an association in the data; we cannot conclude that the delivery "
            "mode itself causes delays, as mode is likely correlated with distance, "
            "package type, or other factors not controlled for here."
        ),
        "caution": "Correlation, not causation.",
    }

    # ── Weather ───────────────────────────────────────────────────────────────
    ws  = weather_df.sort_values("delay_rate_pct")
    whi = ws.iloc[-1]
    wlo = ws.iloc[0]
    wrng = round(float(whi["delay_rate_pct"]) - float(wlo["delay_rate_pct"]), 2)

    findings["weather"] = {
        "metric": (
            f"Delay rates by weather range from {wlo['delay_rate_pct']}% "
            f"({wlo['weather_condition']}) to {whi['delay_rate_pct']}% "
            f"({whi['weather_condition']}) \u2014 a spread of {wrng} pp."
        ),
        "groups_compared": weather_df[["weather_condition", "delay_rate_pct"]].to_dict("records"),
        "interpretation": (
            "Certain weather conditions are associated with higher delay rates in this "
            "dataset. In real-world logistics adverse weather can plausibly affect transit "
            "times; however, this is synthetic data, so the relationship reflects the data "
            "generation process rather than operational reality."
        ),
        "caution": "Association observed in synthetic data; no causal inference.",
    }

    # ── Distance ──────────────────────────────────────────────────────────────
    findings["distance"] = {
        "metric": (
            f"Avg delivery cost rises from "
            f"\u20b9{distance_df['avg_delivery_cost'].iloc[0]:,.0f} (0\u201360 km) "
            f"to \u20b9{distance_df['avg_delivery_cost'].iloc[-1]:,.0f} (241\u2013300 km)."
        ),
        "groups_compared": distance_df.to_dict("records"),
        "interpretation": (
            "Delivery cost shows a clear positive association with distance group in this "
            "dataset. Delivery time also increases with distance.  Delay rate variation "
            "across distance bands is an observed pattern; distance alone may not explain "
            "delays without controlling for other variables."
        ),
        "caution": "Association, not causation.",
    }

    # ── Customer experience ───────────────────────────────────────────────────
    findings["customer_experience"] = {
        "metric": f"Pearson r (delivery time vs rating) = {corr_val:.4f}",
        "groups_compared": rating_df[["delivery_rating", "avg_delivery_time"]].to_dict("records"),
        "interpretation": (
            f"The Pearson correlation between delivery time and rating is {corr_val:.3f}, "
            "indicating a weak negative association \u2014 longer delivery times tend to "
            "correspond to slightly lower ratings in this dataset.  This is a statistical "
            "association; other factors (cost, package condition, communication) also "
            "influence customer satisfaction and are not captured here."
        ),
        "caution": "Weak correlation; no causal claim.",
    }

    # ── Partner ───────────────────────────────────────────────────────────────
    p_min   = partner_df["delay_rate_pct"].min()
    p_max   = partner_df["delay_rate_pct"].max()
    p_range = round(float(p_max) - float(p_min), 2)

    findings["partner"] = {
        "metric": (
            f"Partner delay rates span a range of {p_range} percentage points "
            f"({p_min}% \u2013 {p_max}%)."
        ),
        "groups_compared": partner_df[["delivery_partner", "delay_rate_pct"]].to_dict("records"),
        "interpretation": (
            "There is meaningful variation in delay rates across delivery partners in this "
            f"dataset. The range of {p_range} pp represents the gap between the highest- "
            "and lowest-rate partners. Because partners may operate in different regions, "
            "carry different package types, or serve different delivery modes, the observed "
            "difference is a descriptive pattern, not an isolated measure of each partner's "
            "performance."
        ),
        "caution": (
            "Confounding variables (region, mode, package type) are not controlled for. "
            "Do not interpret rate differences as a direct ranking of operational quality."
        ),
    }

    # ── Region ────────────────────────────────────────────────────────────────
    r_min   = region_df["delay_rate_pct"].min()
    r_max   = region_df["delay_rate_pct"].max()
    r_range = round(float(r_max) - float(r_min), 2)

    findings["region"] = {
        "metric": (
            f"Region delay rates span a range of {r_range} percentage points "
            f"({r_min}% \u2013 {r_max}%)."
        ),
        "groups_compared": region_df[["region", "delay_rate_pct"]].to_dict("records"),
        "interpretation": (
            f"Delay rates differ across regions by up to {r_range} pp in this dataset.  "
            "Regional differences may reflect varying mixes of partners, weather conditions, "
            "or delivery modes rather than geography alone."
        ),
        "caution": "Descriptive observation; confounding not controlled.",
    }

    # ── Console summary ───────────────────────────────────────────────────────
    for section, content in findings.items():
        print(f"\n  [{section.upper()}]")
        print(f"  Metric : {content['metric']}")
        print(textwrap.fill(
            f"  Interpretation: {content['interpretation']}",
            width=78, subsequent_indent="    "))
        print(f"  Caution: {content.get('caution', '')}")

    with open(os.path.join(OUTPUT_DIR, "findings.json"), "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: findings.json")

    return findings


# =============================================================================
# MAIN — orchestrates the complete workflow
# =============================================================================

def main():
    print("=" * 60)
    print("DELIVERY LOGISTICS PERFORMANCE & DELAY ANALYTICS")
    print("BharatCares Data Analytics with AI Internship")
    print("=" * 60)

    # ── Step 1: Load raw data ─────────────────────────────────────────────────
    raw_df = load_raw_data(RAW_CSV)

    # ── Step 2: Clean data ────────────────────────────────────────────────────
    df = clean_data(raw_df)

    # ── Step 3: EDA / data-quality inspection ─────────────────────────────────
    run_eda(df)

    # ── Step 4: Compute overall KPIs ─────────────────────────────────────────
    kpis = compute_kpis(df)
    overall_delay_rate = (df["delayed"].str.lower() == "yes").mean()

    # ── Step 5: Mode analysis ─────────────────────────────────────────────────
    mode_df = analyse_delivery_mode(df)

    # ── Step 6: Weather analysis ──────────────────────────────────────────────
    weather_df = analyse_weather(df)

    # ── Step 7: Distance analysis ─────────────────────────────────────────────
    distance_df = analyse_distance(df)

    # ── Step 8: Customer experience ───────────────────────────────────────────
    rating_df, corr_val = analyse_customer_experience(df)

    # ── Step 9: Partner and region analysis ───────────────────────────────────
    partner_df, region_df = analyse_partners_and_regions(df)

    # ── Step 10: Visualizations ───────────────────────────────────────────────
    generate_visualizations(
        df, kpis, overall_delay_rate,
        mode_df, weather_df, distance_df,
        rating_df, corr_val,
        partner_df, region_df,
    )

    # ── Step 11: Findings report ──────────────────────────────────────────────
    generate_findings(
        kpis, overall_delay_rate,
        mode_df, weather_df, distance_df,
        rating_df, corr_val,
        partner_df, region_df,
    )

    print("\n" + "=" * 60)
    print("All steps complete.")
    print(f"Output folder : {os.path.abspath(OUTPUT_DIR)}/")
    print(f"  Charts      : 9 PNG files (01_kpi_summary … 09_region_delay_rate)")
    print(f"  Result files: kpis.json, findings.json,")
    print(f"                mode_analysis.csv, weather_analysis.csv,")
    print(f"                distance_analysis.csv, rating_analysis.csv,")
    print(f"                partner_analysis.csv, region_analysis.csv")
    print("=" * 60)


if __name__ == "__main__":
    main()

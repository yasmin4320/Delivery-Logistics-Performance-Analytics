# Delivery Logistics Performance & Delay Analytics

**BharatCares Data Analytics with AI — Internship Project**

---

## 1. Project Overview

This project analyzes a synthetic delivery-logistics dataset to understand patterns in delivery delays, delivery performance across modes, weather conditions, distance bands, customer satisfaction ratings, delivery partners, regions, and delivery costs.

The dataset contains **25,000 delivery records** spanning 9 delivery partners, 4 delivery modes, 6 weather conditions, and 5 regions.

> **Important:** The dataset used in this project is **synthetic** (artificially generated). All findings, patterns, and observations described here reflect the characteristics of this dataset only. They do not represent the real-world performance, operations, or reputation of any logistics company named in the data.

---

## 2. Objectives

- Measure the overall delivery delay rate and key performance indicators.
- Analyze delay patterns by delivery mode.
- Examine the association between weather conditions and delivery delays.
- Analyze the relationship between delivery distance and performance (time, cost, delay rate).
- Examine the association between delivery time and customer ratings.
- Analyze observed delay-rate variation across delivery partners and regions.
- Identify useful business observations from the data.
- Create clear visualizations to support decision-making.

---

## 3. Dataset

### Raw Dataset: `Delivery_Logistics.csv`

| Property | Value |
|---|---|
| Rows | 25,000 |
| Columns | 15 |
| Source | Synthetic dataset — [Delivery_Logistics.csv](Delivery_Logistics.csv)

### Columns

| Column | Description |
|---|---|
| `delivery_id` | Delivery identifier (not a unique key in this dataset) |
| `delivery_partner` | Logistics company name |
| `package_type` | Category of the package (e.g., groceries, electronics) |
| `vehicle_type` | Vehicle used for delivery (e.g., bike, truck, ev van) |
| `delivery_mode` | Service tier: same day, express, two day, standard |
| `region` | Geographic region: north, south, east, west, central |
| `weather_condition` | Weather at delivery time: clear, cold, foggy, hot, rainy, stormy |
| `distance_km` | Distance between origin and destination (km) |
| `package_weight_kg` | Weight of the package (kg) |
| `delivery_time_hours` | Actual delivery time (encoded; converted to numeric hours during cleaning) |
| `expected_time_hours` | Expected/SLA delivery time (encoded; converted to numeric hours during cleaning) |
| `delayed` | Original delay label: `yes` or `no` |
| `delivery_status` | Outcome: `delivered`, `delayed`, or `failed` |
| `delivery_rating` | Customer rating: 1 to 5 |
| `delivery_cost` | Delivery cost in Indian Rupees (₹) |

### Cleaned Dataset: `Delivery_Logistics_cleaned.csv`

The cleaned dataset adds 6 derived columns to support analysis:

| Added Column | Description |
|---|---|
| `delivery_time_hours_num` | Numeric hours extracted from the encoded `delivery_time_hours` field |
| `expected_time_hours_num` | Numeric hours extracted from the encoded `expected_time_hours` field |
| `zero_hour_flag` | 1 if actual delivery time was zero (255 records flagged as missing actual time) |
| `is_delayed_flag` | 1 if `delivery_status == 'delayed'` |
| `delayed_original_binary` | 1 if `delayed == 'yes'` (binary version of the original field) |
| `computed_delayed` | 1 if actual time exceeded expected time (kept for reference; not used for business KPIs) |

The original raw dataset is preserved unchanged. All 25,000 records are retained — no rows are deleted.

---

## 4. Technologies Used

| Package | Purpose |
|---|---|
| Python 3 | Core language |
| [Pandas](https://pandas.pydata.org/) | Data loading, cleaning, grouping, and analysis |
| [NumPy](https://numpy.org/) | Numeric operations and NaN handling |
| [Matplotlib](https://matplotlib.org/) | Chart generation |

---

## 5. Project Workflow

1. **Load** the raw dataset (`Delivery_Logistics.csv`).
2. **Inspect** data structure, data types, missing values, duplicate IDs, and categorical distributions.
3. **Clean and transform** the delivery-time and expected-time fields from their encoded string format into numeric hours.
4. **Handle zero-hour records** — 255 records where actual delivery time was zero are flagged and treated as missing actual delivery time in the cleaned working data.
5. **Preserve the original `delayed` field** — this field is used as the source of truth for all business delay-rate calculations.
6. **Perform exploratory data analysis** — distributions, correlations, SLA-tier breakdowns, and data-quality observations.
7. **Calculate business KPIs** — overall delay rate, average times, average cost, average rating.
8. **Analyse delivery mode, weather, distance, customer experience, partners, and regions.**
9. **Generate visualizations** — 9 charts covering all key dimensions.
10. **Generate a structured findings report** (`findings.json`) with metrics, interpretations, and analytical cautions.

The original raw dataset is never overwritten at any step.

---

## 6. Key Results

All values are computed from the data. The `delayed` column (`yes`/`no`) is used as the source for delay-rate calculations throughout.

### Overall KPIs

| Metric | Value |
|---|---|
| Total deliveries | 25,000 |
| Overall delay rate (`delayed = yes`) | **26.68%** |
| Delivered | 18,331 (73.3%) |
| Delayed (status) | 5,341 (21.4%) |
| Failed | 1,328 (5.3%) |
| Average actual delivery time | 6.31 hours |
| Average expected / SLA time | 13.11 hours |
| Average delivery cost | ₹864.94 |
| Average delivery rating | 3.67 / 5 |

### Delivery Mode — observed delay rates

| Mode | Delay Rate | Avg Actual Time | Avg SLA Time |
|---|---|---|---|
| Express | 73.78% | 6.28 h | 4.52 h |
| Same Day | 32.54% | 6.33 h | 8.00 h |
| Two Day | 0.43% | 6.34 h | 16.00 h |
| Standard | 0.00% | 6.30 h | 24.00 h |

> **Observation:** Express mode is associated with the highest observed delay rate in this dataset (73.78%), while Standard mode shows 0%. This is a pattern in the data; the delivery mode itself cannot be concluded to cause delays without controlling for other variables.

### Weather — observed delay rates

| Condition | Delay Rate | Avg Delivery Time |
|---|---|---|
| Stormy | 41.45% | 8.81 h |
| Rainy | 37.35% | 7.80 h |
| Foggy | 30.32% | 6.49 h |
| Clear | 17.43% | 4.89 h |
| Hot | 17.12% | 4.87 h |
| Cold | 16.02% | 4.87 h |

> **Observation:** Adverse weather conditions (stormy, rainy, foggy) are associated with higher delay rates and longer average delivery times in this dataset. This is an observed association in synthetic data, not a causal claim.

### Distance — observed patterns

| Distance Band | Deliveries | Delay Rate | Avg Time | Avg Cost |
|---|---|---|---|---|
| 0–60 km | 4,920 | 17.36% | 3.42 h | ₹264.36 |
| 61–120 km | 5,044 | 19.85% | 4.74 h | ₹560.62 |
| 121–180 km | 5,053 | 26.04% | 6.29 h | ₹866.35 |
| 181–240 km | 4,960 | 31.75% | 7.69 h | ₹1,162.78 |
| 241–300 km | 5,023 | 38.28% | 9.25 h | ₹1,463.31 |

> **Observation:** Delivery cost, average delivery time, and observed delay rate all increase monotonically with distance in this dataset. This is a clear positive association.

### Customer Experience — delivery time vs rating

| Rating | Deliveries | Avg Delivery Time | Delay Rate |
|---|---|---|---|
| 1 | 920 | 8.13 h | 100.00% |
| 2 | 3,602 | 8.11 h | 100.00% |
| 3 | 5,773 | 6.53 h | 37.19% |
| 4 | 7,318 | 5.64 h | 0.00% |
| 5 | 7,387 | 5.69 h | 0.00% |

**Pearson correlation (delivery time vs rating): −0.2693**

> **Observation:** There is a weak negative association between delivery time and customer rating in this dataset — longer delivery times tend to correspond with lower ratings. This is a statistical association (r = −0.27); other factors such as cost, package condition, and communication also influence customer satisfaction and are not captured here.

### Partner — observed delay-rate range

Delay rates across 9 delivery partners range from **24.80% to 28.27%**, a spread of **3.47 percentage points**.

> **Observation:** There is modest variation in observed delay rates across partners. Because partners may operate in different regions, carry different package types, or handle different delivery modes, this spread reflects a descriptive pattern in the data — not an isolated or controlled measure of partner performance. No partner is ranked as best or worst.

### Region — observed delay-rate range

Delay rates across 5 regions range from **25.80% (east) to 27.25% (central)**, a spread of **1.45 percentage points**.

> **Observation:** Regional delay rates are very similar in this dataset. Differences may reflect varying mixes of partners, weather conditions, or delivery modes rather than geography alone.

---

## 7. Visualizations

All charts are saved to `business_analysis_outputs/`.

| File | Description |
|---|---|
| `01_kpi_summary.png` | Tile grid showing all 6 overall KPIs at a glance |
| `02_delay_rate_by_mode.png` | Horizontal bar chart — delay rate per delivery mode vs overall average |
| `03_delay_rate_by_weather.png` | Horizontal bar chart — delay rate per weather condition vs overall average |
| `04_distance_vs_delivery_time.png` | Vertical bar chart — average delivery time per distance band, with delay rate annotated |
| `05_distance_vs_delivery_cost.png` | Vertical bar chart — average delivery cost per distance band |
| `06_delivery_time_vs_rating.png` | Line chart — average delivery time per rating (1–5), with Pearson r in the title |
| `07_delivery_status_distribution.png` | Pie chart — proportion of delivered / delayed / failed orders |
| `08_partner_delay_rate.png` | Vertical bar chart — delay rate per delivery partner vs overall average |
| `09_region_delay_rate.png` | Vertical bar chart — delay rate per region vs overall average |

---

## 8. Project Files

```
.
├── SafwanaYasmin_DeliveryLogisticsPerformanceAnalytics.py            # Complete analysis workflow (single runnable script)
├── requirements.txt                   # Required Python packages
├── Delivery_Logistics.csv             # Original raw dataset (never modified)
├── Delivery_Logistics_cleaned.csv     # Cleaned working dataset (25,000 rows × 21 cols)
├── business_analysis_outputs/
│   ├── 01_kpi_summary.png
│   ├── 02_delay_rate_by_mode.png
│   ├── 03_delay_rate_by_weather.png
│   ├── 04_distance_vs_delivery_time.png
│   ├── 05_distance_vs_delivery_cost.png
│   ├── 06_delivery_time_vs_rating.png
│   ├── 07_delivery_status_distribution.png
│   ├── 08_partner_delay_rate.png
│   ├── 09_region_delay_rate.png
│   ├── kpis.json                      # Overall KPI values
│   ├── findings.json                  # Structured findings with metrics and interpretations
│   ├── mode_analysis.csv              # Delay and time metrics by delivery mode
│   ├── weather_analysis.csv           # Delay and time metrics by weather condition
│   ├── distance_analysis.csv          # Delay, time, and cost metrics by distance band
│   ├── rating_analysis.csv            # Delivery time and delay rate by customer rating
│   ├── partner_analysis.csv           # Delay rate and average rating by delivery partner
│   └── region_analysis.csv            # Delay rate and average rating by region
├── process_logistics.py               # Data-cleaning script
├── eda_report.py                      # Preliminary data-inspection script
├── eda_logistics.py                   # Full EDA script
└── eda_results.json                   # Saved EDA output
```

---

## 9. How to Run the Project

### Prerequisites

- Python 3.8 or later
- The raw dataset file `Delivery_Logistics.csv` must be present in the same directory as the script

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the full analysis

```bash
python SafwanaYasmin_DeliveryLogisticsPerformanceAnalytics.py
```

The script will:
1. Load and clean the raw data from scratch.
2. Print a full EDA report and business analysis to the console.
3. Save all 9 charts and 8 result files to `business_analysis_outputs/`.

> **Note:** Running the script regenerates all output files in `business_analysis_outputs/`. The raw dataset (`Delivery_Logistics.csv`) and cleaned dataset (`Delivery_Logistics_cleaned.csv`) are never modified.

---

## 10. Analytical Caveats

- All findings are **observations from a synthetic dataset** and should not be interpreted as real-world performance data.
- **Correlation is not causation.** Where this README describes an association between two variables (e.g., weather and delay rate), this does not imply that one causes the other.
- Confounding variables (e.g., region mix, package type, delivery mode) are not controlled for in the group-level comparisons.
- No machine learning or predictive modelling is applied in this project.

# Hotel Booking Cancellation Analysis

## Project Overview
- **Project Name:** Hotel Booking Cancellation Analysis
- **Domain:** Hospitality
- **Core Business Question:** *Why do guests cancel their bookings?*
- **Dataset:** Kaggle Hotel Booking Demand (Optimized with a stratified limit of 15,000 records preserving exact Hotel & Cancellation distributions)
- **Database Architecture:** Relational SQLite Database (`database/hotel_cancellations.db`) with 4 distinct tables:
  1. `bookings` (core transactional records, lead time, arrival dates, ADR, deposit type, special requests)
  2. `customers` (customer demographics, repeated guest status, previous cancellations, family composition)
  3. `rooms` (reserved room type, assigned room type, room mismatch detection, meal plan)
  4. `channels` (market segment, distribution channel, booking agent ID, company ID)

---

## Directory Structure
```
hotel booking cancelation/
├── data/
│   ├── raw/
│   │   └── hotel_bookings.csv
│   └── processed/
│       ├── bookings.csv
│       ├── customers.csv
│       ├── rooms.csv
│       ├── channels.csv
│       └── hotel_bookings_master.csv
├── database/
│   └── hotel_cancellations.db
├── scripts/
│   ├── 01_data_pipeline.py
│   └── 02_statistical_analysis.py
├── reports/
│   ├── figures/
│   │   ├── fig1_overall_cancellation_breakdown.png
│   │   ├── fig2_lead_time_impact.png
│   │   ├── fig3_deposit_and_adr_analysis.png
│   │   ├── fig4_channels_and_segments.png
│   │   ├── fig5_behavioral_and_loyalty_drivers.png
│   │   ├── fig6_monthly_seasonality.png
│   │   └── fig7_feature_importance_drivers.png
│   └── output/
│       └── model_summary.json
└── README.md
```

---

## Executive Summary of Findings

### 1. Overall Cancellation Scale
- **Total Bookings Analyzed:** 15,000
- **Total Cancellations:** 5,556
- **Global Cancellation Rate:** 37.04%
- **Hotel Disparity:** City Hotels suffer a cancellation rate of **41.73%**, compared to **27.76%** for Resort Hotels.

### 2. Why Do Guests Cancel? (Key Drivers Ranked)
1. **Lead Time Horizon (The Primary Behavioral Driver, Feature Importance: 0.246):**
   - Bookings made **0–7 days** in advance cancel only **13.1%** of the time.
   - Bookings made **>180 days** in advance cancel at **68.7%**.
   - *Behavioral Cause:* Guests reserve rooms far in advance using lenient cancellation policies as a risk-free placeholder. They shop continuously for alternative deals and cancel when itineraries shift or lower rates appear.
2. **Distribution Channel Fragility:**
   - **Online Travel Agencies (OTAs):** Cancellation rate of **41.7%** due to aggressive in-app price-drop alerts and frictionless one-click cancellations.
   - **Direct Bookings:** Cancellation rate of only **17.5%**, reflecting direct brand commitment.
3. **The Non-Refundable Deposit Paradox:**
   - Non-refundable deposit bookings showed a **99.36% cancellation rate** due to adverse selection: hotels applied strict non-refundable terms primarily to volatile third-party group blocks and high-risk peak events. When tour operators failed to fill packages, reservations defaulted.
4. **Price Sensitivity (ADR):**
   - Canceled bookings averaged a higher rate (€104.96) compared to confirmed stays (€99.98). Guests booked at premium rates exhibit sharper price elasticity.
5. **Operational Dampeners (Buffers Against Cancellation):**
   - **Complimentary Upgrades:** When assigned room type differs from reserved room type, cancellation plummets to **5.4%** (vs 41.6% when matched).
   - **Special Requests:** Guests submitting 2+ special requests cancel at only **15.6%** (vs 47.7% for 0 requests).
   - **Repeat Guests:** Returning visitors cancel at only **14.4%** (vs 37.8% for first-time guests).

---

## Machine Learning Results
- **Model:** Random Forest Classifier (100 Trees, Max Depth 14)
- **Accuracy:** **81.53%** on unseen holdout test data
- **ROC-AUC Score:** **0.8964** (Strong ranking and classification power)
- **Top 3 Quantitative Predictors:**
  1. Lead Time (Gini: 0.246)
  2. Average Daily Rate (ADR) (Gini: 0.134)
  3. Non-Refundable Deposit Type (Gini: 0.119)

---

## Execution Instructions

To run the pipeline and analytics:
```bash
# 1. Run Data Normalization Pipeline & Build SQLite Database
python scripts/01_data_pipeline.py

# 2. Run Statistical Analysis, Train ML Model & Output Charts
python scripts/02_statistical_analysis.py
```

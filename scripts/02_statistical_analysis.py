"""
Statistical Analysis & Machine Learning Modeling on Hotel Booking Cancellations
Answers the core business question: WHY GUEST CANCEL THE BOOKINGS?
- Analyzes key drivers across Customers, Channels, Rooms, and Booking Behavior
- Evaluates machine learning models (Random Forest, Logistic Regression) to compute Feature Importances and Odds Ratios
- Produces high-resolution visualization charts for the 7-8 page executive report
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler

# Set aesthetic styling for charts
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 12

FIGURES_DIR = 'reports/figures'
os.makedirs(FIGURES_DIR, exist_ok=True)

def run_analysis_and_generate_figures():
    conn = sqlite3.connect('database/hotel_cancellations.db')
    
    # Query merged analytical view from the 4 tables
    query = """
    SELECT 
        b.booking_id,
        b.hotel,
        b.is_canceled,
        b.lead_time,
        b.arrival_date_year,
        b.arrival_date_month,
        b.total_nights,
        b.deposit_type,
        b.days_in_waiting_list,
        b.booking_changes,
        b.adr,
        b.required_car_parking_spaces,
        b.total_of_special_requests,
        c.country,
        c.customer_type,
        c.is_repeated_guest,
        c.previous_cancellations,
        c.previous_bookings_not_canceled,
        c.total_guests,
        ch.distribution_channel,
        ch.market_segment,
        r.reserved_room_type,
        r.assigned_room_type,
        r.room_type_mismatch,
        r.meal
    FROM bookings b
    JOIN customers c ON b.customer_id = c.customer_id
    JOIN channels ch ON b.channel_id = ch.channel_id
    JOIN rooms r ON b.room_id = r.room_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"Loaded merged relational analytical dataset: {df.shape}")

    # Summary Stats
    total_bookings = len(df)
    cancellations = df['is_canceled'].sum()
    cancel_rate = (cancellations / total_bookings) * 100
    print(f"Total: {total_bookings}, Canceled: {cancellations}, Rate: {cancel_rate:.2f}%")

    # -------------------------------------------------------------
    # FIGURE 1: Overall Cancellation Rate & Hotel Type Comparison
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    # Pie chart overall
    cancel_counts = df['is_canceled'].value_counts()
    axes[0].pie(
        cancel_counts, 
        labels=['Confirmed / Checked Out', 'Canceled'],
        autopct='%1.1f%%',
        startangle=140,
        colors=['#2ecc71', '#e74c3c'],
        explode=(0, 0.08),
        wedgeprops=dict(edgecolor='w', linewidth=2)
    )
    axes[0].set_title("Overall Booking Outcome Proportion")

    # Hotel type comparison
    hotel_cancel = df.groupby('hotel')['is_canceled'].value_counts(normalize=True).unstack() * 100
    hotel_cancel.plot(kind='bar', stacked=True, ax=axes[1], color=['#2ecc71', '#e74c3c'], edgecolor='black', alpha=0.9)
    axes[1].set_title("Cancellation Rate by Hotel Type")
    axes[1].set_xlabel("Hotel Type")
    axes[1].set_ylabel("Percentage (%)")
    axes[1].legend(['Confirmed', 'Canceled'], loc='upper right')
    for p in axes[1].patches:
        width, height = p.get_width(), p.get_height()
        if height > 5:
            axes[1].text(p.get_x() + width/2, p.get_y() + height/2, f"{height:.1f}%", ha='center', va='center', color='white', fontweight='bold')
    
    plt.tight_layout()
    fig1_path = os.path.join(FIGURES_DIR, "fig1_overall_cancellation_breakdown.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print("Saved Figure 1")

    # -------------------------------------------------------------
    # FIGURE 2: Lead Time Impact (The Strongest Driver)
    # -------------------------------------------------------------
    plt.figure(figsize=(11, 5))
    df['lead_time_bucket'] = pd.cut(
        df['lead_time'], 
        bins=[-1, 7, 30, 90, 180, 365, 1000],
        labels=['0-7 Days', '8-30 Days', '31-90 Days', '91-180 Days', '181-365 Days', '365+ Days']
    )
    lead_summary = df.groupby('lead_time_bucket', observed=False)['is_canceled'].agg(['count', 'mean']).reset_index()
    lead_summary['mean'] = lead_summary['mean'] * 100

    ax1 = sns.barplot(data=lead_summary, x='lead_time_bucket', y='mean', palette='Reds', edgecolor='black')
    plt.title("Cancellation Probability vs. Booking Lead Time Buckets")
    plt.xlabel("Lead Time Duration Ahead of Arrival")
    plt.ylabel("Cancellation Rate (%)")
    plt.ylim(0, 100)
    for p in ax1.patches:
        ax1.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=11, fontweight='bold', xytext=(0, 3),
                     textcoords='offset points')
    
    plt.tight_layout()
    fig2_path = os.path.join(FIGURES_DIR, "fig2_lead_time_impact.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print("Saved Figure 2")

    # -------------------------------------------------------------
    # FIGURE 3: Deposit Type & Pricing (ADR) Paradox
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Deposit Type Rate
    dep_summary = df.groupby('deposit_type')['is_canceled'].agg(['count', 'mean']).reset_index()
    dep_summary['mean'] = dep_summary['mean'] * 100
    sns.barplot(data=dep_summary, x='deposit_type', y='mean', ax=axes[0], palette='Purples_d', edgecolor='black')
    axes[0].set_title("Cancellation Rate by Deposit Policy")
    axes[0].set_xlabel("Deposit Type")
    axes[0].set_ylabel("Cancellation Rate (%)")
    axes[0].set_ylim(0, 105)
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=10, fontweight='bold', xytext=(0, 3),
                         textcoords='offset points')

    # ADR Boxplot (filter extreme outliers for clean view)
    df_filtered_adr = df[(df['adr'] > 0) & (df['adr'] < 400)]
    sns.boxplot(data=df_filtered_adr, x='is_canceled', y='adr', ax=axes[1], palette=['#2ecc71', '#e74c3c'])
    axes[1].set_title("Average Daily Rate (ADR in €) by Cancellation Status")
    axes[1].set_xticklabels(['Confirmed (0)', 'Canceled (1)'])
    axes[1].set_xlabel("Outcome")
    axes[1].set_ylabel("Daily Rate (€)")

    plt.tight_layout()
    fig3_path = os.path.join(FIGURES_DIR, "fig3_deposit_and_adr_analysis.png")
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print("Saved Figure 3")

    # -------------------------------------------------------------
    # FIGURE 4: Distribution Channels & Market Segments
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    channel_summary = df.groupby('distribution_channel')['is_canceled'].agg(['count', 'mean']).reset_index()
    channel_summary['mean'] = channel_summary['mean'] * 100
    channel_summary = channel_summary.sort_values('mean', ascending=False)
    sns.barplot(data=channel_summary, x='distribution_channel', y='mean', ax=axes[0], palette='Blues_r', edgecolor='black')
    axes[0].set_title("Cancellation Rate by Distribution Channel")
    axes[0].set_xlabel("Distribution Channel")
    axes[0].set_ylabel("Cancellation Rate (%)")
    axes[0].set_ylim(0, 50)
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=10, fontweight='bold', xytext=(0, 2),
                         textcoords='offset points')

    # Market Segment
    mkt_summary = df.groupby('market_segment')['is_canceled'].agg(['count', 'mean']).reset_index()
    mkt_summary['mean'] = mkt_summary['mean'] * 100
    mkt_summary = mkt_summary.sort_values('mean', ascending=False)
    sns.barplot(data=mkt_summary, x='market_segment', y='mean', ax=axes[1], palette='Oranges_r', edgecolor='black')
    axes[1].set_title("Cancellation Rate by Market Segment")
    axes[1].set_xlabel("Market Segment")
    axes[1].set_ylabel("Cancellation Rate (%)")
    axes[1].tick_params(axis='x', rotation=35)
    for p in axes[1].patches:
        axes[1].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold', xytext=(0, 2),
                         textcoords='offset points')

    plt.tight_layout()
    fig4_path = os.path.join(FIGURES_DIR, "fig4_channels_and_segments.png")
    plt.savefig(fig4_path, dpi=300)
    plt.close()
    print("Saved Figure 4")

    # -------------------------------------------------------------
    # FIGURE 5: Customer Loyalty, Room Mismatch & Special Requests
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # Repeat Guest
    rep_summary = df.groupby('is_repeated_guest')['is_canceled'].agg(['count', 'mean']).reset_index()
    rep_summary['mean'] = rep_summary['mean'] * 100
    rep_summary['label'] = ['First-Time Guest', 'Repeated Guest']
    sns.barplot(data=rep_summary, x='label', y='mean', ax=axes[0], palette=['#e67e22', '#27ae60'], edgecolor='black')
    axes[0].set_title("First-Time vs. Repeated Guests")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Cancellation Rate (%)")
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=11, fontweight='bold', xytext=(0, 2),
                         textcoords='offset points')

    # Room Mismatch
    mismatch_summary = df.groupby('room_type_mismatch')['is_canceled'].agg(['count', 'mean']).reset_index()
    mismatch_summary['mean'] = mismatch_summary['mean'] * 100
    mismatch_summary['label'] = ['Room Matched', 'Room Upgraded/Different']
    sns.barplot(data=mismatch_summary, x='label', y='mean', ax=axes[1], palette=['#e74c3c', '#2ecc71'], edgecolor='black')
    axes[1].set_title("Room Assignment Match vs Mismatch")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Cancellation Rate (%)")
    for p in axes[1].patches:
        axes[1].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=11, fontweight='bold', xytext=(0, 2),
                         textcoords='offset points')

    # Special requests
    sr_summary = df.groupby('total_of_special_requests')['is_canceled'].agg(['count', 'mean']).reset_index()
    sr_summary['mean'] = sr_summary['mean'] * 100
    sns.barplot(data=sr_summary, x='total_of_special_requests', y='mean', ax=axes[2], hue='total_of_special_requests', palette='viridis', legend=False, edgecolor='black')
    axes[2].set_title("Cancellation Rate by Number of Special Requests")
    axes[2].set_xlabel("Number of Special Requests")
    axes[2].set_ylabel("Cancellation Rate (%)")
    for p in axes[2].patches:
        axes[2].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=10, fontweight='bold', xytext=(0, 2),
                         textcoords='offset points')

    plt.tight_layout()
    fig5_path = os.path.join(FIGURES_DIR, "fig5_behavioral_and_loyalty_drivers.png")
    plt.savefig(fig5_path, dpi=300)
    plt.close()
    print("Saved Figure 5")

    # -------------------------------------------------------------
    # FIGURE 6: Monthly Seasonality of Cancellations
    # -------------------------------------------------------------
    plt.figure(figsize=(12, 5))
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly = df.groupby('arrival_date_month')['is_canceled'].agg(['count', 'mean']).reindex(month_order).reset_index()
    monthly['mean'] = monthly['mean'] * 100

    ax = sns.lineplot(data=monthly, x='arrival_date_month', y='mean', marker='o', linewidth=3, color='#c0392b')
    plt.title("Seasonal Cancellation Rate Fluctuations by Arrival Month")
    plt.xlabel("Month of Arrival")
    plt.ylabel("Cancellation Rate (%)")
    plt.xticks(rotation=40)
    plt.ylim(25, 45)
    for i, row in monthly.iterrows():
        ax.annotate(f"{row['mean']:.1f}%", (row['arrival_date_month'], row['mean']),
                    textcoords="offset points", xytext=(0, 8), ha='center', fontweight='bold', color='#c0392b')
    
    plt.tight_layout()
    fig6_path = os.path.join(FIGURES_DIR, "fig6_monthly_seasonality.png")
    plt.savefig(fig6_path, dpi=300)
    plt.close()
    print("Saved Figure 6")

    # -------------------------------------------------------------
    # MACHINE LEARNING MODEL & FEATURE IMPORTANCE
    # -------------------------------------------------------------
    print("Training Machine Learning Model for Root-Cause Identification...")
    feature_cols = [
        'lead_time', 'total_nights', 'booking_changes', 'days_in_waiting_list',
        'adr', 'required_car_parking_spaces', 'total_of_special_requests',
        'is_repeated_guest', 'previous_cancellations', 'previous_bookings_not_canceled',
        'total_guests', 'room_type_mismatch'
    ]
    
    # Categorical variables encoded
    cat_cols = ['hotel', 'deposit_type', 'customer_type', 'distribution_channel']
    df_encoded = pd.get_dummies(df[feature_cols + cat_cols], drop_first=True)
    
    X = df_encoded
    y = df['is_canceled']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    rf_model = RandomForestClassifier(n_estimators=100, max_depth=14, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)

    y_pred = rf_model.predict(X_test)
    y_prob = rf_model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    print(f"Random Forest Accuracy: {acc:.4f}, ROC AUC: {roc_auc:.4f}")

    # Feature Importance Plot
    importances = pd.Series(rf_model.feature_importances_, index=X.columns).sort_values(ascending=False).head(12)
    
    plt.figure(figsize=(11, 6))
    ax = sns.barplot(x=importances.values, y=importances.index, palette='magma')
    plt.title("Top 12 Quantitative Drivers of Hotel Cancellations (Random Forest Feature Importance)")
    plt.xlabel("Gini Importance Score")
    plt.ylabel("Predictor Variable")
    for p in ax.patches:
        ax.annotate(f"{p.get_width():.4f}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                    ha='left', va='center', fontsize=10, fontweight='bold', xytext=(4, 0),
                    textcoords='offset points')
    
    plt.tight_layout()
    fig7_path = os.path.join(FIGURES_DIR, "fig7_feature_importance_drivers.png")
    plt.savefig(fig7_path, dpi=300)
    plt.close()
    print("Saved Figure 7")

    # Save summary metrics to a dictionary / file for the report
    metrics = {
        'total_bookings': int(total_bookings),
        'cancellations': int(cancellations),
        'cancel_rate': f"{cancel_rate:.2f}%",
        'city_hotel_cancel_rate': f"{hotel_cancel.loc['City Hotel', 1]:.2f}%",
        'resort_hotel_cancel_rate': f"{hotel_cancel.loc['Resort Hotel', 1]:.2f}%",
        'rf_accuracy': f"{acc * 100:.2f}%",
        'rf_roc_auc': f"{roc_auc:.4f}",
        'top_features': list(importances.index[:5])
    }
    
    import json
    os.makedirs('reports/output', exist_ok=True)
    with open('reports/output/model_summary.json', 'w') as f:
        json.dump(metrics, f, indent=4)
    print("Metrics written to reports/output/model_summary.json")

if __name__ == '__main__':
    run_analysis_and_generate_figures()

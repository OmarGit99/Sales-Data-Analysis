"""
SkyGeni Sales Intelligence – EDA, Custom Metrics, and Win Rate Driver Analysis.
Run from the same directory as skygeni_sales_data.csv.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Load and prepare data
# ---------------------------------------------------------------------------
def load_data(path="skygeni_sales_data.csv"):
    df = pd.read_csv(path)
    df["created_date"] = pd.to_datetime(df["created_date"])
    df["closed_date"] = pd.to_datetime(df["closed_date"])
    df["outcome_binary"] = (df["outcome"] == "Won").astype(int)
    return df

df = load_data()

# ---------------------------------------------------------------------------
# Part 2a – Exploratory Data Analysis
# ---------------------------------------------------------------------------
def run_eda(df):
    print("=" * 60)
    print("PART 2 – EXPLORATORY DATA ANALYSIS")
    print("=" * 60)
    print("\n--- Dataset shape and types ---")
    print(df.shape)
    print(df.dtypes)
    print("\n--- Missing values ---")
    print(df.isnull().sum())
    print("\n--- Outcome distribution ---")
    print(df["outcome"].value_counts())
    print("\n--- Win rate (overall) ---")
    print(f"  {df['outcome_binary'].mean():.2%}")
    print("\n--- Key columns value counts ---")
    for col in ["region", "industry", "product_type", "lead_source", "deal_stage"]:
        print(f"\n{col}:")
        print(df[col].value_counts().head(8))
    print("\n--- Numeric summary ---")
    print(df[["deal_amount", "sales_cycle_days"]].describe())
    print("\n--- Date range ---")
    print(f"  created_date: {df['created_date'].min()} to {df['created_date'].max()}")
    print(f"  closed_date: {df['closed_date'].min()} to {df['closed_date'].max()}")

run_eda(df)

# ---------------------------------------------------------------------------
# Custom Metric 1: Segment Impact Score
# Volume-weighted "concern" – high volume + low win rate = high impact
# Formula: deal_count * (1 - win_rate) so we prioritize segments where we lose a lot
# ---------------------------------------------------------------------------
def segment_impact_score(df, segment_col):
    grp = df.groupby(segment_col).agg(
        deals=("deal_id", "count"),
        win_rate=("outcome_binary", "mean"),
    ).reset_index()
    grp["segment_impact_score"] = grp["deals"] * (1 - grp["win_rate"])
    grp = grp.sort_values("segment_impact_score", ascending=False)
    return grp

print("\n--- Custom Metric 1: Segment Impact Score (by region) ---")
impact_region = segment_impact_score(df, "region")
print(impact_region.to_string(index=False))
print("\nInterpretation: Higher score = more deals lost in that segment (volume × loss rate).")
print("Use this to prioritize where to investigate or reallocate effort.")

# ---------------------------------------------------------------------------
# Custom Metric 2: Cycle–Outcome Gap
# Median sales_cycle_days (Won) vs (Lost) by segment; large gap = timing/process signal
# ---------------------------------------------------------------------------
def cycle_outcome_gap(df, segment_col):
    won = df[df["outcome"] == "Won"].groupby(segment_col)["sales_cycle_days"].median()
    lost = df[df["outcome"] == "Lost"].groupby(segment_col)["sales_cycle_days"].median()
    gap = (lost - won).reindex(won.index).fillna(0)
    return pd.DataFrame({"median_cycle_won": won, "median_cycle_lost": lost, "cycle_outcome_gap_days": gap})

print("\n--- Custom Metric 2: Cycle–Outcome Gap (by lead_source) ---")
gap_lead = cycle_outcome_gap(df, "lead_source")
print(gap_lead.sort_values("cycle_outcome_gap_days", ascending=False).to_string())
print("\nInterpretation: Positive gap = lost deals tend to have longer cycles in that segment.")
print("Suggests process or timing issues (e.g. slow follow-up, drawn-out negotiations).")

# ---------------------------------------------------------------------------
# Part 2b – Three meaningful business insights (plain language)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("THREE BUSINESS INSIGHTS")
print("=" * 60)

# Insight 1: Win rate by lead source
wr_source = df.groupby("lead_source")["outcome_binary"].agg(["mean", "count"]).round(4)
wr_source.columns = ["win_rate", "deals"]
wr_source = wr_source.sort_values("win_rate", ascending=False)
print("\n--- Insight 1: Win rate by lead source ---")
print(wr_source.to_string())
best_source = wr_source.index[0]
worst_source = wr_source.index[-1]
print(f"\nWhy it matters: Lead source is a strong signal of deal quality. {best_source} outperforms {worst_source}.")
print("Action: Increase investment in higher-win channels (e.g. Inbound, Referral) and review process for lower-win channels (e.g. Outbound, Partner).")

# Insight 2: Win rate trend over time (quarterly)
df["quarter"] = df["closed_date"].dt.to_period("Q")
wr_q = df.groupby("quarter")["outcome_binary"].agg(["mean", "count"]).reset_index()
wr_q.columns = ["quarter", "win_rate", "deals"]
print("\n--- Insight 2: Win rate by quarter ---")
print(wr_q.to_string(index=False))
if len(wr_q) >= 2:
    recent = wr_q["win_rate"].iloc[-1]
    older = wr_q["win_rate"].iloc[0]
    print(f"\nWhy it matters: Win rate moved from {older:.1%} (earliest) to {recent:.1%} (most recent).")
    print("Action: If dropping, combine with driver analysis to find which segments drove the change; if improving, double down on recent initiatives.")

# Insight 3: Win rate by region and volume
wr_region = df.groupby("region").agg(win_rate=("outcome_binary", "mean"), deals=("deal_id", "count")).sort_values("deals", ascending=False)
print("\n--- Insight 3: Win rate and volume by region ---")
print(wr_region.to_string())
print("\nWhy it matters: Regions with high volume but low win rate have the biggest revenue impact.")
print("Action: Use Segment Impact Score to rank regions; focus coaching and process on high-impact, low-win-rate regions.")

# ---------------------------------------------------------------------------
# Part 3 – Win Rate Driver Analysis (Option B)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("PART 3 – WIN RATE DRIVER ANALYSIS (DECISION ENGINE)")
print("=" * 60)

# Prepare features
model_df = df.copy()
for col in ["region", "industry", "product_type", "lead_source"]:
    model_df[col] = model_df[col].astype("category")

# Dummy encoding (drop first to avoid collinearity)
X = pd.get_dummies(model_df[["region", "industry", "product_type", "lead_source", "deal_amount", "sales_cycle_days"]], drop_first=True)
y = model_df["outcome_binary"]

# Handle any inf/nan
X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
coef = pd.DataFrame({"feature": X.columns, "coefficient": model.coef_[0]}).sort_values("coefficient", key=abs, ascending=False)

print("\n--- Top drivers (by absolute coefficient) ---")
print(coef.head(12).to_string(index=False))
print("\nPositive coefficient = associated with higher win rate; negative = lower win rate.")

# Marginal effect: approximate change in win probability per 1 std change in numeric features
# For binary dummies: switching from 0 to 1. We approximate with coefficient * 0.25 (typical for logit at mean)
print("\n--- How a sales leader would use this ---")
print("1. Use the ranked list to see which segments or factors hurt/help win rate most.")
print("2. Prioritize actions on the top negative drivers (e.g. long sales_cycle_days, certain regions/lead sources).")
print("3. Reinforce positive drivers (e.g. Referral, Partner) and replicate what works in underperforming segments.")
print("4. Re-run this analysis quarterly to see if drivers change as the business evolves.")

# Simple accuracy for reference (we care about interpretation, not Kaggle-style accuracy)
acc = model.score(X_test, y_test)
print(f"\nModel accuracy (test): {acc:.2%} – used for sanity check; focus on interpretability for the CRO.")

print("\n" + "=" * 60)
print("END OF ANALYSIS")
print("=" * 60)

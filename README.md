# Sales Intelligence

---

## Part 1 – Problem Framing

### 1. What do you think is the real business problem here?

The real problem is **diagnostic and decision clarity**, not just “win rate is down.” The CRO has two signals (win rate down, pipeline volume healthy) but no causal story. So the real business problem is:

- **Uncertainty about why** win rate dropped (which segments, reps, or motions are underperforming).
- **Uncertainty about what to do** (where to coach, where to reallocate effort, and what to fix first).

Until the CRO can tie the drop to specific levers (e.g., “Enterprise in APAC,” “long-cycle Outbound,” “certain reps”), they cannot take targeted action. So the problem is: **turn “something is wrong” into “here’s what’s wrong and what to do about it.”**

### 2. What key questions should an AI system answer for the CRO?

- **Why did win rate drop?**  
  Which dimensions (region, industry, product, lead source, deal size, cycle length, rep) explain most of the change?

- **Where is the biggest risk?**  
  Which segments or deal types have both high volume and low/declining win rate (biggest revenue impact)?

- **What should we do first?**  
  Ranked actions: e.g., “Focus coaching on X,” “Reduce investment in Y,” “Fix process for Z.”

- **Is this a trend or noise?**  
  Is the drop sustained over time or concentrated in a period? Are there leading indicators (e.g., stage velocity, drop-off by stage)?

- **Who needs to act?**  
  Which reps, regions, or teams are driving the drop vs. holding steady?

### 3. What metrics matter most for diagnosing win rate issues?

- **Win rate by segment** (region, industry, product_type, lead_source, deal_stage) — to find where we’re losing.
- **Win rate over time** (by quarter/month) — to confirm trend and timing.
- **Deal volume by segment** — so we weight impact (low win rate with high volume matters more).
- **Sales cycle length** (e.g., median days by outcome and segment) — long cycles often correlate with lower win rate and higher risk.
- **Stage progression / conversion** — where deals stall or drop off (e.g., Demo → Proposal).
- **Revenue at risk** — e.g., (pipeline in segment × loss rate × average deal size) to prioritize segments.

### 4. What assumptions are you making about the data or business?

- **Data:**  
  - Outcomes (Won/Lost) and dates are accurate; no heavy selection bias (e.g., only certain deals logged).  
  - Segments (industry, region, product_type, lead_source) are consistently and correctly assigned.  
  - One row per deal; no double-counting.

- **Business:**  
  - “Win rate” is a meaningful lever (not purely price-driven or one-off big deals).  
  - Segments are actionable (we can change how we sell by region, product, lead source, etc.).  
  - Historical patterns are somewhat stable (so past drivers of win/loss are useful for near-term decisions).  
  - Pipeline “health” is not just volume — mix and segment quality matter.

---

## Part 2 – Data Exploration & Insights

See **`analysis.py`** for full EDA. Summary:

- **3 business insights** (with plain-language “why it matters” and “what action”) are in the script output and summarized in “Key insights” below.
- **2 custom metrics** are defined and computed in code:
  - **Segment Impact Score** — combines win rate and volume so high-volume, low-win-rate segments surface first.
  - **Cycle–Outcome Gap** — difference in median sales cycle (days) between Won and Lost in a segment; large gap suggests process or timing issues.

Run:

```bash
pip install -r requirements.txt
python analysis.py
```

---

## Part 3 – Decision Engine (Option B: Win Rate Driver Analysis)

**Chosen option:** **B – Win Rate Driver Analysis.**

- **Problem:** Identify which factors (region, industry, product_type, lead_source, deal amount, sales_cycle_days) are associated with higher or lower win rate, and quantify their effect so the CRO can prioritize actions.

- **Approach:**  
  - Logistic regression of `outcome` (Won=1, Lost=0) on categorical and numeric features.  
  - Coefficients and marginal effects show **which factors hurt or help** win rate and by how much.  
  - Results are translated into plain-language drivers and a short “what to do” list.

- **Outputs:**  
  - Ranked drivers (positive and negative).  
  - Example: “Referral leads improve win rate by X pp; long sales cycles reduce it by Y pp.”  
  - How a sales leader would use this is described in the script and in “How a sales leader would use this” below.

- **How a sales leader would use this:**  
  - Use the ranked drivers to decide where to invest (e.g., more Referral, better process for long-cycle deals).  
  - Combine with Segment Impact Score to focus on high-impact segments first.  
  - Re-run periodically (e.g., quarterly) to see if drivers change.

Implementation and interpretation are in **`analysis.py`** (same script as Part 2).

---

## Part 4 – Mini System Design: Sales Insight & Alert System

### High-level architecture

- **Data layer:** CRM / sales tool (e.g., Salesforce) → batch sync (nightly or every 6h) into a warehouse or lake (e.g., BigQuery, Snowflake, S3 + Athena).  
- **Compute layer:**  
  - ETL + feature prep (Python/Spark).  
  - Insight jobs: win rate by segment, trend over time, Segment Impact Score, Cycle–Outcome Gap, Win Rate Driver model.  
  - Alert engine: rules on thresholds (e.g., “win rate in segment X below Y%” or “driver Z flipped sign”).  
- **Serving layer:**  
  - Cached dashboards (e.g., Tableau, Metabase, or internal app).  
  - Alerts via email/Slack; optional digest (“Weekly Sales Health”).

```
[CRM] → [Sync] → [Warehouse] → [Feature prep] → [Insight + Model jobs]
                                                      ↓
[Alert engine] ← [Thresholds / rules]    [Dashboards] ← [Cached metrics]
     ↓                    ↓
[Slack/Email]        [CRO / Sales leaders]
```

### Data flow

1. **Ingest:** Deals, contacts, activities (if available) synced on a schedule.  
2. **Clean & enrich:** Standardize segments, compute sales_cycle_days, outcome, deal_amount.  
3. **Aggregate:** Win rate, volume, and custom metrics by segment and time.  
4. **Model:** Win rate driver model (and optionally risk score) refreshed on same schedule.  
5. **Evaluate rules:** Compare metrics to baselines and thresholds; trigger alerts.  
6. **Deliver:** Dashboards updated; alerts sent.

### Example alerts / insights

- “Win rate in **APAC Enterprise** dropped below 35% this quarter (baseline 42%).”  
- “**Outbound** win rate is 8 pp below **Referral**; consider rebalancing lead mix.”  
- “Deals with **sales cycle > 90 days** have 20% lower win rate; review stage velocity.”  
- “**Segment Impact Score** top risk: HealthTech + Europe (high volume, low win rate).”

### How often it runs

- **Batch sync:** e.g., nightly or every 6 hours.  
- **Insight + model refresh:** same frequency or weekly for heavier models.  
- **Alerts:** evaluated after each refresh; digest optionally weekly.

### Failure cases and limitations

- **Data quality:** Missing or wrong segment labels, duplicate deals, or delayed closes → wrong win rates and drivers. Mitigation: validation checks, anomaly detection on input.  
- **Staleness:** If sync or job fails, dashboards and alerts are outdated. Mitigation: monitoring, retries, fallback to last good run.  
- **Over-alerting:** Too many or noisy alerts → ignored. Mitigation: few, high-signal rules; digest; configurable thresholds.  
- **Model drift:** Relationships between drivers and win rate change. Mitigation: periodic retrain and monitor coefficient stability.  
- **Selection bias:** Only closed deals in data; open pipeline not in outcome model. Mitigation: separate pipeline metrics and risk model if needed.

---

## Part 5 – Reflection

1. **Weakest assumptions:**  
   - That historical win/loss drivers are stable; a market or product shift could make past drivers less relevant.  
   - That segment labels are accurate and actionable; misclassification or fuzzy definitions would weaken recommendations.

2. **What would break in production:**  
   - Schema or field changes from the CRM breaking ETL.  
   - Large volume or late-arriving data slowing batch jobs.  
   - Alert rules too sensitive (noise) or too loose (missed issues).  
   - Model trained on closed deals only, so not directly applicable to open pipeline without a separate risk layer.

3. **What I’d build next with 1 month:**  
   - **Deal-level risk score** for open pipeline (Option A) using the same features + driver model.  
   - **Automated segment discovery** (e.g., clusters of deals with similar win/loss behavior).  
   - **Causal checks** (e.g., difference-in-differences or simple experiments) to test “if we do X, does win rate improve?”  
   - **Dashboard + alert config UI** so the CRO can set thresholds and choose segments without code.

4. **Least confident part:**  
   - **Causality.** The driver analysis is associative; we don’t know that changing a factor (e.g., shortening cycle) will cause better win rate. I’d want more validation (e.g., A/B tests or quasi-experiments) before betting big on one lever.

---

## How to Run the Project

### Prerequisites

- Python 3.8+  
- pip

### Setup and run

```bash
pip install -r requirements.txt
python analysis.py
```

- **Input:** `skygeni_sales_data.csv` in the same directory.  
- **Output:** Console output with EDA summary, 3 insights, 2 custom metrics, and Win Rate Driver Analysis (ranked drivers and how to use them).  
- Optional: redirect to a file, e.g. `python analysis.py > report.txt`.

### Key files

| File | Purpose |
|------|--------|
| `README.md` | This file: framing, system design, reflection, run instructions |
| `analysis.py` | EDA, custom metrics, Win Rate Driver model |
| `skygeni_sales_data.csv` | Input data |
| `requirements.txt` | Python dependencies |

### Key decisions

- **Option B (Win Rate Driver Analysis)** chosen because it directly addresses “what is going wrong” and “what to focus on,” with interpretable outputs for the CRO.  
- **Custom metrics:** Segment Impact Score (volume-weighted win rate concern) and Cycle–Outcome Gap (process/timing signal).  
- **Model:** Logistic regression for interpretability and marginal effects; no black-box model to keep the focus on business usefulness and explanation.

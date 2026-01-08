## Research Questions & Key Performance Indicators

### RQ 1. Which contextual variables are most effective in classifying outliers into Harmful, Benign, and Strategic categories?

**KPI 1-1. Contextual Feature Importance Score**
- **Definition**: Relative contribution of contextual variables (customer_type, category, temporal_pattern) vs numerical features (quantity, price) in the classification model
- **Measurement**: `Σ(SHAP_contextual) / Σ(SHAP_all_features)`
- **Target**: Contextual features contribute >40% to classification decisions
- **Data Source**: Model feature importance from Random Forest/XGBoost + SHAP values

**KPI 1-2. Three-Way Classification Accuracy**
- **Definition**: Model accuracy in correctly classifying statistical outliers into three categories:
  - **Harmful**: Significantly distorts KPIs, likely data quality issues
  - **Benign**: Statistically extreme but business-neutral
  - **Strategic**: High-value transactions or strategic opportunities
- **Measurement**: `(TP_harmful + TP_benign + TP_strategic) / Total_outliers`
- **Target**: Class-specific accuracy targets:
  - Harmful detection: >85% (critical for data quality)
  - Strategic detection: >70% (valuable but harder to classify)
  - Benign detection: >65% (most ambiguous category)
  - Weighted average: ~75% overall
- **Validation**: Semi-automated labeling using rule-based criteria (see Ground Truth section) + stratified sampling (100 wholesaler + 100 private + 100 edge cases)

---

### RQ 2. To what extent do harmful outliers distort critical business KPIs compared to strategic and benign outliers?

**KPI 2-1. Harmful Outlier KPI Distortion Index (with Directionality)**
- **Definition**: Percentage change in key metrics (AOV, Total Revenue, Conversion Rate) caused by harmful outliers, including direction of bias
- **Measurement**:
  ```
  For each KPI:
  Distortion_Magnitude = |KPI_with_harmful - KPI_without_harmful| / KPI_without_harmful × 100%
  Distortion_Direction = (KPI_with_harmful - KPI_without_harmful) / KPI_without_harmful × 100%

  If Distortion_Direction > 0: "Overestimation" (과대평가)
  If Distortion_Direction < 0: "Underestimation" (과소평가)
  ```
- **Target**:
  - Magnitude: Harmful outliers cause >15% distortion, strategic outliers cause <5%
  - Direction: Report whether harmful outliers inflate or deflate each KPI
- **Metrics Analyzed**: Average Order Value (AOV), Total Revenue, Revenue per Customer
- **Business Interpretation:**
  - **Overestimation** → Risk of over-investing in marketing/inventory
  - **Underestimation** → Risk of missing high-value customer segments

**KPI 2-2. Harmful Outlier Detection Precision**
- **Definition**: Proportion of flagged harmful outliers that genuinely represent data quality issues
- **Measurement**:
  ```
  Precision = True_Harmful / (True_Harmful + False_Harmful)
  Recall = True_Harmful / (True_Harmful + Missed_Harmful)
  ```
- **Target**: Precision >80%, Recall >70%
- **Validation**: Cross-validation with domain rules (e.g., quantity > 10,000 for retail, price = 0)

**KPI 2-3. Temporal Data Quality Impact**
- **Definition**: Quantify impact of Thursday data anomaly on KPI distortion
- **Critical Finding**: Thursday transactions = 5,620 (vs. 60,000-85,000 for other days) → **~90% data loss**
- **Measurement**:
  ```
  For each KPI:
  KPI_with_thursday = Calculate including Thursday data
  KPI_without_thursday = Calculate excluding Thursday data
  Thursday_Impact = |KPI_with - KPI_without| / KPI_without × 100%
  ```
- **Data Quality Decision:**
  - **Option A (Recommended):** Exclude all Thursday data as "Harmful Period"
    - Rationale: 90% data loss suggests systemic collection failure
    - Reduces bias from incomplete day-of-week representation
  - **Option B:** Keep Thursday data but apply weighting correction
    - Weight = avg(other_days_txn) / thursday_txn ≈ 12.5x
    - Risky: assumes missing transactions have same distribution
  - **Option C:** Treat as natural low-traffic day and keep as-is
    - Unlikely: no business reason for 90% drop on Thursdays
- **Target**: Demonstrate Thursday exclusion reduces KPI variance by >X%
- **Implementation**: Document decision in preprocessing and run sensitivity analysis

---

### RQ 3. What is the business value of preserving strategic outliers compared to traditional blanket removal approaches?

**KPI 3-1. AOV Accuracy Improvement Rate (with Bias Direction)**
- **Definition**: Improvement in AOV estimation accuracy when using context-aware preservation vs blanket removal, including directional bias analysis
- **Measurement**:
  ```
  # Error Magnitude (existing)
  Baseline_Error_Mag = |AOV_blanket - AOV_ground_truth| / AOV_ground_truth
  Context_Error_Mag = |AOV_context - AOV_ground_truth| / AOV_ground_truth
  Improvement_Rate = (Baseline_Error_Mag - Context_Error_Mag) / Baseline_Error_Mag × 100%

  # Bias Direction (new)
  Baseline_Bias = (AOV_blanket - AOV_ground_truth) / AOV_ground_truth × 100%
  Context_Bias = (AOV_context - AOV_ground_truth) / AOV_ground_truth × 100%

  If Bias < 0: "Underestimation" (likely removing strategic outliers)
  If Bias > 0: "Overestimation" (likely keeping harmful outliers)
  ```
- **Target**:
  - Improvement Rate: >25%
  - **Expected Result**: Blanket removal causes underestimation (negative bias), context-aware corrects this
- **Ground Truth**: AOV calculated using robust estimator (5% trimmed mean) after removing only rule-based Harmful outliers
  - Rationale: Trimmed mean is less sensitive to extreme values while avoiding complete removal
  - Alternative: Use wholesaler-only AOV as benchmark for high-value segment
- **Business Insight:**
  - Negative bias in blanket removal → Lost revenue from strategic customers
  - Bias correction measures value recovered by context-aware approach

**KPI 3-2. Strategic Revenue Retention Rate**
- **Definition**: Percentage of revenue recovered from data points preserved as "strategic" that would have been removed under traditional methods
- **Measurement**:
  ```
  Retained_Revenue = Σ(line_total where outlier_class = 'Strategic')
  Total_Outlier_Revenue = Σ(line_total where is_statistical_outlier = True)
  Retention_Rate = Retained_Revenue / Total_Outlier_Revenue × 100%
  ```
- **Target**: Recover >30% of outlier-flagged revenue as strategic
- **Business Impact**: Quantify revenue that would be lost through indiscriminate outlier removal

**KPI 3-3. Customer Segment Value Preservation**
- **Definition**: Percentage of high-value customer transactions (wholesaler, bulk buyers) correctly preserved
- **Measurement**:
  ```
  Preserved_Wholesaler_Txn = COUNT(txn where customer_type='wholesaler' AND outlier_class='Strategic')
  Total_Wholesaler_Outliers = COUNT(txn where customer_type='wholesaler' AND is_outlier=True)
  Preservation_Rate = Preserved / Total × 100%
  ```
- **Target**: Preserve >90% of wholesaler transactions flagged as outliers
- **Rationale**: Wholesaler bulk orders are naturally extreme but strategically important

---

### RQ 4. How can SHAP-based explainability provide transparent and actionable justifications for outlier classification decisions?

**KPI 4-1. SHAP Feature Consistency Score**
- **Definition**: Consistency of top-3 SHAP features within each outlier cluster
- **Measurement**:
  ```
  For each cluster:
  Consistency = Frequency(top-3 features appear together) / Total_instances_in_cluster
  Average across all clusters
  ```
- **Target**: >80% consistency (revised from 95% for realism)
- **Interpretation**: High consistency indicates stable, interpretable decision patterns

**KPI 4-2. Business Rule Alignment Rate**
- **Definition**: Percentage of model classifications that align with predefined business logic rules
- **Business Rules**:
  - `customer_type = 'wholesaler' AND quantity > Q3 + 3×IQR → Strategic`
  - `price < 0.1 OR quantity > 10,000 → Harmful`
  - `category = 'seasonal' AND date in peak_season → Strategic`
- **Measurement**:
  ```
  Aligned_Cases = COUNT(model_prediction matches business_rule)
  Total_Rule_Applicable = COUNT(instances where rules apply)
  Alignment_Rate = Aligned / Total × 100%
  ```
- **Target**: >85% alignment rate
- **Purpose**: Validate that ML model learns genuine business patterns, not spurious correlations

**KPI 4-3. Explanation Stability Score**
- **Definition**: Stability of SHAP explanations when model is retrained on different data samples
- **Measurement**:
  ```
  Train 5 models with different 80% subsamples
  For same test instances, calculate:
  Stability = 1 - (StdDev of SHAP values across 5 models) / Mean(|SHAP values|)
  ```
- **Target**: Stability score >0.85
- **Rationale**: Ensures explanations are robust, not artifacts of specific training samples
Research Questions and Key Performance Indicators (RQ_KPI)

 - This document defines the research questions (RQs) and key performance indicators (KPIs) for the OutlierAnalytics project. The objective is to evaluate the impact of context-aware outlier handling on data quality, business KPIs, and analytical reliability compared to traditional statistical outlier removal approaches.


----

#RQ1: Can contextual information improve outlier classification compared to purely statistical methods?
Research Question

Can a context-aware machine learning approach classify outliers into harmful, benign, and strategic categories more effectively than purely statistical methods?

Description

Traditional outlier detection techniques rely on statistical thresholds and often fail to differentiate between data quality errors and legitimate high-value transactions. This research question evaluates whether incorporating contextual information such as customer type, product category, and seasonality improves outlier classification.

KPIs

KPI 1-1: Classification Performance

Precision, recall, and F1-score for each outlier class (harmful, benign, strategic).

Confusion matrix to analyze misclassification patterns.

KPI 1-2: Contextual Feature Contribution

Quantification of the contribution of contextual features using explainability techniques (e.g., SHAP or feature-importance-based methods) relative to numeric features.

----

#RQ2: How do harmful outliers distort key business KPIs?
Research Question

To what extent do harmful outliers distort key business KPIs such as revenue, average order value (AOV), and customer-level metrics?

Description

Harmful outliers caused by data quality issues can significantly bias business KPIs, leading to incorrect reporting and decision-making. This research question quantifies the magnitude and direction of such distortions.

KPIs

KPI 2-1: KPI Distortion Magnitude

Percentage distortion in revenue, AOV, and revenue per customer caused by harmful outliers.

KPI 2-2: Segment-Level Distortion

KPI distortion analyzed separately for different customer segments (e.g., private vs wholesaler).

KPI 2-3: Temporal Distortion Patterns

Variation in KPI distortion across time periods (e.g., daily or weekly trends).

----

#RQ3: What is the strategic value loss from blanket outlier removal?
Research Question

How much strategic business value is lost when blanket statistical outlier removal is applied instead of a context-aware removal strategy?

Description

Blanket outlier removal may eliminate legitimate high-value transactions, particularly for wholesalers or during peak sales periods. This research question evaluates the trade-off between data cleanliness and business value preservation.

KPIs

KPI 3-1: Strategic Revenue Retention

Percentage of outlier-associated revenue retained when using context-aware removal compared to blanket removal.

KPI 3-2: KPI Bias Comparison

Difference in AOV and revenue metrics between blanket and context-aware outlier handling.

KPI 3-3: Temporal and Category Impact

Analysis of retained strategic revenue across time periods and product categories.

----

#RQ4: Are context-aware outlier models explainable, stable, and aligned with business logic?
Research Question

Do context-aware outlier classification models produce explanations that are interpretable, stable across retraining, and aligned with predefined business rules?

Description

For real-world adoption, analytical models must be transparent, consistent, and aligned with domain knowledge. This research question evaluates explainability, stability, and business-rule alignment of the proposed models.

KPIs

KPI 4-1: Explanation Consistency

Stability of top contributing features across multiple model retraining runs, measured using interpretable feature-attribution techniques (e.g., SHAP or permutation-based methods).

KPI 4-2: Business Rule Alignment Rate

Percentage of model predictions that align with predefined business rules for identifying harmful and strategic transactions.

KPI 4-3: Prediction Stability

Proportion of instances whose predicted class remains unchanged across multiple model retraining runs.

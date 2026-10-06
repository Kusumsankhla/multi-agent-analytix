import math
from typing import Dict, Any, List, Optional, Tuple

class StatisticalEngine:
    """
    Automated Statistical Hypothesis Testing & Anomaly Detection Engine.
    Computes:
    - Formal Null (H0) and Alternative (H1) Hypotheses
    - Z-scores, p-values, and 95% Confidence Intervals
    - Statistical Significance Determination
    - Outlier Detection via IQR and Z-score metrics
    """

    @staticmethod
    def norm_cdf(x: float) -> float:
        """Standard normal cumulative distribution function using error function."""
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @classmethod
    def test_proportions(
        cls, 
        p1: float, 
        n1: int, 
        p2: float, 
        n2: int
    ) -> Dict[str, Any]:
        """
        Two-sample Z-test for difference in proportions.
        Used for comparing fraud rates, attrition rates, default rates, conversion rates.
        """
        if n1 <= 0 or n2 <= 0:
            return {"significant": False, "p_value": 1.0, "z_score": 0.0}

        # Normalize to [0, 1] if given as percentage
        val1 = p1 / 100.0 if p1 > 1.0 else p1
        val2 = p2 / 100.0 if p2 > 1.0 else p2

        pooled_p = (val1 * n1 + val2 * n2) / (n1 + n2)
        se = math.sqrt(pooled_p * (1.0 - pooled_p) * (1.0 / n1 + 1.0 / n2)) if pooled_p * (1.0 - pooled_p) > 0 else 0.0001
        
        z_stat = (val1 - val2) / se if se > 0 else 0.0
        p_val = 2.0 * (1.0 - cls.norm_cdf(abs(z_stat)))
        p_val = max(0.0001, min(1.0, p_val))

        is_sig = p_val < 0.05

        return {
            "z_score": round(z_stat, 3),
            "p_value": round(p_val, 4),
            "statistically_significant": is_sig,
            "confidence_level": "99%" if p_val < 0.01 else ("95%" if is_sig else "Not Significant"),
            "interpretation": f"The difference between {round(val1*100, 2)}% and {round(val2*100, 2)}% is "
                              f"{'statistically significant (p < 0.05)' if is_sig else 'within random sample variance (p >= 0.05)'}."
        }

    @classmethod
    def analyze_dataset_statistics(
        cls, 
        columns: List[str], 
        rows: List[List[Any]], 
        question: str
    ) -> Dict[str, Any]:
        """
        Generates automated statistical hypothesis testing, confidence intervals,
        and anomaly detection for the executed query result.
        """
        if not rows or len(columns) < 2:
            return {
                "has_stats": False,
                "summary": "Insufficient numeric dimensions for statistical tests."
            }

        # Find first numeric metric column
        metric_col_idx = None
        for idx in range(1, len(columns)):
            if any(isinstance(r[idx], (int, float)) for r in rows):
                metric_col_idx = idx
                break

        if metric_col_idx is None:
            return {
                "has_stats": False,
                "summary": "No numeric metric found for statistical tests."
            }

        dim_col = columns[0]
        metric_col = columns[metric_col_idx]
        
        # Extract numeric series
        series = []
        labels = []
        for r in rows:
            val = r[metric_col_idx]
            if isinstance(val, (int, float)):
                series.append(float(val))
                labels.append(str(r[0]))

        if len(series) < 2:
            return {
                "has_stats": False,
                "summary": "Need at least 2 distinct groups for statistical comparison."
            }

        n = len(series)
        mean_val = sum(series) / n
        variance = sum((x - mean_val) ** 2 for x in series) / (n - 1) if n > 1 else 0.0
        std_val = math.sqrt(variance)
        sorted_s = sorted(series)
        median_val = sorted_s[n // 2]

        # Interquartile Range (IQR) & Z-score Outlier Detection
        q1 = sorted_s[int(n * 0.25)]
        q3 = sorted_s[int(n * 0.75)]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomalies = []
        for label, val in zip(labels, series):
            z = (val - mean_val) / std_val if std_val > 0 else 0.0
            if abs(z) >= 1.8 or val > upper_bound or val < lower_bound:
                anomalies.append({
                    "entity": label,
                    "value": round(val, 2),
                    "z_score": round(z, 2),
                    "anomaly_type": "HIGH_OUTLIER" if z > 0 else "LOW_OUTLIER",
                    "severity": "CRITICAL" if abs(z) >= 2.5 else "MODERATE"
                })

        # 95% Confidence Interval for the mean
        margin_error = 1.96 * (std_val / math.sqrt(n)) if n > 0 else 0.0
        ci_lower = round(mean_val - margin_error, 2)
        ci_upper = round(mean_val + margin_error, 2)

        # Formal Hypothesis Testing Formulation
        top_entity = labels[0]
        top_val = series[0]
        second_entity = labels[1]
        second_val = series[1]

        # Test if top entity is statistically distinct from the group mean
        z_test_stat = (top_val - mean_val) / (std_val / math.sqrt(n)) if std_val > 0 else 0.0
        p_val_top = 2.0 * (1.0 - cls.norm_cdf(abs(z_test_stat)))
        p_val_top = max(0.0001, min(1.0, p_val_top))

        h0 = f"Null Hypothesis (H0): There is no statistically significant variation in {metric_col} across {dim_col} segments."
        h1 = f"Alternative Hypothesis (H1): '{top_entity}' exhibits a statistically significant deviation in {metric_col} compared to benchmark average."
        
        is_stat_sig = p_val_top < 0.05

        return {
            "has_stats": True,
            "metric_col": metric_col,
            "dim_col": dim_col,
            "sample_size": n,
            "mean": round(mean_val, 2),
            "median": round(median_val, 2),
            "std_dev": round(std_val, 2),
            "confidence_interval_95": (ci_lower, ci_upper),
            "anomalies": anomalies,
            "hypothesis_test": {
                "h0": h0,
                "h1": h1,
                "test_name": "One-Sample Z-Test against Population Mean",
                "test_statistic": round(z_test_stat, 3),
                "p_value": round(p_val_top, 4),
                "significant": is_stat_sig,
                "conclusion": f"Reject H0 in favor of H1 (p = {round(p_val_top, 4)} < 0.05). '{top_entity}' is a statistically significant driver." if is_stat_sig else f"Fail to reject H0 (p = {round(p_val_top, 4)} >= 0.05). Differences are within expected variance."
            }
        }

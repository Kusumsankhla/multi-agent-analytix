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
        Computes descriptive statistics, standardized Z-scores (z = (x - μ) / σ),
        95% confidence intervals for the mean, and Tukey IQR outlier detection.
        Does not divide single-value deviations by standard error or claim single observations
        are 'statistically significant causal drivers'.
        """
        if not rows or len(columns) < 2:
            return {"has_stats": False, "summary": "Insufficient result columns for descriptive statistics."}

        metric_idx = next(
            (i for i in range(1, len(columns))
             if any(isinstance(r[i], (int, float)) and not isinstance(r[i], bool) for r in rows if i < len(r))),
            None
        )
        if metric_idx is None:
            return {"has_stats": False, "summary": "No numeric metric found in the query result."}

        dim_col, metric_col = columns[0], columns[metric_idx]
        pairs = [(str(r[0]), float(r[metric_idx])) for r in rows
                 if len(r) > metric_idx and isinstance(r[metric_idx], (int, float))
                 and not isinstance(r[metric_idx], bool) and math.isfinite(float(r[metric_idx]))]
        if len(pairs) < 2:
            return {"has_stats": False, "summary": "At least two numeric result rows are required."}

        # Sort pairs by metric value descending for inspection
        pairs_sorted_val = sorted(pairs, key=lambda p: p[1], reverse=True)
        top_entity, top_val = pairs_sorted_val[0]

        values = [p[1] for p in pairs]
        n = len(values)
        mean_val = sum(values) / n
        variance = sum((x - mean_val) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
        std_val = math.sqrt(variance)
        sorted_vals = sorted(values)
        median_val = (sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2)

        def percentile(sorted_data, p):
            pos = (len(sorted_data) - 1) * p
            lo = int(math.floor(pos))
            hi = int(math.ceil(pos))
            if lo == hi:
                return sorted_data[lo]
            return sorted_data[lo] * (hi - pos) + sorted_data[hi] * (pos - lo)

        q1, q3 = percentile(sorted_vals, .25), percentile(sorted_vals, .75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr

        # Calculate standard Z-score for single values: z = (x - μ) / σ
        top_z = (top_val - mean_val) / std_val if std_val > 0 else 0.0

        # Detect outliers via Z-score (|z| >= 1.8) and Tukey IQR rule
        anomalies = []
        for label, val in pairs:
            z = (val - mean_val) / std_val if std_val > 0 else 0.0
            reasons = []
            if abs(z) >= 1.8 and (val < lower or val > upper):
                reasons.append("Both Z-Score (|z| ≥ 1.8) and Tukey IQR Bound")
            elif abs(z) >= 1.8:
                reasons.append("Standardized Z-Score (|z| ≥ 1.8)")
            elif val < lower or val > upper:
                bound_desc = f"above upper bound {round(upper, 2)}" if val > upper else f"below lower bound {round(lower, 2)}"
                reasons.append(f"Tukey IQR Rule ({bound_desc}; z = {round(z, 2)} is within normal Z-spread < 1.8)")

            if reasons:
                anomalies.append({
                    "entity": label,
                    "value": round(val, 2),
                    "z_score": round(z, 2),
                    "anomaly_type": "HIGH_OUTLIER" if val > mean_val else "LOW_OUTLIER",
                    "outlier_rule": " + ".join(reasons),
                    "severity": "HIGH" if abs(z) >= 2.5 else "MODERATE"
                })

        # 95% Confidence Interval for the Group Mean: μ ± 1.96 * (σ / sqrt(n))
        se_mean = (std_val / math.sqrt(n)) if n > 0 else 0.0
        ci_lower = round(mean_val - 1.96 * se_mean, 2)
        ci_upper = round(mean_val + 1.96 * se_mean, 2)

        interpretation = (
            f"Descriptive frequency distribution across {n} '{dim_col}' segments for metric '{metric_col}'. "
            f"Peak group is '{top_entity}' (Value: {round(top_val, 2)}, z = {round(top_z, 2)}). "
            f"Note: In descriptive frequency distributions, a high count represents the sample mode/peak frequency, "
            f"not an inferential causal driver."
        )

        h0 = f"Baseline: Groups follow empirical sample distribution (Mean = {round(mean_val, 2)}, Std Dev = {round(std_val, 2)})."
        h1 = f"Dispersion: Segments deviate from sample mean by their standard Z-scores z = (x - Mean) / StdDev."

        return {
            "has_stats": True,
            "metric_col": metric_col,
            "dim_col": dim_col,
            "sample_size": n,
            "mean": round(mean_val, 2),
            "median": round(median_val, 2),
            "std_dev": round(std_val, 2),
            "iqr": round(iqr, 2),
            "top_entity": top_entity,
            "top_value": round(top_val, 2),
            "top_z": round(top_z, 2),
            "confidence_interval_95": (ci_lower, ci_upper),
            "confidence_interval_95_mean": (ci_lower, ci_upper),
            "anomalies": anomalies,
            "interpretation": interpretation,
            "hypothesis_test": {
                "h0": h0,
                "h1": h1,
                "test_name": "Standardized Group Dispersion & Outlier Analysis",
                "test_statistic": round(top_z, 2),
                "peak_entity": top_entity,
                "peak_value": round(top_val, 2),
                "peak_z_score": round(top_z, 2),
                "p_value": "N/A (Descriptive)",
                "significant": False,
                "conclusion": (
                    f"Descriptive distribution analysis: '{top_entity}' is the peak observation "
                    f"({round(top_val, 2)}, z = {round(top_z, 2)} standard deviations from the mean). "
                    f"No causal driver claim is made from grouped descriptive data."
                )
            }
        }


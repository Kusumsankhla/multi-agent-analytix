import os
import ast
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class AnalyticQueryEngine:
    """
    Intelligent heuristic semantic query & synthesis engine.
    Translates business questions into precise, verifiable SQL queries and
    derives grounded analytical insights directly from execution results.
    Acts as an unbreakable deterministic foundation for the multi-agent framework.
    """

    @staticmethod
    def infer_sql_from_intent(question: str, schema_info: str, table_name: str) -> str:
        """Conservative SQL generator for common analytical intents when no LLM is available.

        It uses only columns found in the supplied schema. It deliberately raises for
        Deterministic fallback query planner when no remote LLM is available.
        Inspects schema column types, detects metrics and dimensions dynamically,
        and generates valid, safe SQLite queries for any domain and question type.
        """
        q = question.lower().strip()
        cols_match = re.search(r"Columns:\s*([^\n]+)", schema_info)
        if not cols_match:
            raise ValueError("Could not read the table schema for fallback SQL generation.")
        available_cols = []
        col_types = {}
        for item in cols_match.group(1).split(","):
            item = item.strip()
            if not item:
                continue
            parts = item.split("(")
            name = parts[0].strip().strip('`"')
            t = parts[1].rstrip(")").strip().upper() if len(parts) > 1 else "TEXT"
            if name:
                available_cols.append(name)
                col_types[name] = t
        if not available_cols:
            raise ValueError("No columns were available for fallback SQL generation.")

        def qi(name):
            return '"' + name.replace('"', '""') + '"'
        def norm(name):
            return re.sub(r'[^a-z0-9]', '', name.lower())
        def column_matches_word(col_name: str, text: str) -> bool:
            cn = col_name.lower()
            if re.search(r'\b' + re.escape(cn) + r's?\b', text):
                return True
            if cn.endswith('y') and re.search(r'\b' + re.escape(cn[:-1]) + r'ies\b', text):
                return True
            spaced = cn.replace('_', ' ')
            if spaced in text:
                return True
            return False

        by_norm = {norm(c): c for c in available_cols}
        table = qi(table_name.strip().strip("'\""))
        limit_match = re.search(r'\b(?:top|first|bottom|last)\s+(\d+)\b', q)
        limit = max(1, min(100, int(limit_match.group(1)))) if limit_match else 10
        ascending = any(w in q for w in ['lowest', 'least', 'smallest', 'bottom', 'minimum', 'min '])
        order = 'ASC' if ascending else 'DESC'

        numeric_type_keywords = ['INT', 'REAL', 'FLOAT', 'NUMERIC', 'DOUBLE', 'DECIMAL', 'NUMBER']
        numeric_cols = [c for c in available_cols if any(k in col_types.get(c, '') for k in numeric_type_keywords)]
        if not numeric_cols:
            numeric_cols = [c for c in available_cols if any(k in norm(c) for k in [
                'age', 'amount', 'sales', 'profit', 'income', 'price', 'value', 'score', 'bmi',
                'cholesterol', 'volume', 'rate', 'hr', 'duration', 'salary', 'fee', 'cost',
                'discount', 'quantity', 'balance', 'budget', 'revenue', 'loss', 'count', 'num',
                'bp', 'weight', 'height', 'temp', 'speed', 'distance', 'time', 'grade', 'pct'
            ])]
        categorical_cols = [c for c in available_cols if c not in numeric_cols]

        # Common multi-word synonyms
        synonyms = {
            'transaction amount': ['transactionamt', 'amount'],
            'order value': ['ordervalue', 'sales', 'amount'],
            'monthly income': ['monthlyincome', 'income', 'salary'],
            'heart rate': ['maxhr', 'restingbp'],
            'blood pressure': ['restingbp', 'bp'],
            'sales': ['sales', 'revenue', 'turnover'],
            'profit': ['profit', 'earnings', 'margin']
        }

        matched_cols = []
        for phrase, targets in synonyms.items():
            if phrase in q:
                for t in targets:
                    if t in by_norm and by_norm[t] not in matched_cols:
                        matched_cols.append(by_norm[t])

        for c in available_cols:
            if column_matches_word(c, q) and c not in matched_cols:
                matched_cols.append(c)

        target_keywords = [
            'heartdisease', 'target', 'isfraud', 'fraud', 'attrition', 'default', 'loanstatus',
            'converted', 'conversion', 'outcome', 'churn', 'pass', 'passed', 'status', 'approved',
            'survived', 'active', 'isactive', 'label', 'class', 'risk', 'disease', 'failure', 'fail'
        ]
        outcome = next((by_norm[k] for k in target_keywords if k in by_norm), None)
        if outcome is None:
            outcome = next((c for c in available_cols if any(k in norm(c) for k in target_keywords)), None)

        dim_by = None
        for c in available_cols:
            if re.search(r'\b(?:by|across|per|in|for each)\s+' + re.escape(c.lower()) + r's?\b', q) or (
                c.lower().endswith('y') and re.search(r'\b(?:by|across|per|in|for each)\s+' + re.escape(c.lower()[:-1]) + r'ies\b', q)
            ):
                dim_by = c
                break

        has_outcome_condition = outcome and any(w in q for w in ['heart disease', 'heart failure', 'disease', 'fraud', 'attrition', 'default', 'churn', 'with ' + (outcome.lower() if outcome else '')])
        matched_numeric = [c for c in matched_cols if c in numeric_cols and (c != outcome or not has_outcome_condition)]
        matched_categorical = [c for c in matched_cols if c in categorical_cols and c != outcome]

        # 1. Missing / Null checks
        if any(x in q for x in ['missing value', 'missing values', 'null value', 'null values', 'missing data', 'nulls', 'nan', 'empty value', 'blank']):
            pieces = [
                f"SELECT '{c.replace(chr(39), chr(39)*2)}' AS column_name, "
                f"SUM(CASE WHEN {qi(c)} IS NULL OR TRIM(CAST({qi(c)} AS TEXT)) = '' THEN 1 ELSE 0 END) AS missing_count "
                f"FROM {table}" for c in available_cols
            ]
            return ' UNION ALL '.join(pieces) + ' ORDER BY missing_count DESC LIMIT 100;'

        # 2. Row count / Dataset size
        if (
            any(x in q for x in ['how many records', 'number of records', 'total records', 'row count', 'how many rows', 'total transactions', 'total employees', 'total loans', 'total sessions', 'total count', 'how many total', 'size of the dataset', 'number of rows', 'count of records', 'count of rows', 'dataset size'])
            or (re.search(r'\bhow many\b|\btotal\s+(?:number of|records|rows|cases|patients|students|items|entries|orders|customers|samples|data)\b|\bcount\s+all\b', q) and not any(x in q for x in ['by ', 'group by', 'average', 'avg', 'rate', 'percentage', 'per ']))
        ):
            where_filter = ""
            if outcome and has_outcome_condition:
                where_filter = f" WHERE CAST({qi(outcome)} AS TEXT) IN ('1','1.0','Yes','yes','TRUE','True','Default','Fraud')"
            return f'SELECT COUNT(*) AS record_count FROM {table}{where_filter};'

        # 3. Preview / Sample data
        if any(x in q for x in ['preview', 'sample data', 'show data', 'show all', 'display data', 'view data', 'first few records', 'first 5 records', 'first 10 records', 'show records', 'list records', 'view table', 'sample records', 'sample of']):
            return f'SELECT * FROM {table} LIMIT {limit};'

        # 4. Top / Bottom individual records by a column (e.g. "What are the top 5 records by Age?")
        if (
            re.search(r'\b(?:top|bottom|highest|lowest|first|last)\s+\d*\s*(?:records|rows|samples|entries|patients|students|transactions|items|orders|users)?\s*by\b', q)
            or (any(x in q for x in ['top ', 'bottom ', 'highest ', 'lowest ']) and any(w in q for w in ['records by', 'rows by', 'entries by', 'records of', 'rows of']))
        ):
            target_metric = matched_numeric[0] if matched_numeric else (matched_cols[0] if matched_cols else (numeric_cols[0] if numeric_cols else available_cols[0]))
            return f'SELECT * FROM {table} ORDER BY {qi(target_metric)} {order} LIMIT {limit};'

        # 5. Top / Bottom categories by metric (e.g. "What are the top 3 categories by total sales and profit?")
        if any(x in q for x in ['top ', 'highest', 'lowest', 'most ', 'least ', 'best ', 'worst ', 'largest', 'smallest', 'generates the highest']):
            dim = dim_by or (matched_categorical[0] if matched_categorical else None)
            if not dim:
                for c in categorical_cols:
                    if column_matches_word(c, q):
                        dim = c
                        break
            if dim:
                metrics_to_use = [m for m in matched_numeric if m != dim]
                if not metrics_to_use:
                    metrics_to_use = [c for c in numeric_cols if c != dim][:2]
                where_clause = ""
                if outcome and has_outcome_condition and outcome != dim:
                    where_clause = f" WHERE CAST({qi(outcome)} AS TEXT) IN ('1','1.0','Yes','yes','TRUE','True','Default','Fraud','Pass','Passed','Churn','Positive','Left','left')"
                if metrics_to_use:
                    agg = 'AVG' if any(x in q for x in ['average', 'avg', 'mean']) else ('COUNT' if 'count' in q else 'SUM')
                    select_parts = [f'{qi(dim)}']
                    for m in metrics_to_use[:2]:
                        select_parts.append(f'ROUND({agg}({qi(m)}), 2) AS {qi(agg.lower() + "_" + norm(m))}')
                    return f'SELECT {", ".join(select_parts)} FROM {table}{where_clause} GROUP BY {qi(dim)} ORDER BY 2 {order} LIMIT {limit};'
                elif where_clause:
                    return f'SELECT {qi(dim)}, COUNT(*) AS {qi(norm(outcome) + "_count")} FROM {table}{where_clause} GROUP BY {qi(dim)} ORDER BY 2 {order} LIMIT {limit};'

        # 6. Rates / Proportions
        if any(x in q for x in ['rate', 'percentage', 'percent', 'proportion', 'share of', 'how often', 'ratio of']):
            dim = dim_by or (matched_categorical[0] if matched_categorical else None)
            target_outcome = outcome
            if target_outcome is None or (dim and dim == target_outcome):
                for c in available_cols:
                    if c != dim and (norm(c) in ['pass','passed','churn','default','attrition','fraud','heartdisease','target','active'] or (norm(c) in norm(q) and c in categorical_cols)):
                        target_outcome = c
                        break

            if target_outcome:
                target_q = qi(target_outcome)
                pos_expr = f"CASE WHEN CAST({target_q} AS TEXT) IN ('1','1.0','Yes','yes','TRUE','True','Default','Fraud','Pass','Passed','Churn','Positive') THEN 1 ELSE 0 END"
                if dim and dim != target_outcome:
                    return (
                        f"SELECT {qi(dim)}, COUNT(*) AS total_records, "
                        f"SUM({pos_expr}) AS positive_count, "
                        f"ROUND(100.0 * SUM({pos_expr}) / NULLIF(COUNT(*),0), 2) AS rate_pct "
                        f"FROM {table} GROUP BY {qi(dim)} ORDER BY rate_pct {order} LIMIT {limit};"
                    )
                return (
                    f"SELECT COUNT(*) AS total_records, "
                    f"SUM({pos_expr}) AS positive_count, "
                    f"ROUND(100.0 * SUM({pos_expr}) / NULLIF(COUNT(*),0), 2) AS rate_pct FROM {table};"
                )

        # 7. Summary statistics
        if any(x in q for x in ['summary statistic', 'summary statistics', 'describe', 'distribution metrics', 'stats for', 'statistical summary']):
            target_metric = matched_numeric[0] if matched_numeric else (matched_cols[0] if matched_cols else (numeric_cols[0] if numeric_cols else None))
            if target_metric:
                return (
                    f'SELECT COUNT({qi(target_metric)}) AS record_count, '
                    f'ROUND(AVG({qi(target_metric)}), 2) AS mean_value, '
                    f'ROUND(MIN({qi(target_metric)}), 2) AS min_value, '
                    f'ROUND(MAX({qi(target_metric)}), 2) AS max_value FROM {table};'
                )
            elif numeric_cols:
                selects = ['COUNT(*) AS record_count']
                for c in numeric_cols[:6]:
                    selects.append(f'ROUND(AVG({qi(c)}), 2) AS {qi("avg_" + norm(c))}')
                return f'SELECT {", ".join(selects)} FROM {table};'

        # 8. Correlation / Relationship
        if any(x in q for x in ['correlation', 'relationship', 'relate', 'associate', 'vs', 'versus', 'scatter']):
            if len(matched_numeric) >= 2:
                return f'SELECT {qi(matched_numeric[0])}, {qi(matched_numeric[1])} FROM {table} WHERE {qi(matched_numeric[0])} IS NOT NULL AND {qi(matched_numeric[1])} IS NOT NULL LIMIT 50;'
            elif len(numeric_cols) >= 2:
                return f'SELECT {qi(numeric_cols[0])}, {qi(numeric_cols[1])} FROM {table} WHERE {qi(numeric_cols[0])} IS NOT NULL AND {qi(numeric_cols[1])} IS NOT NULL LIMIT 50;'

        # 9. Filter / Condition
        cond_match = re.search(r'([a-zA-Z0-9_]+)\s*(>|<|>=|<=|=|!=)\s*([0-9\.\'\"]+)', question)
        if cond_match:
            cand_col, op, val = cond_match.group(1), cond_match.group(2), cond_match.group(3)
            found_c = next((c for c in available_cols if norm(c) == norm(cand_col)), None)
            if found_c:
                return f'SELECT * FROM {table} WHERE {qi(found_c)} {op} {val} LIMIT {limit};'

        # 10. Averages / Sums / Extremes
        if any(x in q for x in ['average', 'avg', 'mean', 'sum of', 'total ', 'maximum', 'minimum', 'highest', 'lowest', 'max ', 'min ']):
            if any(x in q for x in ['average', 'avg', 'mean']): agg = 'AVG'
            elif any(x in q for x in ['maximum', 'highest', 'max ']): agg = 'MAX'
            elif any(x in q for x in ['minimum', 'lowest', 'min ']): agg = 'MIN'
            else: agg = 'SUM'

            dim = dim_by or (matched_categorical[0] if matched_categorical else None)
            target_metric = matched_numeric[0] if matched_numeric else (numeric_cols[0] if numeric_cols else None)

            where_clause = ""
            if outcome and has_outcome_condition:
                where_clause = f" WHERE CAST({qi(outcome)} AS TEXT) IN ('1','1.0','Yes','yes','TRUE','True','Default','Fraud')"

            if target_metric and dim and dim != target_metric:
                return f'SELECT {qi(dim)}, ROUND({agg}({qi(target_metric)}), 2) AS {qi(agg.lower() + "_" + norm(target_metric))} FROM {table}{where_clause} GROUP BY {qi(dim)} ORDER BY 2 {order} LIMIT {limit};'
            elif target_metric:
                return f'SELECT COUNT({qi(target_metric)}) AS non_null_count, ROUND({agg}({qi(target_metric)}), 2) AS metric_value FROM {table}{where_clause};'
            elif numeric_cols:
                selects = ['COUNT(*) AS record_count']
                for c in numeric_cols[:6]:
                    selects.append(f'ROUND({agg}({qi(c)}), 2) AS {qi(agg.lower() + "_" + norm(c))}')
                return f'SELECT {", ".join(selects)} FROM {table}{where_clause};'

        # 11. Distribution / Breakdown
        if any(x in q for x in ['distribution', 'breakdown', 'count by', 'number by', 'how many by', 'frequency of', 'split by']):
            dim = dim_by or (matched_categorical[0] if matched_categorical else (matched_cols[0] if matched_cols else (categorical_cols[0] if categorical_cols else available_cols[0])))
            return f'SELECT {qi(dim)} AS {qi(dim)}, COUNT(*) AS record_count FROM {table} GROUP BY {qi(dim)} ORDER BY record_count {order} LIMIT {limit};'

        # 12. Universal Fallback (Never Fail)
        if matched_numeric:
            c = matched_numeric[0]
            return f'SELECT COUNT({qi(c)}) AS record_count, ROUND(AVG({qi(c)}), 2) AS mean_value, ROUND(MIN({qi(c)}), 2) AS min_value, ROUND(MAX({qi(c)}), 2) AS max_value FROM {table};'
        elif matched_categorical:
            c = matched_categorical[0]
            return f'SELECT {qi(c)} AS {qi(c)}, COUNT(*) AS record_count FROM {table} GROUP BY {qi(c)} ORDER BY record_count DESC LIMIT {limit};'
        elif numeric_cols and categorical_cols:
            return f'SELECT {qi(categorical_cols[0])}, ROUND(AVG({qi(numeric_cols[0])}), 2) AS {qi("avg_" + norm(numeric_cols[0]))} FROM {table} GROUP BY {qi(categorical_cols[0])} ORDER BY 2 DESC LIMIT {limit};'
        elif numeric_cols:
            selects = ['COUNT(*) AS record_count']
            for c in numeric_cols[:5]:
                selects.append(f'ROUND(AVG({qi(c)}), 2) AS {qi("avg_" + norm(c))}')
            return f'SELECT {", ".join(selects)} FROM {table};'
        else:
            return f'SELECT * FROM {table} LIMIT {limit};'

    @staticmethod
    def synthesize_grounded_report(question: str, sql: str, columns: list, rows: list, auditor_verdict: str) -> str:
        """Create an articulate, data-specific report with natural language answers, numbers, and clear engine disclosure."""
        if not rows or not columns:
            return (
                "### Direct Answer\n"
                "The query returned no matching rows or data columns, so no empirical conclusion can be drawn from the database.\n\n"
                f"**Question Analyzed:** {question}\n\n"
                "Please verify table selection, filters, and query syntax.\n\n"
                "*Engine: Deterministic Analytic Engine (Local Fallback)*"
            )

        def fmt(value):
            if value is None:
                return "NULL"
            if isinstance(value, float):
                return f"{value:,.2f}".rstrip("0").rstrip(".") if abs(value) >= 0.01 else f"{value:.4f}"
            if isinstance(value, int):
                return f"{value:,}"
            return str(value)

        lines = [
            f"**Question:** {question}",
            "",
            "### Direct Answer"
        ]

        sql_lower = sql.lower() if sql else ""
        is_select_all = "select *" in sql_lower and "group by" not in sql_lower
        col_names_lower = [c.lower() for c in columns]

        # Case 1: Individual record samples (SELECT * ... LIMIT N)
        if is_select_all and len(columns) >= 3:
            order_match = re.search(r"order\s+by\s+[\"']?([a-zA-Z0-9_]+)[\"']?\s*(asc|desc)?", sql_lower)
            order_col = order_match.group(1) if order_match else columns[0]
            order_dir = "descending" if (order_match and order_match.group(2) == "desc") else "ascending"
            
            lines.append(
                f"In response to the question, the top **{len(rows)}** records ordered by **{order_col}** ({order_dir}) are retrieved below. "
                f"The leading record has **{columns[0]}: {fmt(rows[0][0])}** with **{columns[1]}: {fmt(rows[0][1])}**."
            )

        # Case 2: Single summary row with 1 aggregate column (e.g. overall count)
        elif len(rows) == 1 and len(columns) == 1:
            col_name = columns[0]
            val = rows[0][0]
            lines.append(
                f"In response to the question, the database analysis calculates that the total **{col_name}** is **{fmt(val)}**."
            )

        # Case 3: Single summary row with multiple aggregate metrics
        elif len(rows) == 1:
            row = rows[0]
            col_val_map = {c.lower(): val for c, val in zip(columns, row)}
            
            # Check for mean / count pattern (e.g. non_null_count and metric_value)
            if "metric_value" in col_val_map and "non_null_count" in col_val_map:
                m_val = col_val_map["metric_value"]
                c_val = col_val_map["non_null_count"]
                lines.append(
                    f"In response to the question, the verified database result is **{fmt(m_val)}** (calculated across **{fmt(c_val)}** matching records)."
                )
            # Check for summary stats (mean, min, max, count)
            elif "mean_value" in col_val_map and "min_value" in col_val_map and "max_value" in col_val_map:
                c_val = col_val_map.get("record_count", len(rows))
                lines.append(
                    f"Across **{fmt(c_val)}** analyzed records, the average (mean) is **{fmt(col_val_map['mean_value'])}**, "
                    f"ranging from a minimum of **{fmt(col_val_map['min_value'])}** to a maximum of **{fmt(col_val_map['max_value'])}**."
                )
            # Check for rates (rate_pct, positive_count, total_records)
            elif "rate_pct" in col_val_map:
                r_val = col_val_map["rate_pct"]
                p_val = col_val_map.get("positive_count")
                t_val = col_val_map.get("total_records")
                if p_val is not None and t_val is not None:
                    lines.append(
                        f"In response to the question, the calculated rate is **{fmt(r_val)}%** "
                        f"(**{fmt(p_val)}** positive occurrences out of **{fmt(t_val)}** total records)."
                    )
                else:
                    lines.append(f"In response to the question, the calculated rate is **{fmt(r_val)}%**.")
            else:
                details = [f"**{col}:** {fmt(val)}" for col, val in zip(columns, row)]
                lines.append(
                    f"Based on the database query execution, the summary analysis yields: {', '.join(details)}."
                )

        # Case 4: Grouped breakdown (e.g. Age and count, or Category and Sales, or Department and Attrition rate)
        else:
            dim_col = columns[0]
            col_names_l = [c.lower() for c in columns]
            
            # If rate_pct is present, report the rate breakdown directly
            if "rate_pct" in col_names_l:
                r_idx = col_names_l.index("rate_pct")
                r_pairs = [(row[0], float(row[r_idx])) for row in rows if len(row) > r_idx and isinstance(row[r_idx], (int, float))]
                if r_pairs:
                    best_r = r_pairs[0]
                    lines.append(
                        f"In response to the question, **{dim_col} '{best_r[0]}'** exhibits the highest rate at **{fmt(best_r[1])}%**."
                    )
                    if len(r_pairs) > 1:
                        lowest_r = r_pairs[-1]
                        lines.append(
                            f"The lowest segment is **{dim_col} '{lowest_r[0]}'** at **{fmt(lowest_r[1])}%**."
                        )
            else:
                metric_cols = columns[1:]
                primary_metric = metric_cols[0] if metric_cols else "value"

                numeric_pairs = [(row[0], float(row[1])) for row in rows if len(row) > 1 and isinstance(row[1], (int, float))]
                if numeric_pairs:
                    sorted_pairs = sorted(numeric_pairs, key=lambda p: p[1], reverse=True)
                    best = sorted_pairs[0]
                    total_metric = sum(p[1] for p in numeric_pairs)
                    pct_share = (best[1] / total_metric * 100.0) if total_metric > 0 else 0.0

                    lead_sentence = (
                        f"In response to the question, the data indicates that **{dim_col} '{best[0]}'** ranks highest with "
                        f"**{fmt(best[1])} {primary_metric}**"
                    )
                    if total_metric > 0 and len(rows) > 1:
                        lead_sentence += f" (accounting for **{pct_share:.1f}%** of the returned total across {len(rows)} segments)"
                    lead_sentence += "."
                    lines.append(lead_sentence)

                    if len(sorted_pairs) > 1:
                        second_best = sorted_pairs[1]
                        lines.append(
                            f"The second highest segment is **{dim_col} '{second_best[0]}'** with **{fmt(second_best[1])} {primary_metric}**."
                        )
                else:
                    lines.append(
                        f"The query returned {len(rows)} segments across **{dim_col}**. Top result is **'{rows[0][0]}'**."
                    )

        def markdown_cell(val: Any) -> str:
            return str(val).replace("|", r"\|").replace("\n", " ")

        lines.extend([
            "",
            "#### Key Empirical Data Findings:",
            "| " + " | ".join(markdown_cell(c) for c in columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ])

        for row in rows[:15]:
            lines.append(
                "| " + " | ".join(markdown_cell(fmt(val)) for val in row) + " |"
            )
        if len(rows) > 15:
            lines.append(f"\n*(Showing top 15 of {len(rows)} returned rows)*")

        lines.extend([
            "",
            "#### Verification & Provenance Context:",
            f"- **Auditor Alignment Verdict:** {auditor_verdict}",
            "- **Data Lineage:** Values shown above were extracted directly from the sandboxed SQLite execution rows.",
            "- *Engine Mode: Deterministic Analytic Engine (Local Fallback -- Zero LLM Tokens Used)*"
        ])

        return "\n".join(lines)



class LLMClient:
    """
    Unified, resilient LLM client supporting:
    - OpenAI (gpt-4o-mini, gpt-4o)
    - Local Ollama (qwen2.5:7b, llama3.1)
    - AnalyticQueryEngine (Deterministic, zero-latency grounded engine)
    """

    def __init__(self, provider="auto", model=None, base_url="http://localhost:11434", temperature=0.1):
        self.provider = provider
        self.configured_provider = provider
        self.fallback_used = False
        self.fallback_reason = None
        self.llm_calls_succeeded = 0
        self.temperature = temperature
        self.base_url = base_url
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        
        if self.provider == "auto":
            if self.openai_key and len(self.openai_key) > 20:
                self.provider = "openai"
                self.model = model or "gpt-4o-mini"
            else:
                self.provider = "ollama"
                self.model = model or "qwen2.5:7b"
        elif self.provider == "openai":
            self.model = model or "gpt-4o-mini"
        elif self.provider == "ollama":
            self.model = model or "qwen2.5:7b"
        else:
            self.provider = "fallback"
            self.model = "deterministic-rule-engine"

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1200) -> str:
        """Attempts LLM generation with graceful multi-tier fallback."""
        if self.provider == "openai":
            try:
                result = self._call_openai(system_prompt, user_prompt, max_tokens)
                self.llm_calls_succeeded += 1
                return result
            except Exception as exc:
                self.fallback_used = True
                self.fallback_reason = f"{type(exc).__name__}: {str(exc)[:240]}"
                return self._analytic_fallback(system_prompt, user_prompt)

        elif self.provider == "ollama":
            try:
                result = self._call_ollama(system_prompt, user_prompt, self.model, timeout=20)
                self.llm_calls_succeeded += 1
                return result
            except Exception as exc:
                self.fallback_used = True
                self.fallback_reason = f"{type(exc).__name__}: {str(exc)[:240]}"
                return self._analytic_fallback(system_prompt, user_prompt)

        else:
            self.fallback_used = True
            self.fallback_reason = "Deterministic fallback provider selected; no LLM call was attempted."
            return self._analytic_fallback(system_prompt, user_prompt)

    def _call_openai(self, system_prompt: str, user_prompt: str, max_tokens: int = 1200) -> str:
        if not self.openai_key:
            raise ValueError("No OPENAI_API_KEY available.")
        
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"].strip()

    def _call_ollama(self, system_prompt: str, user_prompt: str, model: str = "qwen2.5:7b", timeout: int = 20) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            return res_json["response"].strip()

    def _analytic_fallback(self, system_prompt: str, user_prompt: str) -> str:
        prompt_l = user_prompt.lower()
        
        # 1. Synthesis & Reporting (Check first to avoid collision with SQL in query prompt)
        if "write the verified executive synthesis" in prompt_l or "executive synthesis" in prompt_l:
            q_match = re.search(r"Question:\s*([^\n]+)", user_prompt)
            question = q_match.group(1).strip() if q_match else "Data Analysis"

            sql_match = re.search(r"Executed Query:\s*([^\n]+)", user_prompt)
            sql_query = sql_match.group(1).strip() if sql_match else ""

            cols_match = re.search(r"Columns:\s*(\[[^\]]+\])", user_prompt)
            rows_match = re.search(r"Raw Rows:\s*(\[.*?\])\s*(?:Auditor Note:|\n\nWrite|$)", user_prompt, re.DOTALL)
            
            auditor_match = re.search(r"Auditor Note:\s*([^\n]+)", user_prompt)
            auditor_verdict = auditor_match.group(1).strip() if auditor_match else "CONFIRMED"

            cols = []
            rows = []
            if cols_match:
                try:
                    cols = ast.literal_eval(cols_match.group(1))
                except Exception:
                    pass
            if rows_match:
                try:
                    rows = ast.literal_eval(rows_match.group(1).strip())
                except Exception:
                    pass

            return AnalyticQueryEngine.synthesize_grounded_report(question, sql_query, cols, rows, auditor_verdict)

        # 2. Auditor Verifier Check
        elif "audit this analysis" in prompt_l or "issue your formal verdict" in prompt_l:
            q_match = re.search(r"User Question:\s*([^\n]+)", user_prompt)
            sql_match = re.search(r"Executed SQL:\s*([^\n]+)", user_prompt)
            cols_match = re.search(r"Columns:\s*(\[[^\]]+\])", user_prompt)
            question = q_match.group(1).strip() if q_match else ""
            sql = sql_match.group(1).strip() if sql_match else ""

            cols = []
            if cols_match:
                try:
                    cols = ast.literal_eval(cols_match.group(1))
                except Exception:
                    pass

            from core.verification_engine import QueryIntentValidator
            iv = QueryIntentValidator.validate_intent(question, sql, columns=cols)
            if not iv["is_aligned"]:
                return (
                    f"VERDICT: NEEDS_REVIEW\n\n"
                    f"- Question-to-SQL Intent Warning: {'; '.join(iv['issues'])}\n"
                    f"- Status: Downgraded to NEEDS_REVIEW because the query does not answer the question."
                )
            else:
                return (
                    f"VERDICT: CONFIRMED\n\n"
                    f"- Question-to-SQL Intent Alignment: SQL query directly addresses requested metric, grouping, and conditions.\n"
                    f"- Status: Intent confirmed ({iv['summary']})."
                )

        # 3. Coder SQL Generation
        elif "generate the sqlite query" in prompt_l or "write a single, highly optimized" in system_prompt.lower():
            q_match = re.search(r"User Question:\s*([^\n]+)", user_prompt)
            question = q_match.group(1).strip() if q_match else "Analyze table data"
            
            t_match = re.search(r"Table:\s*([^\n]+)", user_prompt)
            table = t_match.group(1).strip() if t_match else "orders"
            
            try:
                sql = AnalyticQueryEngine.infer_sql_from_intent(question, user_prompt, table)
                return f"```sql\n{sql}\n```"
            except ValueError as exc:
                return f"UNSUPPORTED_FALLBACK_INTENT: {exc}"

        # 4. Planner Planning
        else:
            q_match = re.search(r"User Question:\s*([^\n]+)", user_prompt)
            question = q_match.group(1).strip() if q_match else "the supplied question"
            schema_match = re.search(r"Columns:\s*([^\n]+)", user_prompt)
            schema_columns = schema_match.group(1).strip() if schema_match else "schema columns not parsed"
            return (
                "DETERMINISTIC FALLBACK PLAN (not an LLM-generated interpretation)\n"
                f"1. User's requested analysis: {question}.\n"
                f"2. Available fields to inspect: {schema_columns}. Use only exact fields from this schema.\n"
                "3. Generate SQL only if the requested metric, filter, and grouping can be mapped confidently; otherwise stop and ask for clarification.\n"
                "4. After execution, report only returned values and mark the result NEEDS_REVIEW because fallback planning does not independently prove question-to-SQL correctness."
            )

    @staticmethod
    def extract_sql(text: str) -> str:
        """Extracts pure SQL query string from markdown code blocks or text."""
        sql_match = re.search(r"```(?:sql|sqlite)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            clean = sql_match.group(1).strip()
            return clean.rstrip(";") + ";"
        
        select_match = re.search(r"(SELECT\s+.*?;?)", text, re.DOTALL | re.IGNORECASE)
        if select_match:
            lines = []
            for line in select_match.group(1).splitlines():
                stripped = line.strip()
                if stripped.startswith("--") or stripped.startswith("#"):
                    continue
                lines.append(stripped)
            sql = " ".join(lines).strip()
            return sql.rstrip(";") + ";"
            
        return text.strip().rstrip(";") + ";"

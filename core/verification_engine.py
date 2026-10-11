import re
import math
from typing import List, Dict, Any, Tuple, Set, Optional

class DeterministicFactChecker:
    """
    Deterministic (non-LLM) verification engine that performs ground-truth fact-checking
    by extracting numerical claims from agent-generated prose and cross-verifying them
    against actual database execution results.
    """

    @staticmethod
    def extract_numbers_from_text(text: str) -> List[Dict[str, Any]]:
        """
        Extracts numeric values from natural language text, including:
        - Integers (e.g. 20000, 20,000)
        - Decimals (e.g. 3.48, 0.035)
        - Percentages (e.g. 3.5%, 12.8%)
        - Dollar amounts (e.g. $12,450.50, $45.2M)
        """
        results = []
        # Support suffixes like K, M, B (e.g. $45.2M, 950K)
        pattern = r"(?:[\$€£])?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?[%kKmMbB]?\b"
        
        matches = re.finditer(pattern, text)
        for m in matches:
            token = m.group(0).strip()
            clean_str = token.replace("$", "").replace("€", "").replace("£", "").replace(",", "")
            
            is_percentage = clean_str.endswith("%")
            multiplier = 1.0
            
            if is_percentage:
                clean_str = clean_str.rstrip("%")
            elif clean_str.endswith(("k", "K")):
                multiplier = 1_000.0
                clean_str = clean_str[:-1]
            elif clean_str.endswith(("m", "M")):
                multiplier = 1_000_000.0
                clean_str = clean_str[:-1]
            elif clean_str.endswith(("b", "B")):
                multiplier = 1_000_000_000.0
                clean_str = clean_str[:-1]
                
            try:
                base_val = float(clean_str)
                val = base_val * multiplier
                
                # Ignore list item numbering prefixes like "1. ", "2. ", "3) " at the start of a line
                line_start = text.rfind("\n", 0, m.start()) + 1
                preceding_on_line = text[line_start:m.start()].strip()
                after_text = text[m.end():m.end() + 2]
                if preceding_on_line in ["", "-", "*"] and (after_text.startswith(". ") or after_text.startswith(") ")):
                    continue

                # Ignore small rank prefixes or step indices like "#1", "Step 1"
                start_idx = max(0, m.start() - 6)
                preceding = text[start_idx:m.start()].lower()
                if text[max(0, m.start() - 1):m.start()] == "#":
                    continue
                if ("step" in preceding or "call" in preceding or preceding.endswith("#")) and val in [1.0, 2.0, 3.0, 4.0]:
                    continue
                    
                results.append({
                    "raw_token": token,
                    "value": val,
                    "base_val": base_val,
                    "is_percentage": is_percentage,
                    "span": (m.start(), m.end())
                })
            except ValueError:
                continue
                
        return results

    @staticmethod
    def index_ground_truth_values(execution_result: Dict[str, Any]) -> Dict[str, Set[float]]:
        """
        Categorizes numbers from database query results into:
        - 'numbers': general counts, amounts, metrics
        - 'rates': percentages and proportions
        """
        truth_index = {
            "numbers": set(),
            "rates": set()
        }
        
        if not execution_result or not execution_result.get("success"):
            return truth_index

        columns = [c.lower() for c in execution_result.get("columns", [])]
        rows = execution_result.get("rows", [])
        
        for row in rows:
            for col_idx, cell in enumerate(row):
                col_name = columns[col_idx] if col_idx < len(columns) else ""
                is_rate_col = any(k in col_name for k in ["rate", "pct", "percent", "ratio", "proportion", "margin", "discount"])
                
                if isinstance(cell, (int, float)):
                    fval = float(cell)
                    truth_index["numbers"].add(fval)
                    truth_index["numbers"].add(float(int(fval)))
                    
                    if is_rate_col or 0.0 <= fval <= 1.0:
                        truth_index["rates"].add(round(fval, 4))
                        truth_index["rates"].add(round(fval * 100.0, 2))
                    elif is_rate_col:
                        truth_index["rates"].add(round(fval, 2))
                        truth_index["rates"].add(round(fval / 100.0, 4))

                elif isinstance(cell, str):
                    try:
                        clean_cell = cell.replace(",", "").rstrip("%")
                        fval = float(clean_cell)
                        truth_index["numbers"].add(fval)
                        if is_rate_col or "%" in cell or 0.0 <= fval <= 1.0:
                            truth_index["rates"].add(round(fval, 4))
                            truth_index["rates"].add(round(fval * 100.0, 2))
                    except ValueError:
                        pass
                        
        return truth_index

    @classmethod
    def verify_claims(
        cls, 
        prose_answer: str, 
        execution_result: Dict[str, Any], 
        tolerance_pct: float = 1.5
    ) -> Dict[str, Any]:
        """
        Cross-verifies claims made in the prose against the actual database result.
        Returns:
        - groundedness_score: float (0.0 to 100.0%)
        - status: str ("FULLY_GROUNDED", "PARTIALLY_VERIFIED", "HALLUCINATION_DETECTED", "NO_TOOL_EXECUTION")
        - claims_audit: List[Dict] with token, value, matched, and status
        - verified_count: int
        - ungrounded_count: int
        - total_claims: int
        """
        if not execution_result or not execution_result.get("success"):
            return {
                "groundedness_score": 0.0,
                "status": "NO_TOOL_EXECUTION_OR_ERROR",
                "claims_audit": [],
                "verified_count": 0,
                "ungrounded_count": 0,
                "total_claims": 0,
                "message": "No valid tool execution results found. Claims cannot be grounded."
            }

        extracted_claims = cls.extract_numbers_from_text(prose_answer)
        truth_index = cls.index_ground_truth_values(execution_result)
        
        if not extracted_claims:
            return {
                "groundedness_score": None,
                "status": "NO_CLAIMS_TO_VERIFY",
                "claims_audit": [],
                "verified_count": 0,
                "ungrounded_count": 0,
                "total_claims": 0,
                "message": "No numerical claims were extracted. Groundedness is not evaluated; this is not a 100% verification."
            }

        claims_audit = []
        verified_count = 0
        ungrounded_count = 0

        for claim in extracted_claims:
            is_pct = claim["is_percentage"]
            val = claim["base_val"] if is_pct else claim["value"]
            matched = False
            best_match_val = None

            # Choose candidate pool based on claim type
            target_candidates = truth_index["rates"] if is_pct else truth_index["numbers"]
            
            # If rate pool was empty but it's a rate, also check general numbers
            if not target_candidates and is_pct:
                target_candidates = truth_index["numbers"]

            for truth in target_candidates:
                if math.isclose(val, truth, rel_tol=tolerance_pct / 100.0, abs_tol=0.02):
                    matched = True
                    best_match_val = truth
                    break

            if matched:
                verified_count += 1
                claims_audit.append({
                    "token": claim["raw_token"],
                    "value": val,
                    "matched": True,
                    "ground_truth_match": best_match_val,
                    "status": "VERIFIED_GROUND_TRUTH"
                })
            else:
                ungrounded_count += 1
                claims_audit.append({
                    "token": claim["raw_token"],
                    "value": val,
                    "matched": False,
                    "ground_truth_match": None,
                    "status": "UNGROUNDED_CLAIM"
                })

        total = len(extracted_claims)
        groundedness = round((verified_count / total) * 100.0, 1)

        if groundedness >= 90.0:
            status = "FULLY_GROUNDED"
        elif groundedness >= 60.0:
            status = "PARTIALLY_VERIFIED"
        else:
            status = "HALLUCINATION_DETECTED"

        return {
            "groundedness_score": groundedness,
            "status": status,
            "claims_audit": claims_audit,
            "verified_count": verified_count,
            "ungrounded_count": ungrounded_count,
            "total_claims": total,
            "message": f"{verified_count} of {total} numerical claims verified against ground-truth database rows."
        }


class QueryIntentValidator:
    """
    Deterministic validator to check whether the generated SQL query
    actually answers the user's natural language question, detecting
    aggregation mismatches, missing condition/outcome filters (e.g. the Age example),
    and metric mismatches.
    """

    @staticmethod
    def validate_intent(
        question: str,
        sql: str,
        schema_info: str = "",
        columns: Optional[List[str]] = None,
        rows: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        q = question.lower().strip()
        sql_clean = sql.strip()
        sql_l = sql_clean.lower()

        issues: List[str] = []
        warnings: List[str] = []
        checks_performed: List[str] = []

        # Extract columns present in schema if provided
        available_cols: List[str] = []
        if schema_info:
            cols_match = re.search(r"Columns:\s*([^\n]+)", schema_info)
            if cols_match:
                for item in cols_match.group(1).split(","):
                    name = item.split("(")[0].strip().strip('`"')
                    if name:
                        available_cols.append(name)
        if not available_cols and columns:
            available_cols = list(columns)

        def norm(s: str) -> str:
            return re.sub(r'[^a-z0-9]', '', s.lower())

        by_norm = {norm(c): c for c in available_cols}

        # 1. Target Condition / Outcome Alignment (The Age Example)
        outcome_concepts = [
            ("heart disease", ["heart disease", "heart failure", "cardiac", "disease"], ["heartdisease", "target"]),
            ("fraud", ["fraud", "fraudulent", "scam"], ["isfraud", "fraud"]),
            ("attrition", ["attrition", "left the company", "churn", "turnover", "quit"], ["attrition"]),
            ("loan default", ["default", "defaulted", "delinquent"], ["loanstatus", "default"]),
            ("conversion", ["converted", "conversion"], ["converted", "conversion"])
        ]

        for concept_name, concept_terms, col_candidates in outcome_concepts:
            if any(term in q for term in concept_terms):
                checks_performed.append(f"Outcome Filter Check: {concept_name}")
                target_col = next((by_norm[norm(c)] for c in col_candidates if norm(c) in by_norm), None)
                if not target_col:
                    target_col = next((c for c in available_cols if any(norm(t) in norm(c) or norm(c) in norm(t) for t in concept_terms)), None)
                if target_col:
                    norm_target = norm(target_col)
                    col_in_sql = norm_target in norm(sql_l)
                    has_where_or_case = "where" in sql_l or "case" in sql_l or "having" in sql_l
                    if not col_in_sql or not has_where_or_case:
                        issues.append(
                            f"Missing Outcome Filter: The question specifically inquires about '{concept_name}', "
                            f"but the SQL query does not filter or condition on the outcome column '{target_col}'. "
                            f"The query measures general records without conditioning on {concept_name}."
                        )
                elif "where" not in sql_l and "case" not in sql_l and "having" not in sql_l:
                    warnings.append(
                        f"Potential Missing Filter: The question references '{concept_name}', but the SQL query "
                        f"contains no WHERE or CASE filter clause."
                    )

        # 2. Aggregation Type Alignment (Average vs Count vs Sum vs Rate)
        checks_performed.append("Aggregation Type Alignment")
        asks_avg = bool(re.search(r'\b(average|avg|mean)\b', q))
        asks_sum = bool(re.search(r'\b(total revenue|total sales|total profit|total amount|sum of|total spend)\b', q))
        asks_rate = bool(re.search(r'\b(rate|percentage|percent|proportion|share of|ratio)\b', q))

        has_avg = "avg(" in sql_l
        has_sum = "sum(" in sql_l
        has_count = "count(" in sql_l
        has_rate_calc = ("*" in sql_l and "/" in sql_l) or "rate" in sql_l or "round(100.0" in sql_l

        if asks_avg and not has_avg:
            if has_count:
                issues.append(
                    "Aggregation Mismatch: The question asks for an average/mean, but the SQL query executes COUNT(*) "
                    "instead of calculating AVG(). Grouped counts do not answer an average question."
                )
            else:
                issues.append("Aggregation Mismatch: The question asks for an average/mean, but no AVG() function was found in the SQL query.")

        if asks_sum and not has_sum and has_count:
            issues.append(
                "Aggregation Mismatch: The question asks for total/sum of a financial/numerical metric, "
                "but the SQL query uses COUNT(*) instead of SUM()."
            )

        if asks_rate and not has_rate_calc and not has_avg:
            if has_count and "group by" not in sql_l:
                issues.append(
                    "Aggregation Mismatch: The question requests a rate or percentage, but the SQL query returns a raw count "
                    "without calculating the requested proportion."
                )
            elif "group by" in sql_l and not ("*" in sql_l and "/" in sql_l):
                warnings.append(
                    "Question asks for a rate/percentage, but SQL returns group counts. "
                    "A manual proportion calculation from the rows is required."
                )

        # 3. Specific Numerical Thresholds / Conditions
        threshold_match = re.search(r'\b(over|above|greater than|older than|under|below|less than|younger than)\s+(\d+)\b', q)
        if threshold_match:
            checks_performed.append("Numerical Cutoff Filter Check")
            cutoff_val = threshold_match.group(2)
            if "where" not in sql_l and "having" not in sql_l:
                issues.append(
                    f"Missing Filter Condition: The question specifies a numerical condition ('{threshold_match.group(0)}'), "
                    f"but the SQL query lacks a WHERE or HAVING filter."
                )
            elif cutoff_val not in sql_clean:
                warnings.append(
                    f"The question specifies threshold '{cutoff_val}', but the literal value '{cutoff_val}' was not found in the SQL filter."
                )

        # 4. Metric Alignment Check
        metric_keywords = [
            ("cholesterol", ["cholesterol"]),
            ("restingbp", ["blood pressure", "resting bp", "restingbp", "bp"]),
            ("maxhr", ["max hr", "maximum heart rate", "maxhr", "heart rate"]),
            ("monthlyincome", ["monthly income", "income", "salary"]),
            ("sales", ["sales", "revenue"]),
            ("profit", ["profit"]),
            ("loanamount", ["loan amount", "loanamount"]),
            ("age", ["age"])
        ]
        for col_concept, terms in metric_keywords:
            if any(re.search(r'\b' + re.escape(t) + r'\b', q) for t in terms):
                matched_schema_col = next((by_norm[norm(c)] for c in available_cols if norm(c) == col_concept or any(norm(c) == norm(t) for t in terms)), None)
                if matched_schema_col:
                    checks_performed.append(f"Metric Column Check: {matched_schema_col}")
                    if norm(matched_schema_col) not in norm(sql_l):
                        issues.append(
                            f"Missing Metric: The question explicitly asks about '{matched_schema_col}', "
                            f"but the column '{matched_schema_col}' is not selected or aggregated in the SQL query."
                        )

        # Final alignment assessment
        if issues:
            is_aligned = False
            alignment_status = "INTENT_MISMATCH"
            verdict = "NEEDS_REVIEW"
            confidence = 30.0
            summary = "SQL query does NOT accurately answer the question: " + " | ".join(issues)
        elif warnings:
            is_aligned = True
            alignment_status = "POTENTIAL_MISMATCH"
            verdict = "NEEDS_REVIEW"
            confidence = 65.0
            summary = "SQL query may partially answer the question with warnings: " + " | ".join(warnings)
        else:
            is_aligned = True
            alignment_status = "ALIGNED"
            verdict = "CONFIRMED"
            confidence = 95.0
            summary = "SQL query matches the question intent, requested aggregation, and filters."

        return {
            "is_aligned": is_aligned,
            "alignment_status": alignment_status,
            "verdict": verdict,
            "confidence_score": confidence,
            "issues": issues,
            "warnings": warnings,
            "checks_performed": checks_performed,
            "summary": summary
        }


import re
import math
from typing import List, Dict, Any, Tuple, Set

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
                
                # Ignore very small indices like step 1, 2, 3 if preceded by "Step" or "#"
                start_idx = max(0, m.start() - 6)
                preceding = text[start_idx:m.start()].lower()
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
                "groundedness_score": 100.0,
                "status": "FULLY_GROUNDED_QUALITATIVE",
                "claims_audit": [],
                "verified_count": 0,
                "ungrounded_count": 0,
                "total_claims": 0,
                "message": "Qualitative response with no numerical claims."
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
        groundedness = round((verified_count / total) * 100.0, 1) if total > 0 else 100.0

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

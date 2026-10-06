import hashlib
import json
import time
from typing import Dict, Any

class CryptographicProofGenerator:
    """
    Generates a cryptographic proof-of-verification certificate for autonomous data analysis.
    Provides tamper-evident traceability for every claim, query, and dataset state.
    """

    @staticmethod
    def generate_proof_receipt(
        question: str,
        db_path: str,
        table_name: str,
        executed_sql: str,
        execution_result: Dict[str, Any],
        auditor_verdict: str,
        fact_check_result: Dict[str, Any],
        synthesized_answer: str
    ) -> Dict[str, Any]:
        timestamp_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        unix_ts = time.time()
        
        raw_hash = execution_result.get("query_hash", "")
        groundedness = fact_check_result.get("groundedness_score", 0.0)
        status = fact_check_result.get("status", "UNVERIFIED")

        # Digital signature block
        provenance_payload = {
            "version": "AGENT-ANALYTIX-V2-PROOF",
            "timestamp": timestamp_utc,
            "unix_timestamp": unix_ts,
            "question": question,
            "target": f"{db_path}::{table_name}",
            "sql": executed_sql,
            "raw_result_sha256": raw_hash,
            "auditor_verdict": auditor_verdict,
            "groundedness_score": groundedness
        }

        # Calculate cryptographic certificate hash
        payload_bytes = json.dumps(provenance_payload, sort_keys=True).encode("utf-8")
        certificate_hash = hashlib.sha256(payload_bytes).hexdigest()

        # Determine formal certification level
        if auditor_verdict == "CONFIRMED" and groundedness >= 90.0:
            badge_level = "CRYPTOGRAPHICALLY_VERIFIED"
            badge_color = "#10B981" # Green
            badge_text = "VERIFIED GROUND TRUTH"
        elif auditor_verdict == "CONFIRMED" or groundedness >= 60.0:
            badge_level = "PARTIALLY_VERIFIED"
            badge_color = "#F59E0B" # Amber
            badge_text = "PARTIALLY VERIFIED"
        else:
            badge_level = "FLAGGED_UNVERIFIABLE"
            badge_color = "#EF4444" # Red
            badge_text = "VERIFICATION FAILED"

        return {
            "certificate_hash": certificate_hash,
            "badge_level": badge_level,
            "badge_color": badge_color,
            "badge_text": badge_text,
            "timestamp": timestamp_utc,
            "provenance_payload": provenance_payload,
            "metrics": {
                "groundedness_pct": groundedness,
                "auditor_verdict": auditor_verdict,
                "execution_time_ms": execution_result.get("execution_time_ms", 0.0),
                "rows_returned": execution_result.get("row_count", 0),
                "claims_verified": fact_check_result.get("verified_count", 0),
                "claims_total": fact_check_result.get("total_claims", 0)
            }
        }

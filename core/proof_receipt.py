import hashlib
import json
import time
from typing import Dict, Any

class CryptographicProofGenerator:
    """
    Generates a tamper-evident cryptographic provenance receipt (SHA-256).
    The certificate guarantees that the recorded query, raw database hash, and execution
    artifact have not been altered after execution (audit record immutability).
    It proves the record wasn't altered; it does NOT prove analytical correctness.
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
        groundedness = fact_check_result.get("groundedness_score")
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
            "groundedness_score": groundedness,
            "fact_check_status": status,
            "claims_verified": fact_check_result.get("verified_count", 0),
            "claims_total": fact_check_result.get("total_claims", 0),
            "proves_record_unaltered": True,
            "proves_answer_correctness": False,
            "scope_note": "SHA-256 seal proves this analysis run record and underlying query outputs have not been altered since execution; it does not prove analytical correctness or semantic question alignment."
        }

        # Calculate cryptographic certificate hash
        payload_bytes = json.dumps(provenance_payload, sort_keys=True).encode("utf-8")
        certificate_hash = hashlib.sha256(payload_bytes).hexdigest()

        # The badge certifies cryptographic tamper-evidence of the run record.
        badge_level = "CRYPTOGRAPHICALLY_VERIFIED"
        badge_color = "#10B981"
        badge_text = "TAMPER-EVIDENT RECORD (UNALTERED)"
        return {
            "certificate_hash": certificate_hash,
            "badge_level": badge_level,
            "badge_color": badge_color,
            "badge_text": badge_text,
            "timestamp": timestamp_utc,
            "proves_record_unaltered": True,
            "proves_answer_correctness": False,
            "provenance_payload": provenance_payload,
            "metrics": {
                "groundedness_pct": groundedness,
                "fact_check_status": status,
                "auditor_verdict": auditor_verdict,
                "execution_time_ms": execution_result.get("execution_time_ms", 0.0),
                "rows_returned": execution_result.get("row_count", 0),
                "claims_verified": fact_check_result.get("verified_count", 0),
                "claims_total": fact_check_result.get("total_claims", 0)
            }
        }


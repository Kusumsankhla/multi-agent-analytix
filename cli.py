import argparse
import sys
import json
from core.pipeline import VerifiableAnalysisPipeline

def main():
    parser = argparse.ArgumentParser(
        description="AGENT-ANALYTIX: Multi-Agent Verifiable Autonomous Data Analysis Engine"
    )
    parser.add_argument("--db", default="retail_data.db", help="Path to SQLite database")
    parser.add_argument("--table", default="orders", help="Target table name")
    parser.add_argument("--question", default="What are the top product categories by total profit?", help="Analysis question")
    parser.add_argument("--provider", default="auto", choices=["auto", "openai", "ollama", "fallback"], help="LLM provider")
    parser.add_argument("--json", action="store_true", help="Output full JSON provenance")

    args = parser.parse_args()

    print("======================================================================")
    print("   AGENT-ANALYTIX: VERIFIABLE AUTONOMOUS DATA ANALYSIS ENGINE")
    print("======================================================================")
    print(f"Target Database : {args.db}")
    print(f"Target Table    : {args.table}")
    print(f"Question        : {args.question}")
    print(f"LLM Provider    : {args.provider}")
    print("----------------------------------------------------------------------")

    def progress(stage, msg):
        print(f"[{stage.upper()}] {msg}")

    pipeline = VerifiableAnalysisPipeline(provider=args.provider)
    result = pipeline.run(
        db_path=args.db,
        table_name=args.table,
        question=args.question,
        progress_callback=progress
    )

    print("\n" + "=" * 70)
    print("                      VERIFIED ANALYSIS REPORT")
    print("=" * 70)
    print(result["synthesis"])

    print("\n" + "-" * 70)
    print(" [PROOF OF VERIFICATION: GROUND TRUTH AUDIT TRAIL]")
    print("-" * 70)
    print(f"Executed SQL       : {result['sql']}")
    print(f"Execution Time     : {result['execution']['execution_time_ms']} ms")
    print(f"Row Count Returned : {result['execution']['row_count']}")
    print(f"Raw Output Hash    : {result['execution']['query_hash']}")
    print(f"Auditor Verdict    : {result['audit']['verdict']}")
    print(f"Fact-Check Grounding: {result['fact_check']['groundedness_score']}%")
    print(f"Verification Badge : {result['proof_certificate']['badge_text']} ({result['proof_certificate']['badge_level']})")
    print(f"Certificate Hash   : {result['proof_certificate']['certificate_hash']}")
    print("=" * 70)

    if args.json:
        print("\n--- FULL CRYPTOGRAPHIC PROVENANCE JSON ---")
        print(json.dumps(result["proof_certificate"], indent=2))

if __name__ == "__main__":
    main()

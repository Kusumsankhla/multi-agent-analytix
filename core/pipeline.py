import os
import sqlite3
import pandas as pd
from typing import Dict, Any, Tuple, Optional, Callable

from core.llm_client import LLMClient
from core.sandbox import SQLSandbox
from core.verification_engine import DeterministicFactChecker, QueryIntentValidator
from core.proof_receipt import CryptographicProofGenerator
from core.statistical_engine import StatisticalEngine
from core.visualizer import VisualizerEngine
from core.agents import (
    PlannerAgent,
    CoderAgent,
    AuditorVerifierAgent,
    SynthesisVisualizerAgent
)

class VerifiableAnalysisPipeline:
    """
    High-level orchestrator for verifiable autonomous data analysis.
    Implements the full 6-stage verification loop:
    1. Hypothesis Planning (Planner)
    2. Dialect-Safe Coding (Coder)
    3. Sandboxed Execution & Hash Lineage (Sandbox)
    4. Adversarial Audit (Auditor Verifier)
    5. Statistical Hypothesis Testing & Anomaly Detection (Statistical Engine)
    6. Ground-Truth Fact-Checking, Multi-Chart Visuals, & Cryptographic Certification
    """

    def __init__(self, provider: str = "auto", model: Optional[str] = None):
        self.llm = LLMClient(provider=provider, model=model)
        self.planner = PlannerAgent(self.llm)
        self.coder = CoderAgent(self.llm)
        self.auditor = AuditorVerifierAgent(self.llm)
        self.synthesizer = SynthesisVisualizerAgent(self.llm)

    @staticmethod
    def load_dataset_to_db(csv_path: str, db_path: str, table_name: str, sample_size: Optional[int] = None) -> Tuple[list, dict]:
        """Loads a CSV into SQLite, returning column names and types."""
        df = pd.read_csv(csv_path, encoding="latin1")
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
        conn = sqlite3.connect(db_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        return list(df.columns), {col: str(dtype) for col, dtype in df.dtypes.items()}

    @staticmethod
    def load_dataframe_to_db(df: pd.DataFrame, db_path: str, table_name: str) -> Tuple[list, dict]:
        """Loads an in-memory DataFrame into SQLite."""
        conn = sqlite3.connect(db_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        return list(df.columns), {col: str(dtype) for col, dtype in df.dtypes.items()}

    @staticmethod
    def build_schema_info(db_path: str, table_name: str, columns: list, dtypes: dict, extra_notes: str = "") -> str:
        """Inspects database schema, identifies column cardinality, and generates strict agent guidelines."""
        col_lines = []
        high_cardinality = []
        
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            for col in columns:
                try:
                    cur.execute(f'SELECT COUNT(DISTINCT "{col}") FROM "{table_name}"')
                    distinct = cur.fetchone()[0]
                    if distinct and distinct > 50:
                        high_cardinality.append(col)
                except Exception:
                    pass
                col_lines.append(f"{col} ({dtypes.get(col, 'TEXT')})")
            conn.close()
        except Exception:
            col_lines = [f"{c} ({dtypes.get(c, 'TEXT')})" for c in columns]

        schema_text = (
            f"Database: SQLite file '{db_path}'\n"
            f"Table: '{table_name}'\n"
            f"Columns: {', '.join(col_lines)}\n"
            "Constraints:\n"
            "- SQLite dialect only. Do NOT use Postgres/MySQL syntax.\n"
            "- Always use '1.0 * COUNT(...)' or '1.0 * SUM(...)' when dividing to prevent integer truncation.\n"
            "- Only write SELECT statements. Always apply LIMIT 15 for multi-row outputs.\n"
        )
        if high_cardinality:
            schema_text += f"- High Cardinality Warning (Do NOT GROUP BY directly): {', '.join(high_cardinality[:8])}\n"
        if extra_notes:
            schema_text += f"- Domain Notes: {extra_notes}\n"
            
        return schema_text

    def run(
        self,
        db_path: str,
        table_name: str,
        question: str,
        sample_size: Optional[int] = None,
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end verifiable autonomous analysis pipeline.
        Returns a rich payload with execution traces, audits, scores, statistical tests,
        interactive chart suites, and cryptographic certificates.
        """
        trace = {
            "question": question,
            "db_path": db_path,
            "table_name": table_name,
            "stages": []
        }

        def notify(stage: str, message: str):
            trace["stages"].append({"stage": stage, "message": message})
            if progress_callback:
                progress_callback(stage, message)

        # 1. Inspect Schema
        notify("SCHEMA_INSPECTION", f"Inspecting schema for table '{table_name}'...")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(f'PRAGMA table_info("{table_name}")')
        col_info = cur.fetchall()
        columns = [c[1] for c in col_info]
        dtypes = {c[1]: c[2] for c in col_info}
        conn.close()

        schema_info = self.build_schema_info(db_path, table_name, columns, dtypes)

        # 2. Stage 1: Planning
        notify("PLANNING", "Formulating analytical hypotheses and execution DAG...")
        plan_result = self.planner.plan(question, schema_info)
        plan_text = plan_result["plan_text"]

        # 3. Stage 2: Coding
        notify("CODING", "Generating dialect-safe SQL query...")
        generated_sql = self.coder.generate_sql(question, plan_text, schema_info, table_name)
        if generated_sql.startswith("UNSUPPORTED_FALLBACK_INTENT:"):
            reason = generated_sql.split(":", 1)[1].strip()
            raise ValueError(reason)

        # 4. Stage 3: Sandboxed Execution
        notify("EXECUTION", f"Executing query in sandboxed SQLite environment: {generated_sql}")
        sandbox = SQLSandbox(db_path=db_path)
        execution_result = sandbox.execute(generated_sql)

        # Self-correction loop: if query errored, retry once with error context
        if not execution_result.get("success"):
            notify("SELF_CORRECTION", f"Query failed ({execution_result.get('error')}). Initiating self-correction...")
            error_msg = execution_result.get("error")
            correction_prompt = f"Previous query failed with error: {error_msg}. Fix the query and ensure only valid SQLite syntax."
            generated_sql = self.coder.generate_sql(question, f"{plan_text}\n{correction_prompt}", schema_info, table_name)
            if generated_sql.startswith("UNSUPPORTED_FALLBACK_INTENT:"):
                raise ValueError(generated_sql.split(":", 1)[1].strip())
            execution_result = sandbox.execute(generated_sql)

        # 5. Stage 4: Adversarial Audit & Semantic Intent Validation
        notify("AUDITING", "Conducting adversarial verification on query and raw results...")
        audit_result = self.auditor.audit(question, generated_sql, execution_result, schema_info)

        # Deterministic Intent Validation: Verifies whether the SQL query actually answers the question
        intent_validation = QueryIntentValidator.validate_intent(
            question=question,
            sql=generated_sql,
            schema_info=schema_info,
            columns=execution_result.get("columns", []),
            rows=execution_result.get("rows", [])
        )

        if not intent_validation["is_aligned"]:
            audit_result["model_verdict"] = audit_result.get("verdict", "CONFIRMED")
            audit_result["verdict"] = intent_validation["verdict"]  # "NEEDS_REVIEW" or "INTENT_MISMATCH"
            audit_result["reasoning"] = (
                f"🚨 QUESTION-TO-SQL INTENT MISMATCH DETECTED:\n"
                f"- Issues: {'; '.join(intent_validation['issues'])}\n\n"
                f"Auditor Evaluation:\n{audit_result.get('reasoning', '')}"
            )
        elif intent_validation.get("warnings"):
            if audit_result.get("verdict") == "CONFIRMED":
                audit_result["verdict"] = "NEEDS_REVIEW"
            audit_result["reasoning"] = (
                f"⚠️ INTENT ALIGNMENT NOTE: {'; '.join(intent_validation['warnings'])}\n\n"
                f"Auditor Evaluation:\n{audit_result.get('reasoning', '')}"
            )

        # 6. Stage 5: Statistical Engine (Hypothesis Testing & Anomaly Detection)
        notify("STATISTICS", "Computing empirical hypothesis tests, p-values, and anomaly dispersion...")
        stats_data = StatisticalEngine.analyze_dataset_statistics(
            columns=execution_result.get("columns", []),
            rows=execution_result.get("rows", []),
            question=question
        )

        # 7. Stage 6: Synthesis & Multi-Chart Visuals
        notify("SYNTHESIS", "Formulating verified executive synthesis and chart suite...")
        synthesis_result = self.synthesizer.synthesize(
            question=question,
            sql=generated_sql,
            execution_result=execution_result,
            auditor_feedback=audit_result.get("reasoning", "")
        )
        verified_answer = synthesis_result["verified_answer"]
        chart_spec = synthesis_result.get("chart_spec")

        # Generate Multi-Chart Suite (Plotly Figures)
        chart_suite = VisualizerEngine.generate_chart_suite(
            columns=execution_result.get("columns", []),
            rows=execution_result.get("rows", []),
            question=question,
            stats_data=stats_data
        )

        # 8. Stage 7: Deterministic Fact-Checking & Hallucination Check
        notify("FACT_CHECKING", "Running deterministic ground-truth verification on prose numbers...")
        fact_check = DeterministicFactChecker.verify_claims(
            prose_answer=verified_answer,
            execution_result=execution_result
        )

        # 9. Stage 8: Cryptographic Proof Generation
        notify("CERTIFICATION", "Generating tamper-evident cryptographic proof certificate...")
        proof_certificate = CryptographicProofGenerator.generate_proof_receipt(
            question=question,
            db_path=db_path,
            table_name=table_name,
            executed_sql=generated_sql,
            execution_result=execution_result,
            auditor_verdict=audit_result.get("verdict", "FLAGGED"),
            fact_check_result=fact_check,
            synthesized_answer=verified_answer
        )

        notify("COMPLETE", "Verifiable analysis pipeline completed successfully.")

        return {
            "question": question,
            "plan": plan_text,
            "sql": generated_sql,
            "execution": execution_result,
            "audit": audit_result,
            "statistics": stats_data,
            "synthesis": verified_answer,
            "chart_spec": chart_spec,
            "chart_suite": chart_suite,
            "fact_check": fact_check,
            "intent_validation": intent_validation,
            "proof_certificate": proof_certificate,
            "llm_runtime": {
                "configured_provider": self.llm.configured_provider,
                "active_provider": self.llm.provider,
                "model": getattr(self.llm, "model", "unknown"),
                "fallback_used": self.llm.fallback_used,
                "fallback_reason": self.llm.fallback_reason,
                "successful_llm_calls": self.llm.llm_calls_succeeded
            },
            "trace": trace
        }

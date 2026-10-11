import unittest
import os
import sqlite3
from core.sandbox import SQLSandbox, SecurityViolationError
from core.verification_engine import DeterministicFactChecker, QueryIntentValidator
from core.proof_receipt import CryptographicProofGenerator
from core.statistical_engine import StatisticalEngine
from core.agents import SynthesisVisualizerAgent

class TestVerificationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_audit.db"
        conn = sqlite3.connect(cls.test_db)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS metrics (category TEXT, revenue REAL, orders INT)")
        cur.execute("DELETE FROM metrics")
        cur.executemany("INSERT INTO metrics VALUES (?, ?, ?)", [
            ("Tech", 45000.5, 120),
            ("Office", 23000.0, 85),
            ("Furniture", 18500.25, 42)
        ])
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_sandbox_safety(self):
        sandbox = SQLSandbox(self.test_db)
        
        # Test safe SELECT
        res = sandbox.execute("SELECT category, SUM(revenue) FROM metrics GROUP BY category;")
        self.assertTrue(res["success"])
        self.assertEqual(len(res["rows"]), 3)
        self.assertTrue(len(res["query_hash"]) > 0)

        # Test injection / destructive command blocked
        drop_res = sandbox.execute("DROP TABLE metrics;")
        self.assertFalse(drop_res["success"])
        self.assertIn("Security Violation", drop_res["error"])

    def test_fact_checker_grounding(self):
        execution_res = {
            "success": True,
            "columns": ["category", "revenue"],
            "rows": [["Tech", 45000.5], ["Office", 23000.0]]
        }
        
        # Grounded text
        grounded_text = "Tech generated $45,000.50 in revenue, whereas Office generated $23,000.00."
        fc_res = DeterministicFactChecker.verify_claims(grounded_text, execution_res)
        self.assertEqual(fc_res["status"], "FULLY_GROUNDED")
        self.assertGreaterEqual(fc_res["groundedness_score"], 90.0)

        # Hallucinated text
        hallucinated_text = "Tech generated $999,999 with 8,500 orders and a 94.2% satisfaction rate."
        fc_halluc = DeterministicFactChecker.verify_claims(hallucinated_text, execution_res)
        self.assertEqual(fc_halluc["status"], "HALLUCINATION_DETECTED")
        self.assertLess(fc_halluc["groundedness_score"], 20.0)

    def test_fact_checker_zero_claims_not_100(self):
        execution_res = {
            "success": True,
            "columns": ["category", "revenue"],
            "rows": [["Tech", 45000.5], ["Office", 23000.0]]
        }
        qualitative_text = "The technology category performed well compared to office supplies."
        res = DeterministicFactChecker.verify_claims(qualitative_text, execution_res)
        self.assertIsNone(res["groundedness_score"])
        self.assertEqual(res["total_claims"], 0)
        self.assertEqual(res["status"], "NO_CLAIMS_TO_VERIFY")

    def test_synthesis_replaces_sql_only_model_output_with_grounded_results(self):
        class SqlOnlyLLM:
            @staticmethod
            def generate(system_prompt, user_prompt, max_tokens):
                return "```sql\nSELECT * FROM transactions;\n```"

        agent = SynthesisVisualizerAgent(SqlOnlyLLM())
        result = agent.synthesize(
            question="Which transaction patterns are most associated with fraud?",
            sql="SELECT ProductCD, COUNT(*) AS fraud_count FROM transactions GROUP BY ProductCD;",
            execution_result={
                "columns": ["ProductCD", "fraud_count"],
                "rows": [["W", 12], ["C", 5]],
            },
            auditor_feedback="NEEDS_REVIEW",
        )

        self.assertIn("### Direct Answer", result["verified_answer"])
        self.assertIn("| W | 12 |", result["verified_answer"])
        self.assertNotIn("SELECT *", result["verified_answer"])

    def test_query_intent_validator_age_mismatch(self):
        # Age example: Question asks for average age of heart disease patients,
        # but SQL only groups by age and counts without computing AVG and without HeartDisease filter
        question = "What is the average age of heart disease patients?"
        bad_sql = "SELECT Age, COUNT(*) FROM heart GROUP BY Age ORDER BY COUNT(*) DESC LIMIT 15;"
        schema = "Columns: Age (INTEGER), HeartDisease (INTEGER), Cholesterol (INTEGER)"
        
        validation = QueryIntentValidator.validate_intent(question, bad_sql, schema)
        self.assertFalse(validation["is_aligned"])
        self.assertEqual(validation["verdict"], "NEEDS_REVIEW")
        self.assertGreaterEqual(len(validation["issues"]), 1)
        # Issues should flag missing outcome filter and aggregation mismatch
        issues_text = " ".join(validation["issues"]).lower()
        self.assertTrue("outcome" in issues_text or "average" in issues_text or "count" in issues_text)

        # Aligned query test
        good_sql = "SELECT ROUND(AVG(Age), 2) AS avg_age FROM heart WHERE HeartDisease = 1;"
        good_validation = QueryIntentValidator.validate_intent(question, good_sql, schema)
        self.assertTrue(good_validation["is_aligned"])
        self.assertEqual(good_validation["verdict"], "CONFIRMED")

    def test_statistical_engine_single_value_z_score(self):
        columns = ["Age", "Count"]
        rows = [
            ["54", 51],
            ["53", 48],
            ["52", 35],
            ["50", 25],
            ["45", 20]
        ]
        stats = StatisticalEngine.analyze_dataset_statistics(columns, rows, "Age distribution")
        self.assertTrue(stats["has_stats"])
        # Top value is 51 for age 54
        self.assertEqual(stats["top_entity"], "54")
        self.assertEqual(stats["top_value"], 51)
        # Single value z-score must match: z = (51 - mean) / std_dev
        import math
        vals = [51, 48, 35, 25, 20]
        mean = sum(vals) / 5
        std = math.sqrt(sum((x - mean)**2 for x in vals) / 4)
        expected_z = round((51 - mean) / std, 2)
        self.assertEqual(stats["top_z"], expected_z)
        # Outlier table entries must have matching z-scores
        if stats["anomalies"]:
            top_anomaly = next((a for a in stats["anomalies"] if a["entity"] == "54"), None)
            if top_anomaly:
                self.assertEqual(top_anomaly["z_score"], expected_z)

    def test_proof_receipt_generation(self):
        exec_res = {
            "success": True,
            "query_hash": "a1b2c3d4e5",
            "execution_time_ms": 12.4,
            "row_count": 2
        }
        fact_res = {
            "groundedness_score": 100.0,
            "verified_count": 2,
            "total_claims": 2,
            "status": "FULLY_GROUNDED"
        }
        receipt = CryptographicProofGenerator.generate_proof_receipt(
            question="What is tech revenue?",
            db_path=self.test_db,
            table_name="metrics",
            executed_sql="SELECT category, revenue FROM metrics WHERE category='Tech'",
            execution_result=exec_res,
            auditor_verdict="CONFIRMED",
            fact_check_result=fact_res,
            synthesized_answer="Tech revenue is 45000.5."
        )
        self.assertEqual(receipt["badge_level"], "CRYPTOGRAPHICALLY_VERIFIED")
        self.assertTrue(receipt["proves_record_unaltered"])
        self.assertFalse(receipt["proves_answer_correctness"])
        self.assertTrue(len(receipt["certificate_hash"]) == 64)

if __name__ == "__main__":
    unittest.main()

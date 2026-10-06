import unittest
import os
import sqlite3
from core.sandbox import SQLSandbox, SecurityViolationError
from core.verification_engine import DeterministicFactChecker
from core.proof_receipt import CryptographicProofGenerator

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
        self.assertTrue(len(receipt["certificate_hash"]) == 64)

if __name__ == "__main__":
    unittest.main()

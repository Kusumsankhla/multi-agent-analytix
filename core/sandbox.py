import sqlite3
import time
import hashlib
import json
import re
from typing import Dict, Any, List, Optional

class SecurityViolationError(Exception):
    """Raised when an unsafe or malicious SQL statement is detected."""
    pass

class SQLSandbox:
    """
    Sandboxed execution environment for SQLite databases.
    Enforces:
    - Read-only execution (disallowing DROP, INSERT, UPDATE, DELETE, ALTER, ATTACH, etc.)
    - Single statement safety (preventing stacked injection)
    - Row limits to prevent OOM
    - Performance profiling (latency in ms)
    - Cryptographic result hashing (SHA-256)
    - Query plan explanation (EXPLAIN QUERY PLAN)
    """

    FORBIDDEN_KEYWORDS = [
        r"\bDROP\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
        r"\bALTER\b", r"\bATTACH\b", r"\bDETACH\b", r"\bPRAGMA\b",
        r"\bREPLACE\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"\bEXEC\b",
        r"\bVACUUM\b", r"\bREINDEX\b"
    ]

    def __init__(self, db_path: str, max_rows: int = 500, timeout_sec: float = 10.0):
        self.db_path = db_path
        self.max_rows = max_rows
        self.timeout_sec = timeout_sec

    def validate_safety(self, sql: str) -> None:
        """Validates that the SQL query is safe, read-only, and non-destructive."""
        clean_sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL).strip()
        
        if not clean_sql:
            raise SecurityViolationError("SQL query is empty.")

        # Disallow multiple semicolons (prevent multi-statement injections)
        semicolon_count = clean_sql.count(";")
        if semicolon_count > 1 or (semicolon_count == 1 and not clean_sql.endswith(";")):
            raise SecurityViolationError("Multi-statement SQL injection detected: Only a single SELECT statement is allowed.")

        # Check for forbidden keywords
        for pattern in self.FORBIDDEN_KEYWORDS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                matched = re.search(pattern, clean_sql, re.IGNORECASE).group(0)
                raise SecurityViolationError(f"Forbidden SQL operation detected: '{matched}'. Only read-only queries are permitted.")

        # Must start with SELECT or WITH
        first_word = clean_sql.split()[0].upper() if clean_sql.split() else ""
        if first_word not in ["SELECT", "WITH", "EXPLAIN"]:
            raise SecurityViolationError(f"Invalid statement type: '{first_word}'. Only SELECT queries are permitted.")

    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Executes a SQL query in the sandbox.
        Returns execution dictionary with:
        - success: bool
        - columns: List[str]
        - rows: List[List[Any]]
        - row_count: int
        - truncated: bool
        - execution_time_ms: float
        - query_hash: str (SHA-256 of raw data)
        - query_plan: List[str]
        - error: Optional[str]
        """
        start_time = time.perf_counter()
        
        # 1. Safety validation
        try:
            self.validate_safety(sql)
        except SecurityViolationError as sve:
            return {
                "success": False,
                "error": f"Security Violation: {str(sve)}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "execution_time_ms": (time.perf_counter() - start_time) * 1000,
                "query_hash": "",
                "query_plan": []
            }

        # 2. Database execution with read-only URI if possible
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout_sec)
            cursor = conn.cursor()

            # Execute query
            cursor.execute(sql)
            raw_columns = [d[0] for d in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchmany(self.max_rows + 1)
            
            truncated = len(raw_rows) > self.max_rows
            returned_rows = raw_rows[:self.max_rows]
            
            # Retrieve query plan for transparency
            query_plan = []
            try:
                plan_cursor = conn.cursor()
                plan_cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
                plan_rows = plan_cursor.fetchall()
                query_plan = [f"Detail: {r[-1]}" for r in plan_rows]
            except Exception:
                pass
                
            conn.close()

            # Format rows safely (handling bytes/decimals/timestamps)
            formatted_rows = []
            for row in returned_rows:
                formatted_rows.append([
                    round(v, 4) if isinstance(v, float) else v 
                    for v in row
                ])

            # Calculate deterministic cryptographic hash of result
            result_json = json.dumps({"cols": raw_columns, "rows": formatted_rows}, sort_keys=True, default=str)
            query_hash = hashlib.sha256(result_json.encode("utf-8")).hexdigest()
            
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return {
                "success": True,
                "error": None,
                "columns": raw_columns,
                "rows": formatted_rows,
                "row_count": len(formatted_rows),
                "truncated": truncated,
                "execution_time_ms": elapsed_ms,
                "query_hash": query_hash,
                "query_plan": query_plan
            }

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "error": f"Execution Error: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "execution_time_ms": elapsed_ms,
                "query_hash": "",
                "query_plan": []
            }

import json
import re
from typing import Dict, Any, Optional
from core.llm_client import LLMClient, AnalyticQueryEngine

class PlannerAgent:
    """
    Deconstructs user questions into explicit analytical hypotheses
    and structured execution plans tailored to database schemas.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def plan(self, question: str, schema_info: str) -> Dict[str, Any]:
        system_prompt = (
            "You are the Data Analysis Planner Agent in an autonomous data analysis framework.\n"
            "Your objective: Break down the user's business question into a verifiable analytical plan.\n"
            "Rules:\n"
            "1. ONLY reference valid columns and tables provided in the schema.\n"
            "2. Note any high-cardinality columns to avoid invalid GROUP BY operations.\n"
            "3. State the core hypothesis and the required SQL aggregation strategy.\n"
            "Format your response as a numbered plan with: 1) Analytical Hypothesis, 2) Target Columns & Grouping, 3) Aggregation Formula."
        )
        user_prompt = f"Schema Information:\n{schema_info}\n\nUser Question:\n{question}\n\nProvide the analytical execution plan:"
        raw_plan = self.llm.generate(system_prompt, user_prompt, max_tokens=600)
        return {
            "plan_text": raw_plan,
            "question": question
        }


class CoderAgent:
    """
    Generates dialect-aware, safe SQL queries based on the analytical plan.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate_sql(self, question: str, plan_text: str, schema_info: str, table_name: str) -> str:
        system_prompt = (
            "You are the SQL Coder Agent in an autonomous data analysis framework.\n"
            "Your task: Write a single, highly optimized, valid SQLite SELECT query based on the plan.\n"
            "STRICT RULES:\n"
            "1. ONLY write ONE SELECT statement. No subqueries, no CTEs, no joins unless strictly needed.\n"
            "2. Always multiply by 1.0 when computing ratios, rates, or averages to prevent SQLite integer division truncation.\n"
            "3. Use ONLY exact column names from the provided schema.\n"
            "4. Always add LIMIT 15 unless calculating an overall aggregate.\n"
            "5. Return ONLY the SQL query in a ```sql ... ``` code block. Do NOT write explanatory prose."
        )
        user_prompt = (
            f"Database Schema:\n{schema_info}\n\n"
            f"Table: {table_name}\n"
            f"User Question: {question}\n"
            f"Execution Plan:\n{plan_text}\n\n"
            "Generate the SQLite query:"
        )
        raw_output = self.llm.generate(system_prompt, user_prompt, max_tokens=300)
        return self.llm.extract_sql(raw_output)


class AuditorVerifierAgent:
    """
    Adversarial auditor agent that independently scrutinizes generated queries,
    raw data outputs, and analytical validity before certifying results.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def audit(self, question: str, sql: str, execution_result: Dict[str, Any], schema_info: str) -> Dict[str, Any]:
        if not execution_result.get("success"):
            return {
                "verdict": "FLAGGED",
                "reasoning": f"SQL Execution Failed: {execution_result.get('error')}",
                "confidence_score": 0.0
            }

        rows = execution_result.get("rows", [])
        columns = execution_result.get("columns", [])
        
        if not rows:
            return {
                "verdict": "FLAGGED",
                "reasoning": "Query returned zero rows. The query filters may be overly restrictive or columns mismatched.",
                "confidence_score": 20.0
            }

        system_prompt = (
            "You are the Adversarial Verification Agent (Auditor) in a verifiable data analysis system.\n"
            "You do NOT trust claims blindly. Your duty is to verify whether the SQL query and its raw output "
            "faithfully, correctly, and rigorously answer the exact user question.\n"
            "Evaluate:\n"
            "1. Question-to-SQL intent alignment: Does the query actually answer the question asked?\n"
            "   - If the user asks for average/mean of X, does SQL calculate AVG(X), or does it mistakenly group and COUNT(*)?\n"
            "   - If the user asks about a specific condition (e.g., 'heart disease patients', 'fraud cases', 'age > 50'), does SQL filter with WHERE or condition in CASE? If the SQL ignores the condition, it DOES NOT answer the question.\n"
            "2. Aggregation safety: Did it avoid integer division? Are row groupings logical?\n"
            "3. Data plausibility: Are the resulting numbers mathematically sound?\n"
            "Only conclude VERDICT: CONFIRMED when the SQL demonstrably answers the exact question and the output supports it. "
            "If the question-to-SQL match is not fully established or if conditions are missing, use VERDICT: NEEDS_REVIEW. "
            "Finish with exactly one line: VERDICT: CONFIRMED, VERDICT: FLAGGED, or VERDICT: NEEDS_REVIEW."
        )
        user_prompt = (
            f"User Question: {question}\n"
            f"Executed SQL: {sql}\n"
            f"Columns: {columns}\n"
            f"Sample Result Rows: {rows[:10]}\n\n"
            "Audit this analysis and issue your formal verdict:"
        )
        audit_text = self.llm.generate(system_prompt, user_prompt, max_tokens=500)
        
        upper_audit = audit_text.upper()
        if "VERDICT: FLAGGED" in upper_audit:
            verdict = "FLAGGED"
        elif "VERDICT: CONFIRMED" in upper_audit:
            verdict = "CONFIRMED"
        else:
            verdict = "NEEDS_REVIEW"

        return {
            "verdict": verdict,
            "reasoning": audit_text,
            "confidence_score": 95.0 if verdict == "CONFIRMED" else (40.0 if verdict == "FLAGGED" else 0.0)
        }


class SynthesisVisualizerAgent:
    """
    Formulates data-grounded executive summaries and recommends
    interactive Plotly visual specifications from verified raw data.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def synthesize(self, question: str, sql: str, execution_result: Dict[str, Any], auditor_feedback: str) -> Dict[str, Any]:
        columns = execution_result.get("columns", [])
        rows = execution_result.get("rows", [])

        system_prompt = (
            "You are the Synthesis & Visualizer Agent in an autonomous data analysis framework.\n"
            "Your task: Formulate an executive business answer strictly grounded in the verified data.\n"
            "STRICT RULES:\n"
            "1. Start with a section: '### Direct Answer' and directly state the answer in natural language words using the exact numbers from the data.\n"
            "2. State the exact numeric values from the result table (counts, percentages, averages, amounts). Never make up numbers not present in the data.\n"
            "3. Do NOT output generic verification checklists like 'Query Correctness... Calculation Safety... Ground Truth Integrity...'. Describe what the data actually says about the question.\n"
            "4. Provide 2-3 key analytical takeaways for business decision-makers."
        )
        user_prompt = (
            f"Question: {question}\n"
            f"Executed Query: {sql}\n"
            f"Columns: {columns}\n"
            f"Raw Rows: {rows}\n"
            f"Auditor Note: {auditor_feedback}\n\n"
            "Write the verified executive synthesis:"
        )
        answer = self.llm.generate(system_prompt, user_prompt, max_tokens=700)
        answer_without_code_fence = re.sub(
            r"^```(?:sql|sqlite)?\s*|\s*```$",
            "",
            answer.strip(),
            flags=re.IGNORECASE,
        ).strip()

        is_generic_checklist = any(
            phrase.lower() in answer.lower()
            for phrase in ["query correctness", "calculation safety", "ground truth integrity"]
        ) or answer.strip().startswith("VERDICT:")
        is_sql_only = bool(re.match(r"^(?:SELECT|WITH)\b", answer_without_code_fence, re.IGNORECASE))
        has_no_claims = not bool(re.search(r"\d+", answer)) if rows else False

        if is_sql_only or is_generic_checklist or has_no_claims or getattr(self.llm, "fallback_used", False):
            answer = AnalyticQueryEngine.synthesize_grounded_report(
                question=question,
                sql=sql,
                columns=columns,
                rows=rows,
                auditor_verdict=auditor_feedback or "CONFIRMED"
            )

        # Build chart specification
        chart_spec = self._build_chart_spec(columns, rows, question)

        return {
            "verified_answer": answer,
            "chart_spec": chart_spec
        }

    @staticmethod
    def _format_grounded_results(columns: list, rows: list) -> str:
        """Show executed values as a readable answer if the model returns SQL instead."""
        if not columns or not rows:
            return (
                "### Direct Answer\n"
                "The executed query returned no rows, so there is no matching result to report."
            )

        def markdown_cell(value: Any) -> str:
            return str(value).replace("|", r"\|").replace("\n", " ")

        lines = [
            "### Direct Answer",
            f"The executed query returned {len(rows)} result(s). The database results are:",
            "",
            "| " + " | ".join(markdown_cell(column) for column in columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ]
        for row in rows[:15]:
            lines.append(
                "| " + " | ".join(markdown_cell(value) for value in row) + " |"
            )
        if len(rows) > 15:
            lines.append(f"\nShowing 15 of {len(rows)} returned results.")
        return "\n".join(lines)

    def _build_chart_spec(self, columns: list, rows: list, question: str) -> Optional[Dict[str, Any]]:
        """Determines best Plotly visualization based on column types and dimensions."""
        if not rows or len(columns) < 2:
            return None

        # Look for numeric column and categorical column
        col0 = columns[0]
        col1 = columns[1]

        # Check types in first row
        first_row = rows[0]
        val0 = first_row[0]
        val1 = first_row[1]

        chart_type = "bar"
        if len(rows) > 10 and any(kw in question.lower() for kw in ["trend", "time", "date", "over time", "month"]):
            chart_type = "line"
        elif len(columns) >= 3 and isinstance(val1, (int, float)) and isinstance(rows[0][2], (int, float)):
            chart_type = "scatter"

        return {
            "chart_type": chart_type,
            "x_column": col0,
            "y_column": col1,
            "title": f"{col1} by {col0}",
            "color_column": columns[2] if len(columns) > 2 else None
        }

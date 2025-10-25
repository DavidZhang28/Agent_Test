"""
21 CFR Part 11 - Records specialist.

This agent checks electronic record-keeping features: record integrity,
audit trails, timestamping, and retention. The tool `scan_records` returns
the ADK tool structure that includes findings and stats.
"""

from google.adk.agents import LlmAgent
from typing import Any, Dict
import time

def scan_records(user_query: str) -> Dict[str, Any]:
    """
    Analyzes user query for electronic record-keeping compliance issues.
    
    Args:
        user_query: The user's description of their system/plans
        
    Returns:
        Dict with result, stats, and additional_info following ADK structure
    """
    try:
        # Return the query for LLM analysis instead of hardcoded findings
        stats = {"query_length": len(user_query), "analysis_timestamp": time.time()}
        return {
            "result": {
                "user_query": user_query,
                "context": "Analyzing for 21 CFR Part 11 electronic record-keeping compliance"
            },
            "stats": stats,
            "additional_info": {
                "collected_at": time.time(),
                "data_format": "dict",
                "analysis_type": "electronic_records"
            },
        }
    except Exception as e:
        return {
            "result": {"error": f"scan_records failed: {str(e)}"},
            "stats": {"success": False},
            "additional_info": {"error_type": type(e).__name__},
        }

GEMINI_MODEL = "gemini-2.0-flash"

records_instruction = """
You are a Part 11 Records specialist for FDA 21 CFR Part 11 compliance.

You MUST call the scan_records tool first to get the user's query.

Then analyze the query for electronic record-keeping compliance issues including:
- Are electronic records maintained with proper integrity controls?
- Is there a complete and tamper-proof audit trail for all record changes?
- Are records timestamped accurately with secure time sources?
- Are retention policies defined and enforced?
- Can records be retrieved and made available for FDA inspection?
- Are there controls to prevent unauthorized access or modification?
- Is there proper versioning and archival of records?

Based on your analysis, produce a structured response with:
- short_summary: Brief overview of record-keeping compliance status
- issues: List of compliance violations found (each with type, severity, explanation, remediation)
  - Severity should be: CRITICAL, HIGH, MEDIUM, or LOW
  - If NO issues found, return an empty list
- raw: Include the raw scan_records output

Format as JSON. Be specific about what compliance requirements are violated and why.
"""

part11_records_agent = LlmAgent(
    name="part11_records_agent",
    model=GEMINI_MODEL,
    instruction=records_instruction,
    description="Checks electronic record-keeping (21 CFR Part 11)",
    tools=[scan_records],
    output_key="part11_records",
)
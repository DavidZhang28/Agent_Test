"""
21 CFR Part 11 - Signatures specialist.

Checks implementation of electronic signatures, signature linking to records,
and signature controls. Tool `scan_signatures` implements the check and returns
the ADK tool structure.
"""

from google.adk.agents import LlmAgent
from typing import Any, Dict
import time

def scan_signatures(user_query: str) -> Dict[str, Any]:
    """
    Analyzes user query for electronic signature compliance issues.
    
    Args:
        user_query: The user's description of their system/plans
        
    Returns:
        Dict with result, stats, and additional_info following ADK structure
    """
    try:
        # Instead of hardcoded findings, return the query for LLM analysis
        # The LLM will analyze this and determine actual compliance issues
        stats = {"query_length": len(user_query), "analysis_timestamp": time.time()}
        return {
            "result": {
                "user_query": user_query,
                "context": "Analyzing for 21 CFR Part 11 electronic signature compliance"
            },
            "stats": stats,
            "additional_info": {
                "collected_at": time.time(),
                "data_format": "dict",
                "analysis_type": "electronic_signatures"
            },
        }
    except Exception as e:
        return {
            "result": {"error": f"scan_signatures failed: {str(e)}"},
            "stats": {"success": False},
            "additional_info": {"error_type": type(e).__name__},
        }

GEMINI_MODEL = "gemini-2.0-flash"

signatures_instruction = """
You are a Part 11 Signatures specialist for FDA 21 CFR Part 11 compliance.

You MUST call the scan_signatures tool first to get the user's query.

Then analyze the query for electronic signature compliance issues including:
- Are electronic signatures properly implemented and validated?
- Are signatures linked to their respective records?
- Are there controls to ensure signature authenticity and non-repudiation?
- Is there a system to verify the identity of the signer?
- Are signature events logged with timestamps?

Based on your analysis, produce a structured response with:
- short_summary: Brief overview of signature compliance status
- issues: List of compliance violations found (each with type, severity, explanation, remediation)
  - Severity should be: CRITICAL, HIGH, MEDIUM, or LOW
  - If NO issues found, return an empty list
- raw: Include the raw scan_signatures output

Format as JSON. Be specific about what compliance requirements are violated and why.
"""

part11_signatures_agent = LlmAgent(
    name="part11_signatures_agent",
    model=GEMINI_MODEL,
    instruction=signatures_instruction,
    description="Checks electronic signatures for Part 11",
    tools=[scan_signatures],
    output_key="part11_signatures",
)
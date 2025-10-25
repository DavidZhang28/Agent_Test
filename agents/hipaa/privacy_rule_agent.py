"""
HIPAA Privacy Rule Specialist Agent and its tool(s).

This agent examines user actions/record-access logs and checks for
potential privacy rule violations. The agent MUST call the provided 'scan_privacy' tool.

The tool returns the ADK custom structure:
{
  "result": {...},           # detected events, sample context
  "stats": {...},            # counts and severity summary
  "additional_info": {...},  # timestamps, data-format, etc.
}
"""

from google.adk.agents import LlmAgent
from typing import Any, Dict
import time

def scan_privacy(user_query: str) -> Dict[str, Any]:
    """
    Analyzes user query for HIPAA Privacy Rule compliance.
    
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
                "context": "Analyzing for HIPAA Privacy Rule compliance"
            },
            "stats": stats,
            "additional_info": {
                "collected_at": time.time(),
                "data_format": "dict",
                "analysis_type": "privacy_rule"
            },
        }
    except Exception as e:
        return {
            "result": {"error": f"scan_privacy failed: {str(e)}"},
            "stats": {"success": False},
            "additional_info": {"error_type": type(e).__name__},
        }


GEMINI_MODEL = "gemini-2.0-flash"

privacy_instruction = """
You are a HIPAA Privacy Rule specialist.

You MUST call the scan_privacy tool first to get the user's query.

Then analyze the query for HIPAA Privacy Rule compliance including:
- Is there proper authorization for use and disclosure of PHI (Protected Health Information)?
- Are minimum necessary standards being followed?
- Is patient consent obtained where required?
- Are Notice of Privacy Practices provided to patients?
- Are there proper access controls limiting who can view PHI?
- Is PHI being shared with unauthorized parties (e.g., partner clinics without BAA)?
- Are patients' rights being respected (access, amendment, accounting of disclosures)?
- Is PHI being used only for treatment, payment, or healthcare operations?
- Are there safeguards against incidental disclosures?

Based on your analysis, produce a structured response with:
- short_summary: Brief overview of Privacy Rule compliance status
- issues: List of privacy violations found (each with type, severity, explanation, remediation)
  - Severity should be: CRITICAL, HIGH, MEDIUM, or LOW
  - If NO issues found, return an empty list
- recommendations: Specific actions to achieve compliance
- raw: Include the raw scan_privacy output

Format as JSON. Be specific about which Privacy Rule requirements are violated and why.
"""

hipaa_privacy_agent = LlmAgent(
    name="hipaa_privacy_agent",
    model=GEMINI_MODEL,
    instruction=privacy_instruction,
    description="Identifies HIPAA Privacy Rule issues",
    tools=[scan_privacy],
    output_key="hipaa_privacy",
)
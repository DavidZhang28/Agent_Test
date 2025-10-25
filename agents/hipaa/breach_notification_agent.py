"""
HIPAA Breach Notification Specialist and tool.

This agent assesses whether detected events meet the definition of a breach,
and determines notification obligations. The tool 'assess_breach' simulates
the logic and returns the ADK tool structure.
"""

from google.adk.agents import LlmAgent
from typing import Any, Dict
import time

def assess_breach(user_query: str) -> Dict[str, Any]:
    """
    Analyzes user query for HIPAA breach notification compliance.
    
    Args:
        user_query: The user's description of their system/plans
        
    Returns:
        Dict with result, stats, and additional_info following ADK structure
    """
    try:
        # Return the query for LLM analysis instead of hardcoded breach
        stats = {"query_length": len(user_query), "analysis_timestamp": time.time()}
        return {
            "result": {
                "user_query": user_query,
                "context": "Analyzing for HIPAA breach notification requirements"
            },
            "stats": stats,
            "additional_info": {
                "collected_at": time.time(),
                "data_format": "dict",
                "analysis_type": "breach_notification"
            },
        }
    except Exception as e:
        return {
            "result": {"error": f"assess_breach failed: {str(e)}"},
            "stats": {"success": False},
            "additional_info": {"error_type": type(e).__name__},
        }

GEMINI_MODEL = "gemini-2.0-flash"

breach_instruction = """
You are a Breach Notification specialist for HIPAA.

You MUST call the assess_breach tool first to get the user's query.

Then analyze the query to assess breach notification compliance including:
- Does the described system have proper safeguards to prevent unauthorized disclosure?
- Are there mechanisms to detect if PHI has been acquired, accessed, used, or disclosed?
- Is there a breach notification policy and procedure in place?
- Are notification timelines understood (60 days for individuals, HHS reporting)?
- Are there processes for breach risk assessments?
- Does the system track potentially affected individuals?
- Are there contracts with business associates that include breach notification provisions?

Based on your analysis, produce a structured response with:
- short_summary: Brief overview of breach notification readiness
- breach_risk_assessment: Evaluate likelihood and severity of potential breaches
- issues: List of compliance gaps (each with type, severity, explanation, remediation)
  - Severity should be: CRITICAL, HIGH, MEDIUM, or LOW
  - If NO issues found, return an empty list
- notification_requirements: If gaps exist, specify what notifications would be required
- raw: Include the raw assess_breach output

Format as JSON. Focus on preventive controls and incident response readiness.
"""

hipaa_breach_agent = LlmAgent(
    name="hipaa_breach_agent",
    model=GEMINI_MODEL,
    instruction=breach_instruction,
    description="Assesses breach and notification obligations for HIPAA",
    tools=[assess_breach],
    output_key="hipaa_breach",
)
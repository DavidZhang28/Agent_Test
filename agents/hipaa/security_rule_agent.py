"""
HIPAA Security Rule Specialist Agent + tool.

This agent inspects technical safeguards (access controls, authentication events)
and returns findings in the ADK tool structure. The LLM agent MUST call get_security_findings tool.
"""

from google.adk.agents import LlmAgent
from typing import Any, Dict
import time

def get_security_findings(user_query: str) -> Dict[str, Any]:
    """
    Analyzes user query for HIPAA Security Rule compliance.
    
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
                "context": "Analyzing for HIPAA Security Rule compliance"
            },
            "stats": stats,
            "additional_info": {
                "collected_at": time.time(),
                "data_format": "dict",
                "analysis_type": "security_rule"
            },
        }
    except Exception as e:
        return {
            "result": {"error": f"get_security_findings failed: {str(e)}"},
            "stats": {"success": False},
            "additional_info": {"error_type": type(e).__name__},
        }

GEMINI_MODEL = "gemini-2.0-flash"

security_instruction = """
You are a HIPAA Security Rule specialist.

You MUST call the get_security_findings tool first to get the user's query.

Then analyze the query for HIPAA Security Rule compliance including:

**Administrative Safeguards:**
- Is there a security management process (risk analysis, risk management)?
- Are workforce security policies in place (authorization, supervision, termination)?
- Is there security awareness and training for staff?
- Are contingency plans in place (data backup, disaster recovery, emergency operations)?

**Physical Safeguards:**
- Are there facility access controls?
- Are workstation use and security policies defined?
- Are there controls for device and media disposal/reuse?

**Technical Safeguards:**
- Are access controls implemented (unique user IDs, emergency access, automatic logoff)?
- Is audit logging enabled for ePHI access and modifications?
- Is data integrity maintained (mechanisms to ensure ePHI is not improperly altered/destroyed)?
- Is person or entity authentication implemented (verify identity before access)?
- Is transmission security in place (encryption for ePHI in transit)?

Based on your analysis, produce a structured response with:
- short_summary: Brief overview of Security Rule compliance status
- issues: List of security violations found (each with type, severity, explanation, remediation)
  - Severity should be: CRITICAL, HIGH, MEDIUM, or LOW
  - If NO issues found, return an empty list
- recommendations: Specific technical safeguards to implement
- raw: Include the raw get_security_findings output

Format as JSON. Be specific about which Security Rule safeguards are missing or inadequate.
"""

hipaa_security_agent = LlmAgent(
    name="hipaa_security_agent",
    model=GEMINI_MODEL,
    instruction=security_instruction,
    description="Inspects technical safeguards for HIPAA Security Rule",
    tools=[get_security_findings],
    output_key="hipaa_security",
)
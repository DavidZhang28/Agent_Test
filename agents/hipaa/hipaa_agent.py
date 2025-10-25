"""
HIPAA regulation coordinator.

This coordinator runs three HIPAA sub-specialists in parallel:
- privacy rule agent
- security rule agent
- breach notification agent

It ensures each sub-agent is invoked and returns a combined structured
result that the top-level coordinator can synthesize.
"""

from google.adk.agents import ParallelAgent, LlmAgent, SequentialAgent

from .privacy_rule_agent import hipaa_privacy_agent
from .security_rule_agent import hipaa_security_agent
from .breach_notification_agent import hipaa_breach_agent

GEMINI_MODEL = "gemini-2.0-flash"

# Step 1: Run the specialists in parallel
hipaa_parallel = ParallelAgent(
    name="hipaa_parallel",
    sub_agents=[hipaa_privacy_agent, hipaa_security_agent, hipaa_breach_agent],
)

# Step 2: Summarize their outputs
hipaa_summary_instruction = """
You are the HIPAA Coordinator. You will receive the results from the HIPAA subagents
as privacy, security, and breach. Produce a structured dictionary with:
- short_summary: 1-2 sentence summary
- issues: list of detected issues (each with type, severity, explanation)
- raw: include the raw outputs under 'privacy', 'security', 'breach'
Return as a JSON-like structure.
"""

hipaa_summary_agent = LlmAgent(
    name="hipaa_summary",
    model=GEMINI_MODEL,
    instruction=hipaa_summary_instruction,
    description="Summarizes HIPAA subagent outputs",
)

# Step 3: Chain them together - parallel execution THEN summary
hipaa_coordinator_agent = SequentialAgent(
    name="hipaa_coordinator",
    sub_agents=[hipaa_parallel, hipaa_summary_agent],
    #output_key="hipaa_report",
)
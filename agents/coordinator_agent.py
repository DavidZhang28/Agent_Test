"""
Coordinator agent for Ghost Manager.

This top-level agent composes the HIPAA and FDA coordinator agents into a
parallel gatherer and then synthesizes a final structured compliance report.
Users should only interact with this agent.

Design:
- A ParallelAgent runs HIPAA and FDA coordinators concurrently for speed.
- A synthesizer LlmAgent merges their outputs into a single structured result.
- All sub-agents/tools return the ADK-standard custom structure:
  {"result": ..., "stats": ..., "additional_info": ...}
"""

from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

# Import sub-coordinators
from .hipaa.hipaa_agent import hipaa_coordinator_agent
from .fda.fda_agent import fda_coordinator_agent

# Simple model constant — in a real system, choose as appropriate
GEMINI_MODEL = "gemini-2.0-flash"

# Parallel gatherer: run both HIPAA and FDA coordinators at once
regulations_gatherer = ParallelAgent(
    name="regulations_gatherer",
    sub_agents=[hipaa_coordinator_agent, fda_coordinator_agent],
)

# Synthesizer: combine outputs into a human- and machine-friendly report
synthesizer_instruction = """
You are the Ghost Manager Report Synthesizer.
You will receive outputs from HIPAA and FDA coordinators as:
- hipaa_report: hipaa_report
- fda_report: fda_report

Produce a structured response in JSON-like markdown with the following keys:
- status: one of ['OK', 'WARNING', 'VIOLATION']
- hipaa: short summary and list of issues (if any)
- fda: short summary and list of issues (if any)
- recommendations: combined prioritized actions
- raw_details: include the hipaa_report and fda_report (as-is) under raw_details

Ensure output is machine-parsable and also readable.
"""

system_report_synthesizer = LlmAgent(
    name="ghost_synthesizer",
    model=GEMINI_MODEL,
    instruction=synthesizer_instruction,
    description="Synthesizes HIPAA and FDA coordinator outputs into final report",
    output_key="synthesized_report",
)

# The top-level coordinator runs gatherer then synthesizer
coordinator_agent = SequentialAgent(
    name="ghost_coordinator",
    sub_agents=[regulations_gatherer, system_report_synthesizer],
)

"""
FDA regulation coordinator.

Coordination pattern for FDA checks. Runs Part11 Records and Part11 Signatures
specialists in parallel and consolidates their outputs.
"""

from google.adk.agents import ParallelAgent, LlmAgent, SequentialAgent

from .part11_records_agent import part11_records_agent
from .part11_signatures_agent import part11_signatures_agent

GEMINI_MODEL = "gemini-2.0-flash"

# Step 1: Run the specialists in parallel
fda_parallel = ParallelAgent(
    name="fda_parallel",
    sub_agents=[part11_records_agent, part11_signatures_agent],
)

# Step 2: Summarize their outputs
fda_summary_instruction = """
You are the FDA Coordinator.
You will receive outputs from the Part11 Records and Part11 Signatures specialists.
Produce a structured object with:
- short_summary: A brief overview of FDA Part 11 compliance status
- issues: A list of any compliance issues found (each with type, severity, explanation)
- raw: Include the full records and signatures outputs

Format your response as a JSON object.
"""

fda_summary_agent = LlmAgent(
    name="fda_summary",
    model=GEMINI_MODEL,
    instruction=fda_summary_instruction,
    description="Summarizes FDA Part 11 specialist outputs",
)

# Step 3: Chain them together - parallel execution THEN summary
fda_coordinator_agent = SequentialAgent(
    name="fda_coordinator",
    sub_agents=[fda_parallel, fda_summary_agent],
    #output_key="fda_report",
)
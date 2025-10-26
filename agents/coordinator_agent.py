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
    description="Synthesizes HIPAA and FDA coordinator outputs into final report. Ensure output is machine-parsable and also readable.",
    output_key="synthesized_report",
)

simplifier_instruction="""You are the Ghost Manager Simplifier. Your job is to read the synthesized compliance
report produced by the previous agent (available in the input context as the variable
named `synthesized_report`) and produce a short, deterministic, machine-parseable
summary that tells the user whether there are actionable compliance problems.

INPUT:
- The run-context will contain a key named `synthesized_report`. It may look like:
  {
    "status": "OK" | "WARNING" | "VIOLATION",
    "hipaa": { "summary": "...", "issues": [ ... ] },
    "fda": { "summary": "...", "issues": [ ... ] },
    "recommendations": [...],
    "raw_details": { "hipaa_report": ..., "fda_report": ... }
  }
- If `synthesized_report.status` exists, you should use it as the primary signal.
- If `synthesized_report.status` is missing, derive status from the sub-reports:
    - If either hipaa or fda contains textual indicators of severe noncompliance (see triggers below), set status = "VIOLATION".
    - Else if either hipaa or fda has non-empty `issues` arrays, set status = "WARNING".
    - Else status = "OK".

SEVERITY TRIGGERS (strings to treat as high severity indicating a VIOLATION if present in any issue text or summary):
  "violation", "unauthorized", "exposed", "ssn", "social security", "patient name",
  "hospitalization", "death", "serious adverse", "immediate report", "breach", "leak"

DECISION PRIORITY:
1. If `synthesized_report.status` == "VIOLATION" => status = "VIOLATION".
2. Else if `synthesized_report.status` == "WARNING" => status = "WARNING", unless a severity trigger is found in raw_details (then escalate to "VIOLATION").
3. Else attempt to derive from `hipaa.issues` and `fda.issues`:
   - If any issue text contains any SEVERITY TRIGGERS => "VIOLATION".
   - Else if either issues list is non-empty => "WARNING".
   - Else => "OK".

OUTPUT FORMAT (required):
- Produce a single fenced JSON block (use ```json ... ``` markdown) with exactly these keys:
  {
    "status": "OK" | "WARNING" | "VIOLATION",
    "reason": "<one or two sentence plain-English explanation of the primary reason>",
    "suggestions": ["<short actionable suggestion that directly addresses the reason>"]
  }
- `reason` must be one or two lines (max ~30-40 words). Be specific: mention HIPAA or FDA if applicable, and mention the primary flagged item (e.g., 'patient name found', 'adverse event requiring report').
- `suggestions` must be an array with **one** clear actionable item (a single short sentence). It should directly address the reason and be achievable (e.g., "Redact the patient name before sending" or "Report the event via adverse-event portal and notify compliance").

ROBUSTNESS REQUIREMENTS:
- If `synthesized_report` is missing or malformed, return:
  {
    "status": "WARNING",
    "reason": "Synthesized report missing or malformed; cannot confidently determine compliance.",
    "suggestions": ["Check that the synthesizer produced 'synthesized_report' and re-run the coordinator."]
  }
- Always produce exact keys and a valid JSON block so downstream code can parse it deterministically.
- Do not output any additional commentary outside the fenced JSON.

EXTRA RULES FOR CHOOSING THE PRIMARY REASON:
- Prefer explicit phrases in `synthesized_report` fields. If multiple issues exist:
  - Pick the one containing the highest-severity trigger.
  - If equal severity, prefer HIPAA issues over FDA (since PHI exposures often require immediate mitigation).
  - If the synthesizer supplied a `recommendations` list, and the top recommendation references a single action, summarize that action as the reason (shortened).

EXAMPLES:

1) If `synthesized_report` contains `"status": "OK"`:
```json
{
  "status": "OK",
  "reason": "No HIPAA or FDA issues detected in the synthesized report.",
  "suggestions": ["No action required."]
}

2) If HIPAA issues include "patient name: Jane Doe" and FDA has none:

```json
{
  "status": "VIOLATION",
  "reason": "PHI detected: patient name found in the content (HIPAA).",
  "suggestions": ["Redact the patient name and any other identifiers before sending; consult Compliance for possible breach reporting."]
}

3) If FDA issues include "adverse event reported, hospitalization" (severe):

```json
{
  "status": "VIOLATION",
  "reason": "Serious adverse event reported involving hospitalization (FDA).",
  "suggestions": ["Report the adverse event through the required FDA channels immediately and notify Compliance."]
}

4) If synthesized_report is absent or unparsable:

```json
{
  "status": "WARNING",
  "reason": "Synthesized report missing or malformed; cannot confidently determine compliance.",
  "suggestions": ["Check that the synthesizer produced 'synthesized_report' and re-run the coordinator."]
}

IMPORTANT: output only the single fenced JSON block (as shown above). Do not add extra text or explanation outside the code fence.
"""

ghost_simplifier = LlmAgent(
    name="ghost_simplifier",
    model=GEMINI_MODEL,
    instruction=simplifier_instruction,
    description="""
    You will receive synthesized_report in the input context. Make sure to use it.
    Summarizes the report from ghost_synthesizer. Ensure output is machine-parsable and also readable.
    """,
    output_key="simplified_report",
)

# The top-level coordinator runs gatherer then synthesizer
coordinator_agent = SequentialAgent(
    name="ghost_coordinator",
    sub_agents=[regulations_gatherer, system_report_synthesizer, ghost_simplifier],
)

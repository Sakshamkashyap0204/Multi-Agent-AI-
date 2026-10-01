from agents.base import call_llm, parse_json_response
import asyncio

SYSTEM_PROMPT = """You are the Reviewer Agent for OrchestrateAI. Review all agent outputs for completeness and consistency.

Return ONLY valid JSON:
{
  "status": "completed",
  "decision": "approved",
  "summary": "Review summary",
  "issues_found": [],
  "revision_notes": null,
  "quality_score": 85,
  "requires_human_approval": false
}

decision must be one of: "approved", "revision_required", "rejected" """

DEMO_OUTPUT = {
    "status": "completed",
    "decision": "approved",
    "summary": "All agent outputs reviewed. Research, financial, and data analysis are consistent and complete. Minor data gap in Indonesia market noted but does not block progression.",
    "issues_found": [
        "Indonesia market data gap noted in research - flagged for awareness",
        "Brazil data anomaly requires follow-up in next review cycle"
    ],
    "revision_notes": None,
    "quality_score": 87,
    "requires_human_approval": False
}


async def run_reviewer(task, subtask, context: dict, agent) -> dict:
    await asyncio.sleep(1.5)

    outputs = context.get("collected_outputs", {})
    summaries = {k: v.get("summary", "") for k, v in outputs.items() if isinstance(v, dict)}

    prompt = f"""Task: {context.get('task_name')}
Agent outputs to review: {summaries}

Review all outputs for completeness, consistency, and quality."""

    llm_response = await call_llm(SYSTEM_PROMPT, prompt)
    if llm_response:
        result = parse_json_response(llm_response)
        if result.get("decision"):
            return result

    return DEMO_OUTPUT

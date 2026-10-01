from agents.base import call_llm, parse_json_response
import asyncio

SYSTEM_PROMPT = """You are the Compliance Agent for OrchestrateAI. Check outputs against governance policies.

Return ONLY valid JSON:
{
  "status": "completed",
  "compliance_status": "requires_approval",
  "summary": "Compliance summary",
  "violations": [],
  "warnings": ["warning 1"],
  "policy_triggered": "Policy name",
  "risk_level": "high",
  "requires_human_approval": true,
  "approval_reason": "Reason for approval"
}

compliance_status must be one of: "compliant", "warning", "blocked", "requires_approval" """

DEMO_OUTPUT = {
    "status": "completed",
    "compliance_status": "requires_approval",
    "summary": "Compliance review complete. Financial recommendations exceed the $1M governance threshold. External market expansion recommendations require executive authorization before proceeding.",
    "violations": [],
    "warnings": [
        "Financial recommendations exceed $1M threshold (Governance Policy: Financial Actions)",
        "External market entry recommendations require executive sign-off"
    ],
    "policy_triggered": "Financial Actions Policy",
    "risk_level": "high",
    "requires_human_approval": True,
    "approval_reason": "Financial recommendations totaling $4.8M exceed the $1M executive authorization threshold defined in governance policy. Human approval required before proceeding to final synthesis."
}


async def run_compliance(task, subtask, context: dict, agent) -> dict:
    await asyncio.sleep(1.5)

    outputs = context.get("collected_outputs", {})
    finance_output = outputs.get("finance", {})

    prompt = f"""Task: {context.get('task_name')}
Financial output: {finance_output.get('summary', '')}
Recommendations: {finance_output.get('recommendation', '')}

Check compliance with governance policies and return structured assessment."""

    llm_response = await call_llm(SYSTEM_PROMPT, prompt)
    if llm_response:
        result = parse_json_response(llm_response)
        if result.get("compliance_status"):
            return result

    return DEMO_OUTPUT


async def run_risk(task, subtask, context: dict, agent) -> dict:
    return await run_compliance(task, subtask, context, agent)

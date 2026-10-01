from agents.base import call_llm, parse_json_response
import asyncio

SYSTEM_PROMPT = """You are the Research Agent for OrchestrateAI. Gather and analyze information relevant to the task.

Return ONLY valid JSON:
{
  "status": "completed",
  "summary": "Research summary",
  "findings": [
    {"title": "Finding title", "description": "Details", "significance": "high/medium/low"}
  ],
  "key_insights": ["insight 1", "insight 2"],
  "data_gaps": ["gap 1"],
  "requires_human_approval": false
}"""

DEMO_OUTPUT = {
    "status": "completed",
    "summary": "Market research identified strong expansion opportunities in Southeast Asia and Latin America, with emerging middle-class demographics and growing digital adoption rates.",
    "findings": [
        {
            "title": "Southeast Asia Market Opportunity",
            "description": "Combined addressable market of $4.2B across Vietnam, Thailand, and Indonesia with 23% YoY growth in target segment.",
            "significance": "high"
        },
        {
            "title": "Competitive Landscape",
            "description": "Three major competitors present in target markets, with market share fragmented below 30% each. Significant whitespace identified.",
            "significance": "high"
        },
        {
            "title": "Regulatory Environment",
            "description": "Vietnam and Thailand have favorable foreign investment policies. Indonesia requires local partnership for market entry.",
            "significance": "medium"
        },
        {
            "title": "Digital Infrastructure",
            "description": "Mobile internet penetration exceeds 75% in target markets. Strong e-commerce adoption supports digital-first entry strategy.",
            "significance": "medium"
        },
        {
            "title": "Latin America Secondary Opportunity",
            "description": "Brazil and Colombia show 18% growth in target segment. Higher entry costs but stronger brand recognition potential.",
            "significance": "medium"
        }
    ],
    "key_insights": [
        "Southeast Asia offers the highest growth potential with lower entry barriers",
        "Local partnerships are strategically advantageous even where not legally required",
        "Digital-first market entry reduces initial capital requirements by approximately 40%",
        "Q1 entry timing aligns with regional fiscal year planning cycles"
    ],
    "data_gaps": [
        "Detailed consumer preference data for Indonesia not available",
        "Regulatory timeline for Vietnam market entry requires legal consultation"
    ],
    "requires_human_approval": False
}


async def run_research(task, subtask, context: dict, agent) -> dict:
    await asyncio.sleep(3)

    prompt = f"""Task: {context.get('task_name')}
Subtask: {subtask.description}
Goal: {context.get('goal', '')}

Conduct research and return structured findings."""

    llm_response = await call_llm(SYSTEM_PROMPT, prompt)
    if llm_response:
        result = parse_json_response(llm_response)
        if result.get("findings"):
            return result

    return DEMO_OUTPUT

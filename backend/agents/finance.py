from agents.base import call_llm, parse_json_response
import asyncio

SYSTEM_PROMPT = """You are the Finance Agent for OrchestrateAI. Your role is to evaluate financial implications, estimate costs, model scenarios, and produce financial summaries.

Return ONLY valid JSON:
{
  "status": "completed",
  "summary": "Financial analysis summary",
  "scenarios": [
    {
      "name": "Scenario name",
      "capital_required": "$X.XM",
      "projected_roi": "XX%",
      "payback_months": 22,
      "risk_profile": "Low/Moderate/High",
      "recommended": true
    }
  ],
  "cost_breakdown": [
    {"category": "Category name", "amount": "$XXX,XXX", "percentage": "XX%"}
  ],
  "projections": [
    {"period": "Year 1", "revenue": "$X.XM", "gross_margin": "XX%"}
  ],
  "recommendation": "Executive financial recommendation",
  "financial_risks": ["Risk 1", "Risk 2"],
  "requires_human_approval": true
}"""

DEMO_OUTPUT = {
    "status": "completed",
    "summary": "Financial analysis evaluated three expansion scenarios. Balanced Expansion recommends $4.8M phased investment with 34% projected 3-year ROI and 22-month payback period. Exceeds $1M threshold requiring human executive sign-off.",
    "scenarios": [
        {
            "name": "Conservative (Vietnam Only)",
            "capital_required": "$2.1M",
            "projected_roi": "24%",
            "payback_months": 28,
            "risk_profile": "Low",
            "recommended": False
        },
        {
            "name": "Balanced Expansion (SEA Core: Vietnam, Thailand, Indonesia)",
            "capital_required": "$4.8M",
            "projected_roi": "34%",
            "payback_months": 22,
            "risk_profile": "Moderate",
            "recommended": True
        },
        {
            "name": "Aggressive Global (SEA + Latin America)",
            "capital_required": "$8.5M",
            "projected_roi": "41%",
            "payback_months": 18,
            "risk_profile": "High",
            "recommended": False
        }
    ],
    "cost_breakdown": [
        {"category": "Market Entry & Legal Compliance", "amount": "$380,000", "percentage": "8%"},
        {"category": "Technology Infrastructure & Localization", "amount": "$620,000", "percentage": "13%"},
        {"category": "Marketing & Brand Acquisition", "amount": "$840,000", "percentage": "17.5%"},
        {"category": "Regional Operations & Talent", "amount": "$1,200,000", "percentage": "25%"},
        {"category": "Working Capital & Contingency Reserve", "amount": "$760,000", "percentage": "15.8%"}
    ],
    "projections": [
        {"period": "Year 1", "revenue": "$1.9M", "gross_margin": "48%"},
        {"period": "Year 2", "revenue": "$5.4M", "gross_margin": "56%"},
        {"period": "Year 3", "revenue": "$11.2M", "gross_margin": "62%"}
    ],
    "recommendation": "Balanced Expansion strategy requiring $4.8M capital allocation over 18 months, yielding 34% ROI with break-even at month 22.",
    "financial_risks": [
        "Foreign exchange currency fluctuations in emerging markets (±12% sensitivity)",
        "Regulatory licensing delays in Indonesia extending payback by 3-4 months",
        "Digital CAC volatility during peak Q4 ad auction cycles (±15%)"
    ],
    "requires_human_approval": True
}


async def run_finance(task, subtask, context: dict, agent) -> dict:
    await asyncio.sleep(2.5)

    previous = context.get("previous_outputs", {})
    research = previous.get("research", {})
    data = previous.get("data_analyst", {})

    prompt = f"""Task: {context.get('task_name')}
Description: {context.get('task_description', '')}
Goal: {context.get('goal', '')}
Subtask: {subtask.description}
Research context: {research.get('summary', 'Market expansion opportunity')}
Data metrics: {data.get('summary', 'Growing market CAGR')}

Perform financial modeling, cost estimation, and scenario analysis."""

    llm_response = await call_llm(SYSTEM_PROMPT, prompt)
    if llm_response:
        result = parse_json_response(llm_response)
        if result.get("scenarios") or result.get("summary"):
            return result

    return DEMO_OUTPUT


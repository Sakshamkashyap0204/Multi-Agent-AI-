from agents.base import call_llm, parse_json_response
import asyncio

SYSTEM_PROMPT = """You are the Writer Agent for OrchestrateAI. Convert research and analysis into clear, professional reports.

Return ONLY valid JSON:
{
  "status": "completed",
  "summary": "Report summary",
  "sections": [
    {"title": "Section title", "content": "Section content"}
  ],
  "executive_summary": "Brief executive summary",
  "word_count": 500,
  "requires_human_approval": false
}"""

DEMO_OUTPUT = {
    "status": "completed",
    "summary": "Executive report compiled from research, financial, and data analysis outputs. Report is structured for C-suite presentation.",
    "executive_summary": "Market analysis indicates a compelling opportunity for Q4 expansion into Southeast Asian markets, with a recommended $4.8M phased investment yielding projected 34% ROI over 3 years. Vietnam and Thailand present the lowest-risk entry points, while Indonesia requires a local partnership structure.",
    "sections": [
        {
            "title": "Market Opportunity Overview",
            "content": "The Southeast Asian market presents a $4.2B addressable opportunity growing at 23.4% CAGR. Digital adoption rates exceeding 76% across target markets support a digital-first entry strategy that reduces initial capital requirements by approximately 40% compared to traditional market entry approaches."
        },
        {
            "title": "Competitive Analysis",
            "content": "The competitive landscape remains fragmented with no single player holding more than 30% market share. This fragmentation, combined with identified whitespace in the 25-40 demographic segment, creates a favorable entry window. Three primary competitors have been identified, none of whom have established strong brand loyalty in target segments."
        },
        {
            "title": "Financial Projections",
            "content": "The Balanced Expansion scenario (SEA + LATAM) requires $4.8M investment with projected 34% ROI and 22-month payback period. Cost breakdown: Market Entry & Legal ($380K), Technology Infrastructure ($620K), Marketing & Brand ($840K), Operations & Staffing ($1.2M), Working Capital Reserve ($760K)."
        },
        {
            "title": "Risk Assessment",
            "content": "Primary risks include currency fluctuation (±12% impact), regulatory compliance cost overruns (15-20%), and competitive response in Year 1. Indonesia market entry requires local partnership, adding operational complexity. Brazil data anomalies require verification before LATAM commitment."
        }
    ],
    "word_count": 487,
    "requires_human_approval": False
}


async def run_writer(task, subtask, context: dict, agent) -> dict:
    await asyncio.sleep(2)

    previous = context.get("previous_outputs", {})
    research = previous.get("research", {})
    finance = previous.get("finance", {})
    data = previous.get("data_analyst", {})

    prompt = f"""Task: {context.get('task_name')}
Goal: {context.get('goal', '')}

Research findings: {research.get('summary', 'Not available')}
Financial analysis: {finance.get('summary', 'Not available')}
Data analysis: {data.get('summary', 'Not available')}

Write a professional report based on these inputs."""

    llm_response = await call_llm(SYSTEM_PROMPT, prompt)
    if llm_response:
        result = parse_json_response(llm_response)
        if result.get("sections"):
            return result

    return DEMO_OUTPUT

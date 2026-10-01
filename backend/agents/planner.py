from agents.base import call_llm, parse_json_response
import asyncio

SYSTEM_PROMPT = """You are the Planner Agent for OrchestrateAI. Your role is to analyze a task and create a structured execution plan.

Break the task into subtasks and assign each to the appropriate specialized agent:
- research: Research Agent - gather information, identify findings
- data_analyst: Data Analyst Agent - analyze data, identify trends
- finance: Finance Agent - financial analysis, cost estimation
- writer: Writer Agent - write reports, summaries
- synthesis: Final Synthesis Agent - combine outputs (always last)

Return ONLY valid JSON in this exact format:
{
  "status": "completed",
  "summary": "Brief plan summary",
  "subtasks": [
    {
      "name": "Subtask name",
      "description": "What this subtask does",
      "agent_slug": "agent_name",
      "depends_on": []
    }
  ],
  "execution_strategy": "parallel or sequential description"
}

Rules:
- Research, finance, and data_analyst can run in parallel (no depends_on)
- Writer depends on research
- Synthesis is always last and depends on all others
- Do NOT include planner, reviewer, or compliance in subtasks (they run automatically)
- Create 3-5 subtasks maximum"""

DEMO_PLAN = {
    "status": "completed",
    "summary": "Execution plan for market expansion analysis with parallel research, financial, and data analysis phases.",
    "subtasks": [
        {
            "name": "Market Research",
            "description": "Research market opportunities, competitive landscape, and expansion targets",
            "agent_slug": "research",
            "depends_on": []
        },
        {
            "name": "Financial Analysis",
            "description": "Evaluate financial implications, investment requirements, and ROI projections",
            "agent_slug": "finance",
            "depends_on": []
        },
        {
            "name": "Data Analysis",
            "description": "Analyze available market data, identify trends and patterns",
            "agent_slug": "data_analyst",
            "depends_on": []
        },
        {
            "name": "Report Writing",
            "description": "Compile research findings into a structured executive report",
            "agent_slug": "writer",
            "depends_on": ["Market Research", "Data Analysis"]
        }
    ],
    "execution_strategy": "Market Research, Financial Analysis, and Data Analysis run in parallel. Report Writing follows research completion."
}


async def run_planner(task, subtask, context: dict, agent) -> dict:
    await asyncio.sleep(1.5)

    prompt = f"""Task: {context.get('task_name')}
Description: {context.get('task_description', '')}
Goal: {context.get('goal', '')}

Create an execution plan with appropriate subtasks."""

    llm_response = await call_llm(SYSTEM_PROMPT, prompt)
    if llm_response:
        result = parse_json_response(llm_response)
        if result.get("subtasks"):
            return result

    return DEMO_PLAN

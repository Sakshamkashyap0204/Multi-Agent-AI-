import asyncio
import json
import os
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.db_models import (
    Task, Subtask, Agent, AgentExecution, Approval, GovernancePolicy,
    GovernanceEvent, TaskVersion, TaskStatus, ExecutionStatus, ApprovalStatus,
    PolicyAction
)
from models.database import AsyncSessionLocal
from services.audit import log_event, create_notification
from services.websocket_manager import manager
from agents.planner import run_planner
from agents.research import run_research
from agents.finance import run_finance
from agents.compliance import run_compliance
from agents.writer import run_writer
from agents.reviewer import run_reviewer
from agents.synthesis import run_synthesis
from agents.data_analyst import run_data_analyst

AGENT_RUNNERS = {
    "planner": run_planner,
    "research": run_research,
    "finance": run_finance,
    "compliance": run_compliance,
    "writer": run_writer,
    "reviewer": run_reviewer,
    "synthesis": run_synthesis,
    "data_analyst": run_data_analyst,
}


async def emit(task_id: str, event_type: str, data: dict):
    await manager.broadcast(f"task:{task_id}", {"type": event_type, **data})
    await manager.broadcast_global({"type": event_type, "task_id": task_id, **data})


async def update_task_status(db: AsyncSession, task: Task, status: TaskStatus, step: str = None, agent: str = None):
    task.status = status
    if step:
        task.current_step = step
    if agent:
        task.current_agent = agent
    task.updated_at = datetime.utcnow()
    await db.commit()
    await emit(task.id, "task_status_update", {
        "task_id": task.id,
        "status": status.value,
        "current_step": task.current_step,
        "current_agent": task.current_agent,
    })


async def check_governance(db: AsyncSession, task: Task, agent_slug: str, action: str, output: dict) -> Optional[str]:
    result = await db.execute(
        select(GovernancePolicy).where(GovernancePolicy.is_active == True)
    )
    policies = result.scalars().all()

    for policy in policies:
        triggered = False
        trigger_lower = policy.trigger.lower()

        if "external" in trigger_lower and "external" in action.lower():
            triggered = True
        elif "financial" in trigger_lower and agent_slug == "finance":
            triggered = True
        elif "sensitive" in trigger_lower and output.get("requires_human_approval"):
            triggered = True
        elif "compliance" in trigger_lower and agent_slug == "compliance":
            if output.get("status") in ["blocked", "requires_approval"]:
                triggered = True

        if triggered:
            gov_event = GovernanceEvent(
                policy_id=policy.id,
                task_id=task.id,
                agent_slug=agent_slug,
                event_type="policy_triggered",
                description=f"Policy '{policy.name}' triggered by {agent_slug} during: {action}",
                action_taken=policy.action.value,
            )
            db.add(gov_event)
            await db.commit()

            await log_event(
                db, "governance_triggered", f"Policy '{policy.name}' triggered",
                task_id=task.id, agent_slug=agent_slug,
                risk_level=policy.severity.value,
                details={"policy": policy.name, "action": policy.action.value}
            )

            await emit(task.id, "governance_event", {
                "policy": policy.name,
                "agent": agent_slug,
                "action": policy.action.value,
                "severity": policy.severity.value,
            })

            if policy.action == PolicyAction.block:
                return "blocked"
            elif policy.action == PolicyAction.require_approval:
                return "requires_approval"
            elif policy.action == PolicyAction.warn:
                return "warn"

    return None


async def create_approval_request(
    db: AsyncSession, task: Task, agent_slug: str,
    requested_action: str, reason: str, risk_level: str,
    agent_output: dict, policy_triggered: str = None
) -> Approval:
    approval = Approval(
        task_id=task.id,
        agent_slug=agent_slug,
        requested_action=requested_action,
        reason=reason,
        risk_level=risk_level,
        agent_output=agent_output,
        policy_triggered=policy_triggered,
        status=ApprovalStatus.pending,
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)

    await log_event(
        db, "approval_requested", f"Approval required for {agent_slug}",
        task_id=task.id, agent_slug=agent_slug,
        risk_level=risk_level,
        details={"approval_id": approval.id, "action": requested_action}
    )

    await emit(task.id, "approval_required", {
        "approval_id": approval.id,
        "agent": agent_slug,
        "action": requested_action,
        "risk_level": risk_level,
    })

    result = await db.execute(select(Task).where(Task.id == task.id))
    task_obj = result.scalar_one()
    owner_id = task_obj.owner_id
    if owner_id:
        await create_notification(
            db, owner_id,
            "Approval Required",
            f"Task '{task_obj.name}' requires your approval: {requested_action}",
            type="warning",
            link=f"/approvals/{approval.id}"
        )

    return approval


async def run_agent_step(
    db: AsyncSession, task: Task, subtask: Subtask, agent: Agent,
    context: dict
) -> dict:
    execution = AgentExecution(
        task_id=task.id,
        agent_id=agent.id,
        subtask_id=subtask.id,
        status=ExecutionStatus.running,
        input_data=context,
        started_at=datetime.utcnow(),
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    subtask.status = ExecutionStatus.running
    await db.commit()

    await update_task_status(db, task, TaskStatus.running, subtask.name, agent.slug)
    await log_event(
        db, "agent_started", f"{agent.name} started",
        task_id=task.id, agent_slug=agent.slug, risk_level="low",
        details={"subtask": subtask.name}
    )
    await emit(task.id, "agent_started", {"agent": agent.slug, "agent_name": agent.name, "subtask": subtask.name})

    runner = AGENT_RUNNERS.get(agent.slug)
    if not runner:
        output = {"status": "completed", "summary": f"{agent.name} completed task.", "findings": []}
    else:
        try:
            output = await runner(task, subtask, context, agent)
        except Exception as e:
            output = {"status": "failed", "error": str(e), "summary": f"{agent.name} encountered an error."}

    now = datetime.utcnow()
    duration = (now - execution.started_at).total_seconds()

    if output.get("status") == "failed":
        execution.status = ExecutionStatus.failed
        execution.error = output.get("error", "Unknown error")
        subtask.status = ExecutionStatus.failed
        agent.tasks_failed = (agent.tasks_failed or 0) + 1
    else:
        execution.status = ExecutionStatus.completed
        subtask.status = ExecutionStatus.completed
        subtask.output = output
        agent.tasks_completed = (agent.tasks_completed or 0) + 1
        agent.total_execution_time = (agent.total_execution_time or 0) + duration

    execution.output_data = output
    execution.completed_at = now
    await db.commit()

    await log_event(
        db, "agent_completed", f"{agent.name} completed",
        task_id=task.id, agent_slug=agent.slug, risk_level="low",
        details={"subtask": subtask.name, "duration": duration, "status": output.get("status")}
    )
    await emit(task.id, "agent_completed", {
        "agent": agent.slug,
        "agent_name": agent.name,
        "subtask": subtask.name,
        "output": output,
        "duration": duration,
    })

    return output


async def get_agent_by_slug(db: AsyncSession, slug: str) -> Optional[Agent]:
    result = await db.execute(select(Agent).where(Agent.slug == slug))
    return result.scalar_one_or_none()


async def wait_for_approval(db: AsyncSession, task_id: str, approval_id: str, timeout: int = 3600) -> str:
    start = datetime.utcnow()
    while True:
        await asyncio.sleep(1)
        elapsed = (datetime.utcnow() - start).total_seconds()
        if elapsed > timeout:
            return "timeout"

        async with AsyncSessionLocal() as check_db:
            result = await check_db.execute(
                select(Approval).where(Approval.id == approval_id)
            )
            approval = result.scalar_one_or_none()
            if approval and approval.status != ApprovalStatus.pending:
                return approval.status.value

            task_result = await check_db.execute(select(Task).where(Task.id == task_id))
            task = task_result.scalar_one_or_none()
            if task and task.status == TaskStatus.cancelled:
                return "cancelled"


async def orchestrate_task(task_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return

        try:
            await _run_orchestration(db, task)
        except Exception as e:
            await update_task_status(db, task, TaskStatus.failed)
            await log_event(
                db, "task_failed", f"Orchestration error: {str(e)}",
                task_id=task.id, risk_level="high",
                details={"error": str(e)}
            )
            await emit(task.id, "task_failed", {"error": str(e)})


async def _run_orchestration(db: AsyncSession, task: Task):
    await update_task_status(db, task, TaskStatus.planning, "Planning")
    await log_event(db, "task_started", "Task orchestration started", task_id=task.id, risk_level="low")

    planner_agent = await get_agent_by_slug(db, "planner")
    if not planner_agent:
        raise Exception("Planner agent not found")

    planner_subtask = Subtask(
        task_id=task.id,
        name="Create Execution Plan",
        description="Analyze task and create execution plan",
        agent_slug="planner",
        order=0,
    )
    db.add(planner_subtask)
    await db.commit()
    await db.refresh(planner_subtask)

    plan_output = await run_agent_step(db, task, planner_subtask, planner_agent, {
        "task_name": task.name,
        "task_description": task.description,
        "goal": task.goal,
    })

    if plan_output.get("status") == "failed":
        await update_task_status(db, task, TaskStatus.failed)
        return

    subtasks_plan = plan_output.get("subtasks", [])
    task.execution_plan = plan_output
    await db.commit()

    await emit(task.id, "plan_created", {
        "subtasks": subtasks_plan,
        "message": f"Planner created {len(subtasks_plan)} subtasks",
    })

    created_subtasks = []
    for i, st in enumerate(subtasks_plan):
        subtask = Subtask(
            task_id=task.id,
            name=st["name"],
            description=st.get("description", ""),
            agent_slug=st.get("agent_slug"),
            order=i + 1,
            depends_on=st.get("depends_on", []),
        )
        db.add(subtask)
        created_subtasks.append(subtask)

    await db.commit()
    for st in created_subtasks:
        await db.refresh(st)

    await update_task_status(db, task, TaskStatus.running, "Executing Agents")

    parallel_groups = _group_by_dependencies(subtasks_plan)
    collected_outputs = {}

    for group in parallel_groups:
        group_tasks = []
        for st_plan in group:
            matching = next((s for s in created_subtasks if s.name == st_plan["name"]), None)
            if matching:
                group_tasks.append((matching, st_plan))

        for st, st_plan in group_tasks:
            output = await _execute_subtask(db, task, st, st_plan, collected_outputs)
            collected_outputs[st.agent_slug] = output

            result = await db.execute(select(Task).where(Task.id == task.id))
            current_task = result.scalar_one()
            if current_task.status in [TaskStatus.cancelled, TaskStatus.failed]:
                return

    await db.refresh(task)
    if task.status in [TaskStatus.cancelled, TaskStatus.failed]:
        return

    reviewer_agent = await get_agent_by_slug(db, "reviewer")
    if reviewer_agent:
        reviewer_subtask = Subtask(
            task_id=task.id,
            name="Review All Outputs",
            description="Review and validate all agent outputs",
            agent_slug="reviewer",
            order=len(created_subtasks) + 1,
        )
        db.add(reviewer_subtask)
        await db.commit()
        await db.refresh(reviewer_subtask)

        review_output = await run_agent_step(db, task, reviewer_subtask, reviewer_agent, {
            "task_name": task.name,
            "collected_outputs": collected_outputs,
        })
        collected_outputs["reviewer"] = review_output

        if review_output.get("decision") == "revision_required":
            await update_task_status(db, task, TaskStatus.revision_required)
            await emit(task.id, "revision_required", {"reason": review_output.get("revision_notes")})

    compliance_agent = await get_agent_by_slug(db, "compliance")
    if compliance_agent:
        compliance_subtask = Subtask(
            task_id=task.id,
            name="Compliance Check",
            description="Check outputs against governance policies",
            agent_slug="compliance",
            order=len(created_subtasks) + 2,
        )
        db.add(compliance_subtask)
        await db.commit()
        await db.refresh(compliance_subtask)

        compliance_output = await run_agent_step(db, task, compliance_subtask, compliance_agent, {
            "task_name": task.name,
            "collected_outputs": collected_outputs,
        })
        collected_outputs["compliance"] = compliance_output

        gov_result = await check_governance(
            db, task, "compliance",
            "Compliance review of task outputs",
            compliance_output
        )

        if gov_result == "requires_approval" or compliance_output.get("requires_human_approval"):
            await update_task_status(db, task, TaskStatus.waiting_for_approval, "Awaiting Human Approval")

            approval = await create_approval_request(
                db, task, "compliance",
                "Proceed with final synthesis and report generation",
                compliance_output.get("approval_reason", "Compliance review requires human authorization before proceeding."),
                compliance_output.get("risk_level", "high"),
                compliance_output,
                policy_triggered=compliance_output.get("policy_triggered", "External Communication Policy")
            )

            decision = await wait_for_approval(db, task.id, approval.id)

            await db.refresh(task)
            if task.status == TaskStatus.cancelled:
                return

            if decision == "approved":
                await log_event(
                    db, "approval_granted", "Human approved compliance checkpoint",
                    task_id=task.id, risk_level="medium",
                    details={"approval_id": approval.id}
                )
                await emit(task.id, "approval_granted", {"approval_id": approval.id})
                await update_task_status(db, task, TaskStatus.running, "Resuming after approval")
            elif decision in ["rejected", "timeout"]:
                await update_task_status(db, task, TaskStatus.failed)
                await log_event(
                    db, "task_failed", f"Task rejected at compliance checkpoint ({decision})",
                    task_id=task.id, risk_level="high"
                )
                return
            elif decision == "changes_requested":
                await update_task_status(db, task, TaskStatus.revision_required)
                return

    synthesis_agent = await get_agent_by_slug(db, "synthesis")
    if synthesis_agent:
        synthesis_subtask = Subtask(
            task_id=task.id,
            name="Final Synthesis",
            description="Combine all outputs into final deliverable",
            agent_slug="synthesis",
            order=len(created_subtasks) + 3,
        )
        db.add(synthesis_subtask)
        await db.commit()
        await db.refresh(synthesis_subtask)

        final_output = await run_agent_step(db, task, synthesis_subtask, synthesis_agent, {
            "task_name": task.name,
            "task_description": task.description,
            "goal": task.goal,
            "collected_outputs": collected_outputs,
        })
        collected_outputs["synthesis"] = final_output

        task.final_output = final_output
        task.completed_at = datetime.utcnow()

    version = TaskVersion(
        task_id=task.id,
        version=task.version,
        final_output=task.final_output,
    )
    db.add(version)

    await update_task_status(db, task, TaskStatus.completed, "Completed")
    await log_event(
        db, "task_completed", "Task completed successfully",
        task_id=task.id, risk_level="low",
        details={"version": task.version}
    )
    await emit(task.id, "task_completed", {
        "task_id": task.id,
        "final_output": task.final_output,
    })

    result = await db.execute(select(Task).where(Task.id == task.id))
    t = result.scalar_one()
    if t.owner_id:
        await create_notification(
            db, t.owner_id,
            "Task Completed",
            f"'{t.name}' has been completed successfully.",
            type="success",
            link=f"/tasks/{t.id}"
        )


async def _execute_subtask(db: AsyncSession, task: Task, subtask: Subtask, st_plan: dict, collected_outputs: dict) -> dict:
    agent_slug = st_plan.get("agent_slug")
    if not agent_slug:
        return {"status": "skipped"}

    agent = await get_agent_by_slug(db, agent_slug)
    if not agent or agent.status.value != "active":
        subtask.status = ExecutionStatus.skipped
        await db.commit()
        return {"status": "skipped", "reason": f"Agent {agent_slug} not available"}

    context = {
        "task_name": task.name,
        "task_description": task.description,
        "goal": task.goal,
        "subtask_description": subtask.description,
        "previous_outputs": collected_outputs,
    }

    output = await run_agent_step(db, task, subtask, agent, context)
    return output


def _group_by_dependencies(subtasks_plan: list) -> list:
    groups = []
    independent = [s for s in subtasks_plan if not s.get("depends_on")]
    dependent = [s for s in subtasks_plan if s.get("depends_on")]

    if independent:
        groups.append(independent)

    while dependent:
        ready = []
        completed_names = {s["name"] for group in groups for s in group}
        still_waiting = []
        for s in dependent:
            if all(dep in completed_names for dep in s.get("depends_on", [])):
                ready.append(s)
            else:
                still_waiting.append(s)
        if ready:
            groups.append(ready)
            dependent = still_waiting
        else:
            groups.append(dependent)
            break

    return groups

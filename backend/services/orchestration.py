import asyncio
import json
import os
from datetime import datetime
from typing import Optional
from models.database import gen_id, db as default_db, MongoModel
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


async def get_agent_by_slug(db, slug: str) -> Optional[MongoModel]:
    agent_doc = await db.agents.find_one({"slug": slug})
    return MongoModel(agent_doc) if agent_doc else None


async def update_task_status(db, task_id: str, status: str, step: str = None, agent: str = None):
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow(),
    }
    if step is not None:
        update_data["current_step"] = step
    if agent is not None:
        update_data["current_agent"] = agent

    await db.tasks.update_one({"_id": task_id}, {"$set": update_data})
    await emit(task_id, "task_status_update", {
        "task_id": task_id,
        "status": status,
        "current_step": step,
        "current_agent": agent,
    })


async def check_governance(db, task: dict, agent_slug: str, action: str, output: dict) -> Optional[str]:
    policies = await db.governance_policies.find({"is_active": True}).to_list(100)

    for policy in policies:
        triggered = False
        trigger_lower = policy.get("trigger", "").lower()

        if "external" in trigger_lower and "external" in action.lower():
            triggered = True
        elif "financial" in trigger_lower and agent_slug == "finance":
            triggered = True
        elif "sensitive" in trigger_lower and output.get("requires_human_approval"):
            triggered = True
        elif "compliance" in trigger_lower and agent_slug == "compliance":
            if output.get("compliance_status") in ["blocked", "requires_approval"] or output.get("status") in ["blocked", "requires_approval"]:
                triggered = True

        if triggered:
            gov_event = {
                "_id": gen_id(),
                "policy_id": policy["_id"],
                "policy_name": policy["name"],
                "task_id": task["_id"],
                "agent_slug": agent_slug,
                "event_type": "policy_triggered",
                "description": f"Policy '{policy['name']}' triggered by {agent_slug} during: {action}",
                "action_taken": policy.get("action", "require_approval"),
                "resolved": False,
                "created_at": datetime.utcnow(),
            }
            await db.governance_events.insert_one(gov_event)

            await log_event(
                db, "governance_triggered", f"Policy '{policy['name']}' triggered",
                task_id=task["_id"], agent_slug=agent_slug,
                risk_level=policy.get("severity", "medium"),
                details={"policy": policy["name"], "action": policy.get("action")}
            )

            await emit(task["_id"], "governance_event", {
                "policy": policy["name"],
                "agent": agent_slug,
                "action": policy.get("action"),
                "severity": policy.get("severity"),
            })

            policy_action = policy.get("action")
            if policy_action == "block":
                return "blocked"
            elif policy_action == "require_approval":
                return "requires_approval"
            elif policy_action == "warn":
                return "warn"

    return None


async def create_approval_request(
    db, task: dict, agent_slug: str,
    requested_action: str, reason: str, risk_level: str,
    agent_output: dict, policy_triggered: str = None
) -> dict:
    approval = {
        "_id": gen_id(),
        "task_id": task["_id"],
        "task_name": task.get("name", "Autonomous Task"),
        "agent_slug": agent_slug,
        "requested_action": requested_action,
        "reason": reason,
        "risk_level": risk_level,
        "agent_output": agent_output,
        "policy_triggered": policy_triggered,
        "status": "pending",
        "reviewer_id": None,
        "reviewer_name": None,
        "reviewer_notes": None,
        "created_at": datetime.utcnow(),
        "resolved_at": None,
    }
    await db.approvals.insert_one(approval)

    await log_event(
        db, "approval_requested", f"Approval required for {agent_slug}",
        task_id=task["_id"], agent_slug=agent_slug,
        risk_level=risk_level,
        details={"approval_id": approval["_id"], "action": requested_action}
    )

    await emit(task["_id"], "approval_required", {
        "approval_id": approval["_id"],
        "agent": agent_slug,
        "action": requested_action,
        "risk_level": risk_level,
    })

    owner_id = task.get("owner_id")
    if owner_id:
        await create_notification(
            db, owner_id,
            "Approval Required",
            f"Task '{task.get('name')}' requires your approval: {requested_action}",
            type="warning",
            link=f"/approvals/{approval['_id']}"
        )

    return approval


async def run_agent_step(
    db, task: dict, subtask: dict, agent: MongoModel,
    context: dict
) -> dict:
    execution = {
        "_id": gen_id(),
        "task_id": task["_id"],
        "task_name": task.get("name"),
        "agent_id": agent.id,
        "agent_slug": agent.slug,
        "subtask_id": subtask.get("id"),
        "subtask_name": subtask.get("name"),
        "status": "running",
        "input_data": context,
        "started_at": datetime.utcnow(),
    }
    await db.agent_executions.insert_one(execution)

    # Update subtask status inside task document
    await db.tasks.update_one(
        {"_id": task["_id"], "subtasks.id": subtask.get("id")},
        {"$set": {"subtasks.$.status": "running"}}
    )

    await update_task_status(db, task["_id"], "RUNNING", subtask.get("name"), agent.slug)
    await log_event(
        db, "agent_started", f"{agent.name} started",
        task_id=task["_id"], agent_slug=agent.slug, risk_level="low",
        details={"subtask": subtask.get("name")}
    )
    await emit(task["_id"], "agent_started", {
        "agent": agent.slug,
        "agent_name": agent.name,
        "subtask": subtask.get("name")
    })

    runner = AGENT_RUNNERS.get(agent.slug)
    if not runner:
        output = {"status": "completed", "summary": f"{agent.name} completed task.", "findings": []}
    else:
        try:
            output = await runner(task, subtask, context, agent)
        except Exception as e:
            output = {"status": "failed", "error": str(e), "summary": f"{agent.name} encountered an error."}

    now = datetime.utcnow()
    duration = (now - execution["started_at"]).total_seconds()
    status_str = "failed" if output.get("status") == "failed" else "completed"

    await db.agent_executions.update_one(
        {"_id": execution["_id"]},
        {"$set": {
            "status": status_str,
            "output_data": output,
            "error": output.get("error"),
            "completed_at": now,
            "duration": duration,
        }}
    )

    # Update subtask inside task
    await db.tasks.update_one(
        {"_id": task["_id"], "subtasks.id": subtask.get("id")},
        {"$set": {
            "subtasks.$.status": status_str,
            "subtasks.$.output": output,
        }}
    )

    # Update agent stats
    inc_field = {"tasks_failed": 1} if status_str == "failed" else {
        "tasks_completed": 1,
        "total_execution_time": duration
    }
    await db.agents.update_one({"_id": agent.id}, {"$inc": inc_field})

    await log_event(
        db, "agent_completed", f"{agent.name} completed",
        task_id=task["_id"], agent_slug=agent.slug, risk_level="low",
        details={"subtask": subtask.get("name"), "duration": duration, "status": output.get("status")}
    )
    await emit(task["_id"], "agent_completed", {
        "agent": agent.slug,
        "agent_name": agent.name,
        "subtask": subtask.get("name"),
        "output": output,
        "duration": duration,
    })

    return output


async def wait_for_approval(db, task_id: str, approval_id: str, timeout: int = 3600) -> str:
    start = datetime.utcnow()
    while True:
        await asyncio.sleep(1)
        elapsed = (datetime.utcnow() - start).total_seconds()
        if elapsed > timeout:
            return "timeout"

        approval = await db.approvals.find_one({"_id": approval_id})
        if approval and approval.get("status") != "pending":
            return approval.get("status")

        task = await db.tasks.find_one({"_id": task_id})
        if task and task.get("status") == "CANCELLED":
            return "cancelled"


async def orchestrate_task(task_id: str):
    db = default_db
    task = await db.tasks.find_one({"_id": task_id})
    if not task:
        return

    try:
        await _run_orchestration(db, task)
    except Exception as e:
        await update_task_status(db, task_id, "FAILED")
        await log_event(
            db, "task_failed", f"Orchestration error: {str(e)}",
            task_id=task_id, risk_level="high",
            details={"error": str(e)}
        )
        await emit(task_id, "task_failed", {"error": str(e)})


async def _run_orchestration(db, task: dict):
    task_id = task["_id"]
    await update_task_status(db, task_id, "PLANNING", "Planning")
    await log_event(db, "task_started", "Task orchestration started", task_id=task_id, risk_level="low")

    planner_agent = await get_agent_by_slug(db, "planner")
    if not planner_agent:
        raise Exception("Planner agent not found")

    planner_subtask = {
        "id": gen_id(),
        "name": "Create Execution Plan",
        "description": "Analyze task and create execution plan",
        "agent_slug": "planner",
        "order": 0,
        "status": "pending",
        "depends_on": [],
    }
    await db.tasks.update_one({"_id": task_id}, {"$push": {"subtasks": planner_subtask}})

    plan_output = await run_agent_step(db, task, planner_subtask, planner_agent, {
        "task_name": task.get("name"),
        "task_description": task.get("description", ""),
        "goal": task.get("goal", ""),
    })

    if plan_output.get("status") == "failed":
        await update_task_status(db, task_id, "FAILED")
        return

    subtasks_plan = plan_output.get("subtasks", [])
    created_subtasks = [planner_subtask]

    for i, st in enumerate(subtasks_plan):
        st_doc = {
            "id": gen_id(),
            "name": st["name"],
            "description": st.get("description", ""),
            "agent_slug": st.get("agent_slug"),
            "order": i + 1,
            "depends_on": st.get("depends_on", []),
            "status": "pending",
        }
        created_subtasks.append(st_doc)

    await db.tasks.update_one(
        {"_id": task_id},
        {"$set": {
            "execution_plan": plan_output,
            "subtasks": created_subtasks,
            "started_at": datetime.utcnow(),
        }}
    )

    await emit(task_id, "plan_created", {
        "subtasks": subtasks_plan,
        "message": f"Planner created {len(subtasks_plan)} subtasks",
    })

    await update_task_status(db, task_id, "RUNNING", "Executing Agents")

    collected_outputs = {}
    for st_plan in subtasks_plan:
        matching = next((s for s in created_subtasks if s["name"] == st_plan["name"]), None)
        if not matching:
            continue

        agent_slug = st_plan.get("agent_slug")
        agent = await get_agent_by_slug(db, agent_slug)
        if not agent or agent.status != "active":
            await db.tasks.update_one(
                {"_id": task_id, "subtasks.id": matching["id"]},
                {"$set": {"subtasks.$.status": "skipped"}}
            )
            continue

        context = {
            "task_name": task.get("name"),
            "task_description": task.get("description", ""),
            "goal": task.get("goal", ""),
            "subtask_description": matching.get("description", ""),
            "previous_outputs": collected_outputs,
        }

        output = await run_agent_step(db, task, matching, agent, context)
        collected_outputs[agent_slug] = output

        current_task = await db.tasks.find_one({"_id": task_id})
        if current_task and current_task.get("status") in ["CANCELLED", "FAILED"]:
            return

    # Reviewer Agent Pass
    reviewer_agent = await get_agent_by_slug(db, "reviewer")
    if reviewer_agent:
        reviewer_subtask = {
            "id": gen_id(),
            "name": "Review All Outputs",
            "description": "Review and validate all agent outputs",
            "agent_slug": "reviewer",
            "order": len(created_subtasks) + 1,
            "status": "pending",
            "depends_on": [],
        }
        await db.tasks.update_one({"_id": task_id}, {"$push": {"subtasks": reviewer_subtask}})

        review_output = await run_agent_step(db, task, reviewer_subtask, reviewer_agent, {
            "task_name": task.get("name"),
            "collected_outputs": collected_outputs,
        })
        collected_outputs["reviewer"] = review_output

    # Compliance Agent Pass
    compliance_agent = await get_agent_by_slug(db, "compliance")
    if compliance_agent:
        compliance_subtask = {
            "id": gen_id(),
            "name": "Compliance Check",
            "description": "Check outputs against governance policies",
            "agent_slug": "compliance",
            "order": len(created_subtasks) + 2,
            "status": "pending",
            "depends_on": [],
        }
        await db.tasks.update_one({"_id": task_id}, {"$push": {"subtasks": compliance_subtask}})

        compliance_output = await run_agent_step(db, task, compliance_subtask, compliance_agent, {
            "task_name": task.get("name"),
            "collected_outputs": collected_outputs,
        })
        collected_outputs["compliance"] = compliance_output

        gov_result = await check_governance(
            db, task, "compliance",
            "Compliance review of task outputs",
            compliance_output
        )

        if gov_result == "requires_approval" or compliance_output.get("requires_human_approval"):
            await update_task_status(db, task_id, "WAITING_FOR_APPROVAL", "Awaiting Human Approval")

            approval = await create_approval_request(
                db, task, "compliance",
                "Proceed with final synthesis and report generation",
                compliance_output.get("approval_reason", "Compliance review requires human authorization before proceeding."),
                compliance_output.get("risk_level", "high"),
                compliance_output,
                policy_triggered=compliance_output.get("policy_triggered", "Financial Actions Policy")
            )

            decision = await wait_for_approval(db, task_id, approval["_id"])

            curr = await db.tasks.find_one({"_id": task_id})
            if curr and curr.get("status") == "CANCELLED":
                return

            if decision == "approved":
                await log_event(
                    db, "approval_granted", "Human approved compliance checkpoint",
                    task_id=task_id, risk_level="medium",
                    details={"approval_id": approval["_id"]}
                )
                await emit(task_id, "approval_granted", {"approval_id": approval["_id"]})
                await update_task_status(db, task_id, "RUNNING", "Resuming after approval")
            elif decision in ["rejected", "timeout"]:
                await update_task_status(db, task_id, "FAILED")
                await log_event(
                    db, "task_failed", f"Task rejected at compliance checkpoint ({decision})",
                    task_id=task_id, risk_level="high"
                )
                return
            elif decision == "changes_requested":
                await update_task_status(db, task_id, "REVISION_REQUIRED")
                return

    # Final Synthesis Agent Pass
    synthesis_agent = await get_agent_by_slug(db, "synthesis")
    if synthesis_agent:
        synthesis_subtask = {
            "id": gen_id(),
            "name": "Final Synthesis",
            "description": "Combine all outputs into final deliverable",
            "agent_slug": "synthesis",
            "order": len(created_subtasks) + 3,
            "status": "pending",
            "depends_on": [],
        }
        await db.tasks.update_one({"_id": task_id}, {"$push": {"subtasks": synthesis_subtask}})

        final_output = await run_agent_step(db, task, synthesis_subtask, synthesis_agent, {
            "task_name": task.get("name"),
            "task_description": task.get("description", ""),
            "goal": task.get("goal", ""),
            "collected_outputs": collected_outputs,
        })
        collected_outputs["synthesis"] = final_output

        # Save Final Deliverable
        now = datetime.utcnow()
        await db.tasks.update_one(
            {"_id": task_id},
            {"$set": {
                "final_output": final_output,
                "completed_at": now,
            }}
        )

        version_doc = {
            "_id": gen_id(),
            "task_id": task_id,
            "version": task.get("version", 1),
            "final_output": final_output,
            "created_at": now,
        }
        await db.task_versions.insert_one(version_doc)

    await update_task_status(db, task_id, "COMPLETED", "Completed")
    await log_event(
        db, "task_completed", "Task completed successfully",
        task_id=task_id, risk_level="low",
        details={"version": task.get("version", 1)}
    )
    await emit(task_id, "task_completed", {
        "task_id": task_id,
        "final_output": collected_outputs.get("synthesis"),
    })

    owner_id = task.get("owner_id")
    if owner_id:
        await create_notification(
            db, owner_id,
            "Task Completed",
            f"'{task.get('name')}' has been completed successfully.",
            type="success",
            link=f"/tasks/{task_id}"
        )
